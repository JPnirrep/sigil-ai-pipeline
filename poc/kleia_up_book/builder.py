"""
KLEIA-UP Book — EPUB Builder
Builds valid EPUB 3 files from parsed book structure
"""

import os, zipfile, hashlib
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from .parser import ParsedBook, render_xhtml, render_css_epub


EPUB_MIMETYPE = b"application/epub+zip"


def build_epub(book: ParsedBook, output_path: str, css_override: str = None) -> str:
    """
    Build a valid EPUB 3 file from a ParsedBook.
    Returns the output path.
    """
    output_path = str(Path(output_path).with_suffix(".epub"))
    uid = hashlib.md5(f"kleia-up:{book.title}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
    css = css_override or render_css_epub(book)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype (must be first, uncompressed)
        zf.writestr("mimetype", EPUB_MIMETYPE, compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        zf.writestr("META-INF/container.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""")

        # OEBPS/styles.css
        zf.writestr("OEBPS/styles.css", css)

        # OEBPS/content.xhtml
        body = render_xhtml(book)
        xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="fr">
<head>
  <meta charset="UTF-8"/>
  <title>{escape(book.title or 'Untitled')}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
{body}
</html>"""
        zf.writestr("OEBPS/content.xhtml", xhtml.encode("utf-8"))

        # OEBPS/nav.xhtml (EPUB3 navigation)
        nav_items = "".join(
            f'<li><a href="content.xhtml#_{i}">{escape(ch.title)}</a></li>'
            for i, ch in enumerate(book.chapters)
        )
        nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="fr">
<head><meta charset="UTF-8"/><title>Navigation</title></head>
<body>
  <nav epub:type="toc">
    <h1>Table des matières</h1>
    <ol>{nav_items}</ol>
  </nav>
</body>
</html>"""
        zf.writestr("OEBPS/nav.xhtml", nav.encode("utf-8"))

        # OEBPS/content.opf
        items = f"""
    <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="styles.css" media-type="text/css"/>"""

        spine = """
    <itemref idref="content"/>"""

        opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:{uid}</dc:identifier>
    <dc:title>{escape(book.title or 'Untitled')}</dc:title>
    <dc:creator>{escape(book.author or 'Unknown')}</dc:creator>
    <dc:language>fr</dc:language>
    <dc:date>{datetime.utcnow().strftime('%Y-%m-%d')}</dc:date>
    <meta property="dcterms:modified">{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
  </metadata>
  <manifest>{items}
  </manifest>
  <spine>{spine}
  </spine>
</package>"""
        zf.writestr("OEBPS/content.opf", opf.encode("utf-8"))

    return output_path
