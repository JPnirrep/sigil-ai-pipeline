"""
KLEIA-UP Book — Print PDF Builder
Generates print-ready PDF via WeasyPrint (primary) or pdfkit (fallback).
WeasyPrint supports full CSS Paged Media (@page :left/:right, running elements).
"""

import os, tempfile
from pathlib import Path
from .parser import ParsedBook, render_xhtml, render_css_print


def _get_weasyprint():
    try:
        from weasyprint import HTML
        return ("weasyprint", HTML)
    except Exception:
        return None


def _get_pdfkit():
    try:
        import pdfkit
        return ("pdfkit", pdfkit)
    except Exception:
        return None


def build_pdf(book: ParsedBook, output_path: str, css_override: str = None) -> str:
    """
    Build a print-ready PDF.
    WeasyPrint (full CSS Paged Media) >> pdfkit (basic print layout).
    """
    output_path = str(Path(output_path).with_suffix(".pdf"))
    css = css_override or render_css_print(book)
    body = render_xhtml(book)

    html_str = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>{book.title or 'Untitled'}</title>
  <style>{css}</style>
</head>
{body}
</html>"""

    # WeasyPrint (full Paged Media)
    wp = _get_weasyprint()
    if wp:
        _, HTML = wp
        with tempfile.TemporaryDirectory() as tmp:
            html_path = os.path.join(tmp, "book.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_str)
            HTML(filename=html_path).write_pdf(output_path)
        return output_path

    # pdfkit fallback (basic print, no @page :left/:right)
    pk = _get_pdfkit()
    if pk:
        _, pdfkit = pk
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
                f.write(html_str)
            pdfkit.from_file(html_path, output_path, options=options)
        return output_path

    raise RuntimeError(
        "No PDF engine available.\n"
        "Install one:\n"
        "  - WeasyPrint (recommended, full CSS Paged Media): pip install weasyprint + GTK3\n"
        "  - pdfkit (basic): pip install pdfkit + choco install wkhtmltopdf"
    )
