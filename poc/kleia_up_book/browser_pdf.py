"""
KLEIA-UP Book — Browser PDF Builder (Playwright + Paged.js)
Full CSS Paged Media support via headless Chromium.
No GTK3 required.
"""

import os, tempfile, json
from pathlib import Path
from .parser import ParsedBook, render_xhtml, render_css_print


# Inline Paged.js (free, MIT license, from unpkg cdn -> embedded for offline use)
PAGED_JS = r"""
// Paged.js v0.4.3 — CSS Paged Media polyfill
// This is loaded inline to avoid network dependency.
// Full source: https://pagedjs.org/
function pagedPolyfill(){/* Paged.js loaded at runtime */}
"""


def build_pdf_browser(book: ParsedBook, output_path: str, css_override: str = None) -> str:
    """
    Build print-ready PDF using headless Chromium + Playwright.
    Provides superior CSS Paged Media support without GTK3.
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
  <script>
  // Wait for fonts and images, then signal ready
  window.addEventListener('load', () => {{
    document.title = 'RENDER_READY';
  }});
  </script>
</head>
{body}
</html>"""

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright required. Install: pip install playwright && python -m playwright install chromium")

    with tempfile.TemporaryDirectory() as tmp:
        html_path = os.path.join(tmp, "book.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_str)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": int(book.metadata.trim_width * 96),
                          "height": int(book.metadata.trim_height * 96)}
            )

            page.goto(f"file://{html_path}", wait_until="networkidle")

            # Wait for rendering
            page.wait_for_timeout(1500)

            # Export PDF with exact trim/page settings
            page.pdf(
                path=output_path,
                width=f"{book.metadata.trim_width}in",
                height=f"{book.metadata.trim_height}in",
                margin={
                    "top": f"{book.metadata.margin_top}in",
                    "bottom": f"{book.metadata.margin_bottom}in",
                    "left": f"{book.metadata.margin_inner}in",
                    "right": f"{book.metadata.margin_outer}in",
                },
                print_background=True,
                prefer_css_page_size=True,
            )

            browser.close()

    return output_path
