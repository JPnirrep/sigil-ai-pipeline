"""
KLEIA-UP Book — Print PDF Builder
Generates print-ready PDF via cascade:
1. Playwright/Chromium (best CSS Paged Media, no GTK)  ← RECOMMENDED for Windows
2. WeasyPrint (full CSS Paged Media, requires GTK3)    ← BEST on Linux/Mac
3. pdfkit/wkhtmltopdf (basic print, no @page)          ← FALLBACK
"""

import os, tempfile
from pathlib import Path
from .parser import ParsedBook, render_xhtml, render_css_print


def _get_browser_pdf():
    try:
        from .browser_pdf import build_pdf_browser
        # Quick check: can we import playwright?
        import playwright.sync_api
        return build_pdf_browser
    except Exception:
        return None


def _get_weasyprint():
    try:
        from weasyprint import HTML
        return lambda book, out, css: _weasyprint_render(HTML, book, out, css)
    except Exception:
        return None


def _weasyprint_render(HTML, book, out, css):
    with tempfile.TemporaryDirectory() as tmp:
        html_path = os.path.join(tmp, "book.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(_build_html(book, css))
        HTML(filename=html_path).write_pdf(out)
    return out


def _get_pdfkit():
    try:
        import pdfkit
        return lambda book, out, css: _pdfkit_render(pdfkit, book, out, css)
    except Exception:
        return None


def _pdfkit_render(pdfkit, book, out, css):
    options = {
        "page-width": f"{book.metadata.trim_width}in",
        "page-height": f"{book.metadata.trim_height}in",
        "margin-top": f"{book.metadata.margin_top}in",
        "margin-bottom": f"{book.metadata.margin_bottom}in",
        "margin-left": f"{book.metadata.margin_inner}in",
        "margin-right": f"{book.metadata.margin_outer}in",
        "no-outline": None,
        "encoding": "UTF-8",
        "enable-local-file-access": None,
        "print-media-type": None,
    }
    with tempfile.TemporaryDirectory() as tmp:
        html_path = os.path.join(tmp, "book.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(_build_html(book, css))
        pdfkit.from_file(html_path, out, options=options)
    return out


def _build_html(book, css):
    body = render_xhtml(book)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>{book.title or 'Untitled'}</title>
  <style>{css}</style>
</head>
{body}
</html>"""


def build_pdf(book: ParsedBook, output_path: str, css_override: str = None) -> str:
    """
    Build a print-ready PDF using the best available engine.
    Priority: Playwright/Chromium > WeasyPrint > pdfkit.
    """
    output_path = str(Path(output_path).with_suffix(".pdf"))
    css = css_override or render_css_print(book)

    engines = [
        ("Playwright/Chromium", _get_browser_pdf()),
        ("WeasyPrint", _get_weasyprint()),
        ("pdfkit", _get_pdfkit()),
    ]

    errors = []
    for name, engine in engines:
        if engine:
            try:
                engine(book, output_path, css)
                return output_path
            except Exception as e:
                errors.append(f"{name}: {e}")

    raise RuntimeError(
        "No PDF engine available.\n"
        f"Errors: {'; '.join(errors)}\n"
        "Install one:\n"
        "  pip install playwright && python -m playwright install chromium\n"
        "  pip install weasyprint + GTK3\n"
        "  pip install pdfkit && choco install wkhtmltopdf"
    )
