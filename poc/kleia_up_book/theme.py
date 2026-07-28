"""
KLEIA-UP Book — AI Theme Generator
Generates CSS themes using LLM, with fallback heuristics
"""

import json, os
from dataclasses import dataclass, field
from pathlib import Path

from .parser import ParsedBook, render_css_epub, render_css_print


# ── Genre-based theme presets (fallback when LLM unavailable) ──

GENRE_PRESETS = {
    "fiction": {
        "name": "Classic Novel",
        "epub": {
            "body-font": "Georgia, serif",
            "heading-font": "Georgia, serif",
            "size": "1em",
            "line-height": "1.5",
            "color": "#1a1a1a",
        },
        "print": {
            "body-font": '"Times New Roman", Georgia, serif',
            "heading-font": '"Times New Roman", Georgia, serif',
            "size": "11pt",
            "line-height": "1.3",
            "color": "#000",
        },
        "colors": {"text": "#1a1a1a", "paper": "#faf8f5", "accent": "#8b4513"},
        "style": {"hyphenation": True, "dropcaps": True, "first-para-no-indent": True},
    },
    "scifi": {
        "name": "Neon Futurist",
        "epub": {
            "body-font": '"IBM Plex Sans", Arial, sans-serif',
            "heading-font": '"Orbitron", "Arial Black", sans-serif',
            "size": "1em",
            "line-height": "1.45",
            "color": "#d4d4d4",
        },
        "print": {
            "body-font": '"Crimson Text", "Times New Roman", serif',
            "heading-font": '"Rajdhani", "Arial", sans-serif',
            "size": "11pt",
            "line-height": "1.3",
            "color": "#000",
        },
        "colors": {"text": "#1a1a2e", "paper": "#f0f0f2", "accent": "#e94560"},
        "style": {"hyphenation": True, "dropcaps": False, "first-para-no-indent": True},
    },
    "nonfiction": {
        "name": "Professional Clear",
        "epub": {
            "body-font": "Georgia, serif",
            "heading-font": '"Helvetica Neue", Arial, sans-serif',
            "size": "1em",
            "line-height": "1.5",
            "color": "#333",
        },
        "print": {
            "body-font": '"Palatino Linotype", "Book Antiqua", serif',
            "heading-font": '"Helvetica", Arial, sans-serif',
            "size": "11pt",
            "line-height": "1.2",
            "color": "#000",
        },
        "colors": {"text": "#2d2d2d", "paper": "#ffffff", "accent": "#2a6496"},
        "style": {"hyphenation": True, "dropcaps": False, "first-para-no-indent": False},
    },
    "fantasy": {
        "name": "Elegant Myth",
        "epub": {
            "body-font": '"Lora", Georgia, serif',
            "heading-font": '"Cinzel", Georgia, serif',
            "size": "1em",
            "line-height": "1.5",
            "color": "#1a1a1a",
        },
        "print": {
            "body-font": '"Garamond", "Times New Roman", serif',
            "heading-font": '"Cinzel", "Georgia", serif',
            "size": "11pt",
            "line-height": "1.25",
            "color": "#000",
        },
        "colors": {"text": "#1a1a1a", "paper": "#faf3e0", "accent": "#6b3a2a"},
        "style": {"hyphenation": True, "dropcaps": True, "first-para-no-indent": True},
    },
    "default": {
        "name": "Standard Clean",
        "epub": {
            "body-font": "Georgia, serif",
            "heading-font": "Arial, sans-serif",
            "size": "1em",
            "line-height": "1.5",
            "color": "#333",
        },
        "print": {
            "body-font": '"Times New Roman", serif',
            "heading-font": '"Helvetica", Arial, sans-serif',
            "size": "11pt",
            "line-height": "1.3",
            "color": "#000",
        },
        "colors": {"text": "#333", "paper": "#ffffff", "accent": "#555"},
        "style": {"hyphenation": True, "dropcaps": False, "first-para-no-indent": False},
    },
}


def _detect_genre(book: ParsedBook) -> str:
    """Heuristic genre detection from content analysis"""
    text = " ".join(
        ch.title + " " + " ".join(t for _, _, t in ch.elements)
        for ch in book.chapters
    ).lower()

    scifi_keywords = ["néon", "cyber", "implant", "androïde", "synthe", "nexus",
                      "data", "quantique", "ia ", "ia.", "ia,", "intelligence artificielle",
                      "chrome", "laser", "hologramme", "réseau"]
    fantasy_keywords = ["épée", "magie", "royaume", "dragon", "prophétie", "elfe",
                        "nain", "sorcier", "quête", "légende"]
    nonfiction_keywords = ["étude", "analyse", "recherche", "données", "résultat",
                           "chapitre 1", "introduction", "conclusion", "méthode"]

    score = {"scifi": 0, "fantasy": 0, "nonfiction": 0}
    for kw in scifi_keywords:
        if kw in text: score["scifi"] += 1
    for kw in fantasy_keywords:
        if kw in text: score["fantasy"] += 1
    for kw in nonfiction_keywords:
        if kw in text: score["nonfiction"] += 1

    if score["scifi"] >= 3: return "scifi"
    if score["fantasy"] >= 3: return "fantasy"
    if score["nonfiction"] >= 3: return "nonfiction"
    if book.subtitle and "roman" in book.subtitle.lower(): return "fiction"
    return "default"


def generate_theme(book: ParsedBook, genre: str = None):
    """Generate EPUB + Print CSS from genre preset or LLM"""
    if not genre:
        genre = _detect_genre(book)
    preset = GENRE_PRESETS.get(genre, GENRE_PRESETS["default"])

    # We'll build the CSS using the preset values
    epub_css = _preset_to_css_epub(preset, book)
    print_css = _preset_to_css_print(preset, book)

    return {
        "genre": genre,
        "theme_name": preset["name"],
        "css_epub": epub_css,
        "css_print": print_css,
        "preset": preset,
    }


def _preset_to_css_epub(preset: dict, book: ParsedBook) -> str:
    """Build EPUB CSS from preset configuration"""
    p = preset
    c = p["colors"]
    s = p["style"]
    return f"""/* KLEIA-UP Book — Theme: {p['name']} */
body {{
  font-family: {p['epub']['body-font']};
  font-size: {p['epub']['size']};
  line-height: {p['epub']['line-height']};
  color: {c['text']};
  background-color: {c['paper']};
  margin: 0;
  padding: 0;
}}

h1.book-title {{
  text-align: center;
  font-family: {p['epub']['heading-font']};
  font-size: 2em;
  color: {c['accent']};
  margin-top: 20%;
  margin-bottom: 0.5em;
}}

h2.book-subtitle {{
  text-align: center;
  font-size: 1.3em;
  font-style: italic;
  font-weight: normal;
}}

p.author {{
  text-align: center;
  font-size: 1.1em;
  margin-top: 2em;
}}

h1.chapter-title {{
  font-family: {p['epub']['heading-font']};
  font-size: 1.5em;
  text-align: left;
  color: {c['accent']};
  margin-top: 2em;
  margin-bottom: 1em;
  page-break-before: always;
}}

section.chapter p.body-text {{
  text-indent: 1.5em;
  margin: 0 0 0.5em 0;
  {'hyphens: auto;' if s['hyphenation'] else ''}
}}

section.chapter p.first-para {{
  text-indent: 0;
  margin: 0 0 0.5em 0;
  {'font-variant: small-caps;' if s['dropcaps'] else ''}
}}

blockquote {{
  margin: 1em 2em;
  font-style: italic;
}}

/* ── Front matter ── */
section.title-page {{
  page-break-after: always;
  text-align: center;
  padding-top: 20%;
}}

section.front-matter-toc {{
  page-break-before: always;
}}

section.front-matter-intro {{
  page-break-before: always;
}}

/* ── Number highlighting ── */
span.num {{
  font-weight: bold;
  font-size: 1.1em;
  color: {c['accent']};
}}
"""


def _preset_to_css_print(preset: dict, book: ParsedBook) -> str:
    """Build Print CSS from preset configuration with Paged Media"""
    p = preset
    c = p["colors"]
    s = p["style"]
    m = book.metadata

    dropcap_css = """p.first-para::first-letter {
    font-size: 3em;
    font-weight: bold;
    float: left;
    line-height: 0.8;
    margin-right: 0.15em;
    color: $accent$;
  }""".replace("$accent$", c["accent"]) if s["dropcaps"] else ""

    return f"""/* KLEIA-UP Book Print — Theme: {p['name']} */
@page {{
  size: {m.trim_width}in {m.trim_height}in;
  margin: {m.margin_top}in {m.margin_outer}in {m.margin_bottom}in {m.margin_inner}in;
  bleed: {m.bleed}in;
}}

@page :left {{
  margin-left: {m.margin_inner}in;
  margin-right: {m.margin_outer}in;
  @top-left {{
    content: string(book-title);
    font-family: {p['print']['heading-font']};
    font-size: 8pt;
    font-style: italic;
    color: {c['accent']};
  }}
  @bottom-left {{
    content: counter(page);
    font-size: 8pt;
    font-family: {p['print']['heading-font']};
  }}
}}

@page :right {{
  margin-left: {m.margin_outer}in;
  margin-right: {m.margin_inner}in;
  @top-right {{
    content: string(chapter-title);
    font-family: {p['print']['heading-font']};
    font-size: 8pt;
    font-style: italic;
    color: {c['accent']};
  }}
  @bottom-right {{
    content: counter(page);
    font-size: 8pt;
    font-family: {p['print']['heading-font']};
  }}
}}

@page chapter:first {{
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
}}

body {{
  font-family: {p['print']['body-font']};
  font-size: {p['print']['size']};
  line-height: {p['print']['line-height']};
  color: {c['text']};
}}

h1.book-title {{
  string-set: book-title content(text);
  font-family: {p['print']['heading-font']};
  text-align: center;
  font-size: 24pt;
  color: {c['accent']};
  margin-top: 30%;
  page-break-after: always;
}}

h1.chapter-title {{
  string-set: chapter-title content(text);
  page: chapter;
  page-break-before: right;
  font-family: {p['print']['heading-font']};
  font-size: 16pt;
  text-align: center;
  color: {c['accent']};
  margin-top: 20%;
  margin-bottom: 1.5em;
}}

p.body-text {{
  text-indent: 1.5em;
  margin: 0 0 0.3em 0;
  {'hyphens: auto;' if s['hyphenation'] else ''}
  widows: 2;
  orphans: 2;
}}

p.first-para {{
  text-indent: 0;
  margin: 0 0 0.3em 0;
}}

{dropcap_css}

section.copyright {{
  text-align: center;
  font-size: 9pt;
  margin-top: 10%;
  page-break-before: left;
}}

/* ── Front matter ── */
section.title-page {{
  page-break-after: always;
  text-align: center;
  padding-top: 30%;
}}

section.front-matter-toc {{
  page-break-before: left;
}}

section.front-matter-intro {{
  page-break-before: left;
}}

/* ── Number highlighting ── */
span.num {{
  font-weight: bold;
  font-size: 1.1em;
  color: {c['accent']};
}}
"""



# ── LLM Bridge ──

def generate_theme_llm(book: ParsedBook, genre: str = None):
    """Generate theme using LLM. Falls back to preset on failure."""
    if not genre:
        genre = _detect_genre(book)

    try:
        llm_result = _try_llm_theme(book, genre)
        if llm_result:
            return llm_result
    except Exception:
        pass

    return generate_theme(book, genre)


def _try_llm_theme(book, genre):
    """Try to get a theme from the session LLM. Returns None if unavailable."""
    try:
        chapter_titles = [ch.title for ch in book.chapters[:5]]
        sample_text = ""
        for ch in book.chapters[:1]:
            for _, _, t in ch.elements[:3]:
                sample_text += t[:200] + "\n"

        prompt = f"""Tu es un designer de livres spécialisé.

Analyse ce livre et génère un thème CSS complet au format JSON.

Genre détecté : {genre}
Titre : {book.title or 'Inconnu'}
Chapitres : {chapter_titles[:3]}
Extrait : {sample_text[:500]}

Retourne UNIQUEMENT un objet JSON valide avec cette structure exacte :
{{
  "theme_name": "nom du thème",
  "genre": "{genre}",
  "epub": {{
    "body-font": "police, fallback, serif",
    "heading-font": "police titres, fallback",
    "size": "1em",
    "line-height": "1.5",
    "color": "#hex"
  }},
  "print": {{
    "body-font": '"Times New Roman", serif',
    "heading-font": '"Helvetica", sans-serif',
    "size": "11pt",
    "line-height": "1.3",
    "color": "#000"
  }},
  "colors": {{
    "text": "#hex",
    "paper": "#hex",
    "accent": "#hex"
  }},
  "style": {{
    "hyphenation": true,
    "dropcaps": false,
    "first-para-no-indent": true
  }}
}}
"""

        # Use eval's global completion if available
        import builtins
        if hasattr(builtins, '_completion'):
            result = builtins._completion(prompt, model="smol")
        else:
            return None

        data = json.loads(result)
        preset = {
            "name": data.get("theme_name", "LLM Theme"),
            "epub": data.get("epub", {}),
            "print": data.get("print", {}),
            "colors": data.get("colors", {}),
            "style": data.get("style", {}),
        }

        epub_css = _preset_to_css_epub(preset, book)
        print_css = _preset_to_css_print(preset, book)

        return {
            "genre": genre,
            "theme_name": preset["name"],
            "css_epub": epub_css,
            "css_print": print_css,
            "preset": preset,
            "llm_generated": True,
        }
    except Exception as e:
        return None
