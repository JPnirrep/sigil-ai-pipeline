"""
KLEIA-UP Book — Pipeline Orchestrator
Runs the full DOCX → EPUB + PDF workflow
"""

import os, sys, json, time
from pathlib import Path
from .parser import parse_docx
from .builder import build_epub
from .theme import generate_theme


def _get_build_pdf():
    """Lazy import to avoid WeasyPrint/GTK dependency at import time"""
    try:
        from .pdf_builder import build_pdf
        return build_pdf
    except Exception:
        return None


def run_pipeline(docx_path: str, output_dir: str = None,
                 genre: str = None, format: list = None) -> dict:
    """
    Run full pipeline: DOCX → EPUB + PDF

    Args:
        docx_path: Path to KDP template DOCX
        output_dir: Output directory (default: same as input)
        genre: Override genre detection
        format: ['epub'], ['pdf'], or ['epub', 'pdf']

    Returns:
        dict with results, paths, timing
    """
    start = time.time()
    t0 = time.time()

    if not format:
        format = ["epub", "pdf"]
    if not output_dir:
        output_dir = str(Path(docx_path).parent)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    base_name = Path(docx_path).stem

    # Phase 1: Parse DOCX
    book = parse_docx(docx_path)
    t1 = time.time()
    parsing_time = t1 - t0

    # Phase 2: Generate theme (try LLM first, fallback to preset)
    from . import ai_llm
    # Try to wire completion if available
    try:
        import sys as _sys
        for _f in _sys._current_frames().values():
            if 'completion' in _f.f_locals:
                ai_llm._completion_func = _f.f_locals['completion']
                break
    except Exception:
        pass

    # Theme: try LLM, fallback to preset
    theme_result = None
    ai_theme_title = book.title or "Untitled"
    ai_excerpt = " ".join(
        t for _, _, t in (book.chapters[0].elements if book.chapters else [])[:5]
    ) if book.chapters else ""

    llm_theme = ai_llm.generate_theme_llm(
        ai_theme_title, book.author or "",
        genre or theme_result.get("genre", "general") if theme_result else (genre or "general"),
        len(book.chapters), ai_excerpt
    ) if ai_llm._completion_func else None

    if llm_theme:
        # Convert LLM output to theme format
        from .theme import generate_theme as _fallback_theme, _preset_to_css_epub, _preset_to_css_print
        _tmp = generate_theme(book, genre)
        # Build preset dict from LLM output
        _preset = {
            "name": llm_theme.get("theme_name", "LLM Theme"),
            "epub": llm_theme.get("epub", {}),
            "print": llm_theme.get("print", {}),
            "colors": llm_theme.get("colors", {}),
            "style": llm_theme.get("style", {}),
        }
        theme_result = {
            "genre": llm_theme.get("genre", genre or "general"),
            "theme_name": _preset["name"],
            "css_epub": _preset_to_css_epub(_preset, book),
            "css_print": _preset_to_css_print(_preset, book),
            "preset": _preset,
            "llm_generated": True,
        }

    if not theme_result:
        theme_result = generate_theme(book, genre=genre)
        theme_result["llm_generated"] = False

    t2 = time.time()
    theme_time = t2 - t1

    # ── AI enhancements ──
    # Content cleaner (on first chapter excerpt)
    if ai_llm._completion_func and book.chapters:
        try:
            ch0 = book.chapters[0]
            _original = ch0.elements[0][2] if ch0.elements else ""
            _cleaned = ai_llm.clean_typography(_original[:500])
            if _cleaned and len(_cleaned) > 20 and _cleaned != _original:
                book._cleaning_applied = "✓"
        except Exception:
            pass

    # Accessibility metadata
    if ai_llm._completion_func:
        try:
            _a11y = ai_llm.generate_accessibility(
                book.title or "", genre or "general", len(book.chapters)
            )
            if _a11y:
                book._accessibility = _a11y.get("accessibility", {})
        except Exception:
            pass

    results = {
        "book": {
            "title": book.title,
            "author": book.author,
            "chapters": len(book.chapters),
            "template_detected": book.metadata.detected,
            "trim": f"{book.metadata.trim_width}×{book.metadata.trim_height}in",
            "styles_detected": book.raw_styles_detected,
            "genre_detected": theme_result["genre"],
            "theme": theme_result["theme_name"],
        },
        "paths": {},
        "timing": {
            "parsing": round(parsing_time, 2),
            "theme": round(theme_time, 2),
        },
        "errors": [],
    }

    # Phase 3: Export
    for fmt in format:
        try:
            fmt_start = time.time()
            if fmt == "epub":
                path = build_epub(book, f"{output_dir}/{base_name}", theme_result["css_epub"])
            elif fmt == "pdf":
                builder = _get_build_pdf()
                if not builder:
                    results["errors"].append("pdf: WeasyPrint not available (install GTK3)")
                    continue
                path = builder(book, f"{output_dir}/{base_name}", theme_result["css_print"])
            else:
                continue
            results["paths"][fmt] = path
            results["timing"][f"export_{fmt}"] = round(time.time() - fmt_start, 2)
        except Exception as e:
            results["errors"].append(f"{fmt}: {e}")

    results["timing"]["total"] = round(time.time() - start, 2)
    return results


def cli():
    """Command-line entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="KLEIA-UP Book Pipeline")
    parser.add_argument("input", help="KDP DOCX template path")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-g", "--genre", help="Genre override",
                        choices=["fiction", "scifi", "fantasy", "nonfiction"])
    parser.add_argument("-f", "--format", nargs="+", default=["epub", "pdf"],
                        choices=["epub", "pdf"], help="Output formats")
    parser.add_argument("--json", action="store_true", help="Output JSON report")

    args = parser.parse_args()
    results = run_pipeline(args.input, args.output, args.genre, args.format)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"\n{'='*50}")
        print(f"  KLEIA-UP Book — Pipeline Results")
        print(f"{'='*50}")
        print(f"  Titre:     {results['book']['title'] or 'Auto-détecté'}")
        print(f"  Auteur:    {results['book']['author'] or 'Auto-détecté'}")
        print(f"  Chapitres: {results['book']['chapters']}")
        print(f"  Template:  {results['book']['trim']} {'✓' if results['book']['template_detected'] else '✗'}")
        print(f"  Genre:     {results['book']['genre_detected']}")
        print(f"  Thème:     {results['book']['theme']}")
        print(f"  Styles:    {results['book']['styles_detected']}")
        print(f"\n  ── Exports ──")
        for fmt, path in results['paths'].items():
            size = os.path.getsize(path)
            print(f"  ✓ {fmt.upper()}: {path} ({size/1024:.0f} KB)")
        print(f"\n  ── Timing ──")
        for phase, sec in results['timing'].items():
            print(f"  ⏱  {phase}: {sec}s")
        print(f"\n  {'⚠ ' + str(len(results['errors'])) + ' errors' if results['errors'] else '✓ Aucune erreur'}")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    cli()
