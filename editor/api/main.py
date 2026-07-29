"""
KLEIA-UP Book Editor — Backend API
FastAPI server for book editing, preview, and export
"""

import os, sys, json, uuid, shutil
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Project root ──
_SCRIPT = Path(__file__).resolve()
_EDITOR_DIR = _SCRIPT.parent.parent
_POC_DIR = _EDITOR_DIR.parent / "poc"
if str(_POC_DIR) not in sys.path:
    sys.path.insert(0, str(_POC_DIR))

from kleia_up_book import run_pipeline
from kleia_up_book.parser import ParsedBook, ParsedChapter, KDPMetadata
from kleia_up_book.theme import generate_theme
from kleia_up_book.validator import validate_book

from .models import BookModel, ChapterModel, StyleOverrides, BookMetadata

# ── State ──
DATA_DIR = _EDITOR_DIR / ".data"
DATA_DIR.mkdir(exist_ok=True)

work_dir: Optional[Path] = None
current_book: Optional[BookModel] = None
current_style: StyleOverrides = StyleOverrides()
current_metadata: BookMetadata = BookMetadata()


def _chapters_dir() -> Path:
    return work_dir / "chapters"


def _style_path() -> Path:
    return work_dir / "style_overrides.json"


def _meta_path() -> Path:
    return work_dir / "metadata.json"


def _assets_dir() -> Path:
    p = work_dir / "assets"
    p.mkdir(exist_ok=True)
    return p


def _save_state():
    if not work_dir:
        return
    (work_dir / "book.json").write_text(
        current_book.model_dump_json(indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    _style_path().write_text(
        current_style.model_dump_json(indent=2),
        encoding="utf-8"
    )
    _meta_path().write_text(
        current_metadata.model_dump_json(indent=2),
        encoding="utf-8"
    )


def _load_state(book_dir: Path) -> bool:
    global current_book, current_style, current_metadata
    book_file = book_dir / "book.json"
    style_file = book_dir / "style_overrides.json"
    meta_file = book_dir / "metadata.json"
    if not book_file.exists():
        return False
    try:
        current_book = BookModel.model_validate_json(book_file.read_text(encoding="utf-8"))
        current_style = StyleOverrides.model_validate_json(
            style_file.read_text(encoding="utf-8")
        ) if style_file.exists() else StyleOverrides()
        current_metadata = BookMetadata.model_validate_json(
            meta_file.read_text(encoding="utf-8")
        ) if meta_file.exists() else BookMetadata()
        return True
    except Exception:
        return False


def _elements_to_html(elements: list) -> str:
    """Convert ParsedBook elements (tag, class, text) to rich HTML for TipTap."""
    parts = []
    for tag, cls, text in elements:
        cls_attr = f' class="{cls}"' if cls else ""
        # Escape text for safe HTML
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(f"<{tag}{cls_attr}>{safe}</{tag}>")
    return "\n".join(parts)


def _html_to_elements(html: str):
    """Parse rich HTML back into elements list for the parser.
    Strips tags but preserves them as (tag, class, text) tuples.
    For the prototype, we keep the HTML as-is and modify render_xhtml.
    """
    # The TipTap HTML is already rich — we'll inject it directly in preview/export
    return html


def _convert_parsed_book(pb: ParsedBook, source: str) -> BookModel:
    """Convert ParsedBook to BookModel for the editor."""
    chapters = []
    for i, ch in enumerate(pb.chapters):
        chapters.append(ChapterModel(
            id=str(i + 1),
            title=ch.title,
            content_html=_elements_to_html(ch.elements),
        ))

    # Front matter as HTML
    front_html = _elements_to_html(pb.front_matter)

    m = pb.metadata
    return BookModel(
        id=uuid.uuid4().hex[:12],
        title=pb.title,
        subtitle=pb.subtitle or "",
        author=pb.author or "",
        front_matter_html=front_html,
        chapters=chapters,
        trim_width=m.trim_width,
        trim_height=m.trim_height,
        margin_top=m.margin_top,
        margin_bottom=m.margin_bottom,
        margin_inner=m.margin_inner,
        margin_outer=m.margin_outer,
        bleed=m.bleed,
    )


# ── FastAPI ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="KLEIA-UP Book Editor",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ──

@app.get("/api/health")
def health():
    return {"status": "ok", "has_book": current_book is not None, "work_dir": str(work_dir or "")}


@app.post("/api/import")
async def import_docx(file: UploadFile = File(...)):
    """Import a DOCX file, parse it, and return the book model."""
    global work_dir, current_book, current_style, current_metadata

    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")

    # Save uploaded file
    try:
        session_id = uuid.uuid4().hex[:12]
        session_dir = DATA_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        docx_path = session_dir / "source.docx"
        content = await file.read()
        with open(docx_path, "wb") as f:
            f.write(content)

        # Parse DOCX using the existing pipeline
        from kleia_up_book.parser import parse_docx

        try:
            parsed: ParsedBook = parse_docx(str(docx_path))
        except Exception as e:
            import traceback as _tb
            err_detail = f"Failed to parse DOCX: {e}\n{_tb.format_exc()}"
            shutil.rmtree(session_dir)
            raise HTTPException(422, detail=err_detail)
    except HTTPException:
        raise
    except Exception as e:
        import traceback as _tb
        raise HTTPException(500, detail=f"Import error: {e}\n{_tb.format_exc()}")

    work_dir = session_dir
    current_book = _convert_parsed_book(parsed, file.filename)
    current_style = StyleOverrides()
    current_metadata = BookMetadata(
        word_count=_count_words(parsed),
        chapter_count=len(parsed.chapters),
        parsed_at=__import__("datetime").datetime.now().isoformat(),
        source_file=file.filename,
        genre_detected="default",
    )

    _save_state()

    return {
        "book": current_book.model_dump(),
        "metadata": current_metadata.model_dump(),
        "session": session_id,
    }


def _count_words(pb: ParsedBook) -> int:
    total = 0
    for _, _, t in pb.front_matter:
        total += len(t.split())
    for ch in pb.chapters:
        for _, _, t in ch.elements:
            total += len(t.split())
    return total


@app.get("/api/book")
def get_book():
    """Get the current book model."""
    if not current_book:
        raise HTTPException(404, "No book loaded")
    return {
        "book": current_book.model_dump(),
        "style": current_style.model_dump(),
        "metadata": current_metadata.model_dump(),
    }


class ChapterUpdate(BaseModel):
    title: str
    content_html: str


@app.patch("/api/book/chapter/{chapter_id}")
def update_chapter(chapter_id: str, update: ChapterUpdate):
    """Update a chapter's title and/or content."""
    if not current_book:
        raise HTTPException(404, "No book loaded")
    for ch in current_book.chapters:
        if ch.id == chapter_id:
            ch.title = update.title
            ch.content_html = update.content_html
            _save_state()
            return {"status": "ok", "chapter": ch.model_dump()}
    raise HTTPException(404, f"Chapter {chapter_id} not found")


class NewChapter(BaseModel):
    title: str = "Nouveau chapitre"
    after_id: Optional[str] = None


@app.post("/api/book/chapter")
def add_chapter(new: NewChapter):
    """Add a new chapter."""
    if not current_book:
        raise HTTPException(404, "No book loaded")
    ch = ChapterModel(
        id=uuid.uuid4().hex[:12],
        title=new.title,
        content_html="<p></p>",
    )
    if new.after_id:
        for i, c in enumerate(current_book.chapters):
            if c.id == new.after_id:
                current_book.chapters.insert(i + 1, ch)
                break
        else:
            current_book.chapters.append(ch)
    else:
        current_book.chapters.append(ch)

    _save_state()
    return {"status": "ok", "chapter": ch.model_dump()}


@app.delete("/api/book/chapter/{chapter_id}")
def delete_chapter(chapter_id: str):
    """Delete a chapter."""
    if not current_book:
        raise HTTPException(404, "No book loaded")
    before = len(current_book.chapters)
    current_book.chapters = [c for c in current_book.chapters if c.id != chapter_id]
    if len(current_book.chapters) == before:
        raise HTTPException(404, f"Chapter {chapter_id} not found")
    _save_state()
    return {"status": "ok"}


class ReorderBody(BaseModel):
    chapter_ids: list[str]


@app.put("/api/book/reorder")
def reorder_chapters(body: ReorderBody):
    """Reorder chapters by ID list."""
    if not current_book:
        raise HTTPException(404, "No book loaded")
    id_map = {c.id: c for c in current_book.chapters}
    new_order = []
    for cid in body.chapter_ids:
        if cid in id_map:
            new_order.append(id_map[cid])
    if len(new_order) != len(current_book.chapters):
        raise HTTPException(400, "Chapter ID list doesn't match book chapters")
    current_book.chapters = new_order
    _save_state()
    return {"status": "ok"}


class BookMetaUpdate(BaseModel):
    title: str = ""
    subtitle: str = ""
    author: str = ""


@app.post("/api/book/meta")
def update_book_meta(meta: BookMetaUpdate):
    """Update book title, subtitle, author."""
    if not current_book:
        raise HTTPException(404, "No book loaded")
    current_book.title = meta.title
    current_book.subtitle = meta.subtitle
    current_book.author = meta.author
    if current_metadata:
        current_metadata.source_file = meta.title or current_metadata.source_file
    _save_state()
    return {"status": "ok", "book": current_book.model_dump()}


@app.post("/api/book/cover")
async def upload_cover(file: UploadFile = File(...)):
    """Upload a book cover image."""
    if not work_dir:
        raise HTTPException(404, "No book loaded")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files")
    assets = _assets_dir()
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    cover_name = f"cover{ext}"
    cover_path = assets / cover_name
    with open(cover_path, "wb") as f:
        f.write(await file.read())
    # Save a marker in book state
    (work_dir / ".cover").write_text(cover_name, encoding="utf-8")
    return {"url": f"/api/assets/{cover_name}", "filename": cover_name}


@app.get("/api/book/cover")
def get_cover():
    """Get current cover URL."""
    if not work_dir:
        raise HTTPException(404, "No book loaded")
    cover_file = work_dir / ".cover"
    if not cover_file.exists():
        return {"url": None}
    name = cover_file.read_text(encoding="utf-8").strip()
    cover_path = _assets_dir() / name
    if not cover_path.exists():
        return {"url": None}
    from fastapi.responses import FileResponse
    return FileResponse(str(cover_path), media_type=f"image/{name.rsplit('.', 1)[-1]}")


ALIASES_PATH = _EDITOR_DIR / ".aliases.json"


def _load_aliases() -> list:
    if ALIASES_PATH.exists():
        try:
            return json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_aliases(aliases: list):
    ALIASES_PATH.write_text(json.dumps(aliases, indent=2, ensure_ascii=False), encoding="utf-8")


@app.get("/api/aliases")
def list_aliases():
    """List saved author aliases."""
    return {"aliases": _load_aliases()}


class AliasCreate(BaseModel):
    name: str


@app.post("/api/aliases")
def create_alias(alias: AliasCreate):
    """Save a new author alias."""
    name = alias.name.strip()
    if not name:
        raise HTTPException(400, "Name required")
    aliases = _load_aliases()
    if name not in aliases:
        aliases.append(name)
        _save_aliases(aliases)
    return {"status": "ok", "aliases": aliases}


@app.post("/api/style")
def update_style(style: StyleOverrides):
    """Save CSS style overrides."""
    global current_style
    current_style = style
    _save_state()
    return {"status": "ok"}


@app.get("/api/style")
def get_style():
    """Get current style overrides."""
    try:
        s = current_style
        if s is None:
            s = StyleOverrides()
        return s.model_dump()
    except Exception as e:
        import traceback
        raise HTTPException(500, detail=f"Style error: {e}\n{traceback.format_exc()}")


@app.get("/api/preview", response_class=HTMLResponse)
def preview_html():
    """Render XHTML + CSS with current edits and style overrides."""
    if not current_book:
        raise HTMLResponse("No book loaded", status_code=404)

    body_parts = ["<body>"]

    # Front matter as rendered title page
    body_parts.append('<section class="title-page">')
    if current_book.title:
        body_parts.append(f'<h1 class="book-title">{_escape_html(current_book.title)}</h1>')
    if current_book.subtitle:
        body_parts.append(f'<h2 class="book-subtitle">{_escape_html(current_book.subtitle)}</h2>')
    if current_book.author:
        body_parts.append(f'<p class="author">{_escape_html(current_book.author)}</p>')
    body_parts.append('</section>')

    # Chapters
    for ch in current_book.chapters:
        body_parts.append(f'<section class="chapter" epub:type="chapter">')
        body_parts.append(f'<h1 class="chapter-title">{_escape_html(ch.title)}</h1>')
        if ch.content_html:
            body_parts.append(ch.content_html)  # Rich HTML from TipTap
        body_parts.append('</section>')

    body_parts.append("</body>")
    body_html = "\n".join(body_parts)

    # Build CSS from style overrides
    s = current_style
    css = f"""/* KLEIA-UP Book Editor — Generated CSS */
body {{
    font-family: {s.body_font};
    font-size: {s.body_size};
    line-height: {s.body_line_height};
    color: {s.body_color};
    text-align: {s.body_alignment};
    margin: 0;
    padding: 20px;
}}

p {{
    margin-bottom: {s.body_margin_bottom};
}}

h1 {{
    font-family: {s.h1_font};
    font-size: {s.h1_size};
    font-weight: {s.h1_weight};
    text-align: {s.h1_align};
    color: {s.h1_color};
    margin-top: {s.h1_margin_top};
    margin-bottom: {s.h1_margin_bottom};
}}

h2 {{
    font-family: {s.h2_font};
    font-size: {s.h2_size};
    font-weight: {s.h2_weight};
    text-align: {s.h2_align};
    color: {s.h2_color};
    margin-top: {s.h2_margin_top};
    margin-bottom: {s.h2_margin_bottom};
}}

h3 {{
    font-family: {s.h3_font};
    font-size: {s.h3_size};
    font-weight: {s.h3_weight};
    text-align: {s.h3_align};
    color: {s.h3_color};
}}

img {{
    max-width: {s.image_max_width};
    display: block;
    margin-left: {'0' if s.image_align == 'left' else 'auto'};
    margin-right: {'0' if s.image_align == 'right' else 'auto'};
}}

/* Title page */
section.title-page {{
    text-align: center;
    padding-top: 20vh;
}}
h1.book-title {{ font-size: 2em; }}
h2.book-subtitle {{ font-size: 1.4em; font-style: italic; font-weight: normal; }}
p.author {{ font-size: 1.2em; margin-top: 2em; }}

/* Chapter */
h1.chapter-title {{
    page-break-before: always;
    margin-top: 2em;
    margin-bottom: 1em;
}}

/* Blockquote */
blockquote {{
    margin: 1em 2em;
    font-style: italic;
    color: #555;
}}

/* Images */
figure {{
    margin: 1em 0;
    text-align: center;
}}
figcaption {{
    font-style: italic;
    font-size: 0.9em;
    color: #666;
}}
"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8"/>
    <title>{_escape_html(current_book.title or 'Preview')}</title>
    <style>{css}</style>
</head>
{body_html}
</html>"""
    return html


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


@app.post("/api/export/epub")
def export_epub():
    """Export as EPUB and return the file."""
    if not current_book or not work_dir:
        raise HTTPException(404, "No book loaded")
    results = _do_export(["epub"])
    epub = results.get("epub")
    if not epub or not epub.exists():
        raise HTTPException(500, "EPUB export failed")
    return _file_response(epub)


@app.post("/api/export/pdf")
def export_pdf():
    """Export as PDF print-ready and return the file."""
    if not current_book or not work_dir:
        raise HTTPException(404, "No book loaded")
    results = _do_export(["pdf"])
    pdf = results.get("pdf")
    if not pdf or not pdf.exists():
        raise HTTPException(500, "PDF export failed")
    return _file_response(pdf)


@app.post("/api/export/both")
def export_both():
    """Export EPUB + PDF and return paths in JSON."""
    if not current_book or not work_dir:
        raise HTTPException(404, "No book loaded")
    results = _do_export(["epub", "pdf"])
    return {k: str(v) for k, v in results.items() if v and v.exists()}


def _build_book_xhtml(book: BookModel, style: StyleOverrides, with_paged: bool = False) -> str:
    """Build full XHTML from current book state, including TipTap content."""
    css = _build_css(style, with_paged, book)

    body_parts = ['<body epub:type="bodymatter">']

    # Title page
    body_parts.append('<section epub:type="titlepage">')
    if book.title:
        body_parts.append(f'<h1 class="book-title">{_escape_html(book.title)}</h1>')
    if book.subtitle:
        body_parts.append(f'<h2 class="book-subtitle">{_escape_html(book.subtitle)}</h2>')
    if book.author:
        body_parts.append(f'<p class="author">{_escape_html(book.author)}</p>')
    body_parts.append('</section>')

    # Chapters
    for i, ch in enumerate(book.chapters):
        body_parts.append(f'<section epub:type="chapter" class="chapter" id="ch-{i+1}">')
        body_parts.append(f'<h1 class="chapter-title">{_escape_html(ch.title)}</h1>')
        if ch.content_html:
            # Strip wrapping <p></p> if it's the only content (TipTap wraps everything in <p>)
            body_parts.append(ch.content_html)
        body_parts.append('</section>')

    body_parts.append('</body>')
    body_html = '\n'.join(body_parts)

    paged_js = ''
    if with_paged:
        paged_js = '''<script>
(function(){
var s=document.createElement('script');
s.src='data:text/javascript;base64,';
// Paged.js polyfill for print CSS
})();
</script>'''

    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="fr">
<head>
<meta charset="utf-8"/>
<title>{_escape_html(book.title or 'Book')}</title>
<style>{css}</style>
</head>
{body_html}
</html>'''


def _build_css(style: StyleOverrides, with_paged: bool = False, book: BookModel = None) -> str:
    """Generate CSS from style overrides."""
    s = style
    b = book or current_book  # fallback for page sizes
    css = f'''/* KLEIA-UP Book Editor — Generated CSS */
@namespace epub "http://www.idpf.org/2007/ops";

body {{
    font-family: {s.body_font};
    font-size: {s.body_size};
    line-height: {s.body_line_height};
    color: {s.body_color};
    text-align: {s.body_alignment};
    margin: 0;
    padding: 0;
    widows: 2;
    orphans: 2;
}}

p {{
    margin-bottom: {s.body_margin_bottom};
    text-indent: 0;
}}

h1 {{
    font-family: {s.h1_font};
    font-size: {s.h1_size};
    font-weight: {s.h1_weight};
    text-align: {s.h1_align};
    color: {s.h1_color};
    margin-top: {s.h1_margin_top};
    margin-bottom: {s.h1_margin_bottom};
    page-break-after: avoid;
}}

h2 {{
    font-family: {s.h2_font};
    font-size: {s.h2_size};
    font-weight: {s.h2_weight};
    text-align: {s.h2_align};
    color: {s.h2_color};
    margin-top: {s.h2_margin_top};
    margin-bottom: {s.h2_margin_bottom};
    page-break-after: avoid;
}}

h3 {{
    font-family: {s.h3_font};
    font-size: {s.h3_size};
    font-weight: {s.h3_weight};
    text-align: {s.h3_align};
    color: {s.h3_color};
    page-break-after: avoid;
}}

img {{
    max-width: {s.image_max_width};
    height: auto;
}}

figure {{
    text-align: {'center' if s.image_align == 'center' else s.image_align};
    margin: 1em 0;
}}

figcaption {{
    font-style: italic;
    font-size: 0.9em;
    color: #666;
}}

blockquote {{
    margin: 1em 2em;
    font-style: italic;
    color: #555;
}}

/* Title page */
section[epub\\:type="titlepage"] {{
    text-align: center;
    padding-top: 20vh;
}}
h1.book-title {{
    font-size: 2em;
    margin-bottom: 0.3em;
}}
h2.book-subtitle {{
    font-size: 1.4em;
    font-style: italic;
    font-weight: normal;
}}
p.author {{
    font-size: 1.2em;
    margin-top: 2em;
}}

/* Chapters */
h1.chapter-title {{
    page-break-before: always;
}}
'''

    if with_paged:
        css += f'''
@page {{
    size: {b.trim_width}in {b.trim_height}in;
    margin-top: {b.margin_top}in;
    margin-bottom: {b.margin_bottom}in;
    @bottom-center {{
        content: counter(page);
        font-size: 9pt;
        color: #666;
    }}
}}
@page :first {{
    @bottom-center {{
        content: none;
    }}
}}
'''

    return css


def _is_valid_epub(epub_path: Path) -> bool:
    """Quick check that a file is a valid EPUB (ZIP with mimetype)."""
    try:
        import zipfile
        with zipfile.ZipFile(epub_path, 'r') as zf:
            return 'mimetype' in zf.namelist() and 'META-INF/container.xml' in zf.namelist()
    except Exception:
        return False


def _do_export(formats: list) -> dict:
    """Export EPUB(s) directly from current book state.
    Returns dict of {format: Path}."""
    if not current_book:
        raise HTTPException(404, "No book loaded")

    out_dir = work_dir / "export"
    out_dir.mkdir(exist_ok=True)

    results = {}

    if "epub" in formats:
        epub_path = _export_epub(out_dir)
        if epub_path:
            results["epub"] = epub_path

    if "pdf" in formats:
        pdf_path = _export_pdf(out_dir)
        if pdf_path:
            results["pdf"] = pdf_path

    return results


def _export_epub(out_dir: Path) -> Path:
    """Build EPUB 3 directly from current book state."""
    import zipfile, hashlib
    from xml.sax.saxutils import escape

    book = current_book
    style = current_style

    epub_path = out_dir / f"{book.title or 'book'}.epub"
    uid = hashlib.md5(f"kleia:{book.id}:{len(book.chapters)}".encode()).hexdigest()[:12]

    # Build XHTML content
    xhtml_content = _build_book_xhtml(book, style)

    # Build navigation
    nav_items = ''.join(
        f'<li><a href="content.xhtml#ch-{i+1}">{escape(ch.title)}</a></li>'
        for i, ch in enumerate(book.chapters)
    )
    nav_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="fr">
<head><title>Navigation</title></head>
<body>
<nav epub:type="toc">
<h1>Table des matières</h1>
<ol>
{nav_items}
</ol>
</nav>
</body>
</html>'''

    # ── Cover ──
    cover_info = None
    if work_dir:
        cover_file = work_dir / ".cover"
        if cover_file.exists():
            cname = cover_file.read_text(encoding="utf-8").strip()
            cpath = _assets_dir() / cname
            if cpath.exists():
                cbytes = cpath.read_bytes()
                ext = cname.rsplit(".", 1)[-1].lower()
                cmime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/jpeg")
                cover_info = (f"cover.{ext}", cbytes, cmime)

    manifest_items = [
        '<item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="css" href="styles.css" media-type="text/css"/>',
    ]
    spine_refs = ['<itemref idref="content"/>']

    if cover_info:
        manifest_items.append(f'<item id="cover" href="{cover_info[0]}" media-type="{cover_info[2]}" properties="cover-image"/>')
        spine_refs.insert(0, '<itemref idref="cover" linear="no"/>')

    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="book-id">urn:uuid:{uid}</dc:identifier>
<dc:title>{escape(book.title or '')}</dc:title>
<dc:creator>{escape(book.author or '')}</dc:creator>
<dc:language>fr</dc:language>
<meta property="dcterms:modified">{__import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</meta>
</metadata>
<manifest>
{"".join(manifest_items)}
</manifest>
<spine>
{"".join(spine_refs)}
</spine>
</package>'''

    css = _build_css(style, book=current_book)

    with zipfile.ZipFile(str(epub_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', b'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        zf.writestr('META-INF/container.xml',
            '<?xml version="1.0" encoding="utf-8"?>'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>')
        zf.writestr('OEBPS/content.opf', opf.encode('utf-8'))
        zf.writestr('OEBPS/nav.xhtml', nav_xhtml.encode('utf-8'))
        zf.writestr('OEBPS/content.xhtml', xhtml_content.encode('utf-8'))
        zf.writestr('OEBPS/styles.css', css.encode('utf-8'))
        if cover_info:
            zf.writestr(f'OEBPS/{cover_info[0]}', cover_info[1])

    return epub_path


def _export_pdf(out_dir: Path) -> Path:
    """Build print-ready PDF via Playwright + CSS Paged Media.
    Falls back to simple HTML → PDF if Playwright unavailable."""
    import tempfile

    book = current_book
    style = current_style

    pdf_path = out_dir / f"{book.title or 'book'}.pdf"

    # Build full HTML with print CSS
    xhtml = _build_book_xhtml(book, style, with_paged=True)

    # Write to temp HTML
    html_path = out_dir / "_print.html"
    html_path.write_text(xhtml, encoding="utf-8")

    # Try Playwright first
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(str(html_path.resolve()), wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                width=f"{book.trim_width}in",
                height=f"{book.trim_height}in",
                margin={
                    'top': f"{book.margin_top}in",
                    'bottom': f"{book.margin_bottom}in",
                    'left': f"{book.margin_inner}in",
                    'right': f"{book.margin_outer}in",
                },
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()

        return pdf_path

    except Exception as e_pw:
        # Fallback: try WeasyPrint
        try:
            from weasyprint import HTML
            HTML(filename=str(html_path.resolve())).write_pdf(str(pdf_path))
            return pdf_path
        except Exception as e_wp:
            raise HTTPException(500,
                detail=f"PDF export failed. Playwright: {e_pw}\nWeasyPrint: {e_wp}")


def _file_response(path: Path):
    if not path.exists():
        raise HTTPException(500, f"Export file not found: {path}")
    return FileResponse(
        str(path),
        media_type="application/octet-stream",
        filename=path.name,
    )


def _file_response(path: Path):
    if not path.exists():
        raise HTTPException(500, f"Export file not found: {path}")
    return FileResponse(
        str(path),
        media_type="application/octet-stream",
        filename=path.name,
    )


@app.post("/api/image/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to the book's assets directory."""
    if not work_dir:
        raise HTTPException(404, "No book loaded")
    assets = _assets_dir()
    img_path = assets / file.filename
    with open(img_path, "wb") as f:
        f.write(await file.read())
    return {"url": f"/api/assets/{file.filename}", "filename": file.filename}


@app.get("/api/assets/{filename}")
def get_asset(filename: str):
    """Serve an uploaded or extracted asset."""
    if not work_dir:
        raise HTTPException(404, "No book loaded")
    assets = _assets_dir()
    path = assets / filename
    if not path.exists():
        raise HTTPException(404, f"Asset {filename} not found")
    return FileResponse(str(path))


@app.post("/api/session/load")
def load_session(session_id: str):
    """Load a previous session by ID."""
    global work_dir, current_book, current_style, current_metadata
    session_dir = DATA_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(404, f"Session {session_id} not found")
    work_dir = session_dir
    if not _load_state(session_dir):
        raise HTTPException(500, "Failed to load session state")
    return {
        "book": current_book.model_dump(),
        "style": current_style.model_dump(),
        "metadata": current_metadata.model_dump(),
    }


@app.get("/api/sessions")
def list_sessions():
    """List all available sessions."""
    sessions = []
    for d in sorted(DATA_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if d.is_dir():
            meta = d / "metadata.json"
            book_json = d / "book.json"
            source = d / "source.docx"
            info = {
                "id": d.name,
                "source": source.name if source.exists() else "",
                "has_book": book_json.exists(),
            }
            if meta.exists():
                try:
                    info["metadata"] = json.loads(meta.read_text(encoding="utf-8"))
                except Exception:
                    pass
            sessions.append(info)
    return {"sessions": sessions}


TEMPLATES_DIR = _EDITOR_DIR / "templates"


@app.get("/api/templates")
def list_templates():
    """List available KDP manuscript templates."""
    if not TEMPLATES_DIR.exists():
        return {"templates": []}
    items = []
    for f in sorted(TEMPLATES_DIR.iterdir()):
        if f.suffix == ".docx":
            sz = f.stat().st_size
            name = f.stem.replace("kdp-template-", "").replace("-", " ").title()
            items.append({
                "name": name,
                "filename": f.name,
                "size": sz,
                "size_str": f"{sz / 1024:.0f} KB",
            })
    return {"templates": items}


@app.get("/api/templates/{filename}")
def download_template(filename: str):
    """Download a KDP template."""
    fpath = TEMPLATES_DIR / filename
    if not fpath.exists():
        raise HTTPException(404, f"Template {filename} not found")
    from fastapi.responses import FileResponse
    return FileResponse(
        str(fpath.resolve()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
