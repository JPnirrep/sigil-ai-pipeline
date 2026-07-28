"""
KLEIA-UP Book — AI Core Module
LLM bridge: theme generation, content cleaning, design advice, accessibility
"""

import json, re, hashlib, os, time, sys
from pathlib import Path
from typing import Optional

# ── Cache ──
_CACHE_DIR = Path(__file__).parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)

_completion_func = None

def set_completion(func):
    global _completion_func
    _completion_func = func

def _get_completion():
    """Find the completion function: module global, eval scope, or caller scope."""
    if _completion_func:
        return _completion_func
    # Search caller frames for `completion`
    try:
        for frame_info in sys._current_frames().values():
            if 'completion' in frame_info.f_locals:
                return frame_info.f_locals['completion']
    except Exception:
        pass
    return None

def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

def _cache_get(key: str) -> Optional[str]:
    p = _CACHE_DIR / key
    return p.read_text(encoding="utf-8") if p.exists() else None

def _cache_set(key: str, value: str):
    (_CACHE_DIR / key).write_text(value, encoding="utf-8")

def llm_complete(prompt: str, model: str = "smol",
                 system: str = None, cache: bool = True,
                 max_retries: int = 2) -> Optional[str]:
    """Call LLM with fallback chain. Returns raw text or None."""
    key = _cache_key(prompt[:200]) if cache else None
    if key:
        cached = _cache_get(key)
        if cached:
            return cached

    fn = _get_completion()
    if not fn:
        return None

    models = [model, "smol", "default"]
    for attempt in range(max_retries + 1):
        for m in models:
            try:
                result = fn(prompt, model=m, system=system)
                if result and len(result) > 10:
                    if key:
                        _cache_set(key, result)
                    return result
            except Exception:
                continue
        time.sleep(0.3 * (attempt + 1))
    return None

def extract_json(text: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling markdown and common errors."""
    text = text.strip()
    for s in [text,
              *(re.findall(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)),
              *(re.findall(r'\{[^{}]*\}', text))]:
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    # Repair: trailing commas, single quotes
    for s in [re.sub(r',\s*([}\]])', r'\1', text),
              re.sub(r"(?<!\\)'([^']*)'(?!')", r'"\1"', text)]:
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    return None

# ── Prompt Templates ──

THEME_PROMPT = """Tu es un designer de livres professionnel.

Analyse ce livre et génère un thème CSS complet.

Titre : {title}
Auteur : {author}
Genre : {genre}
Chapitres : {n_chapters}
Extrait : {excerpt}

Réponds UNIQUEMENT avec un objet JSON valide :
{{
  "theme_name": "nom du thème (2-3 mots)",
  "genre": "{genre}",
  "epub": {{
    "body-font": "police_serif_ou_sans, fallback",
    "heading-font": "police_titres, fallback",
    "size": "1em",
    "line-height": 1.5,
    "color": "#hex"
  }},
  "print": {{
    "body-font": '"Times New Roman", serif',
    "heading-font": '"Helvetica", sans-serif',
    "size": "11pt",
    "line-height": 1.3,
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

CLEANER_PROMPT = """Corrige la typographie française de ce texte XHTML :
1. « » au lieu de "" (guillemets)
2. Espace insécable avant ; : ! ?
3. … au lieu de ...
4. — au lieu de --
5. ' au lieu de ' (apostrophe courbe)
6. Pas d'espaces doubles

Retourne UNIQUEMENT le XHTML nettoyé, sans blocs de code.

TEXTE :
{text}"""

ADVISOR_PROMPT = """Analyse ce manuscrit et recommande une mise en page.

Titre : {title}
Genre : {genre}
Chapitres : {n_chapters}
Mots : ~{word_count}
Particularités : {features}

Réponds UNIQUEMENT un objet JSON :
{{
  "recommendation": {{
    "style": "nom du style",
    "rationale": "pourquoi (2-3 phrases)",
    "body_font": "police",
    "heading_font": "police titres",
    "font_size_pt": 11,
    "line_height": 1.3,
    "paper_color": "#hex",
    "text_color": "#hex",
    "accent_color": "#hex",
    "special_treatment": "lettrines, ornements...",
    "target_audience": "public",
    "vibe": "ambiance en 3 mots"
  }}
}}"""

ACCESSIBILITY_PROMPT = """Génère les métadonnées d'accessibilité WCAG pour cet EPUB.

Titre : {title}
Description : Livre sur {genre}, {n_chapters} chapitres.

Réponds UNIQUEMENT un objet JSON :
{{
  "accessibility": {{
    "conformsTo": "WCAG 2.1 AA",
    "summary": "description en français",
    "features": ["structuralNavigation", "displayTransformability"],
    "hazards": ["none"],
    "aria_landmarks": ["landmark1", "landmark2"],
    "language": "fr",
    "certifiedBy": "KLEIA-UP Book"
  }}
}}"""

# ── Public API ──

def generate_theme_llm(title, author, genre, n_chapters, excerpt):
    p = THEME_PROMPT.format(title=title or "", author=author or "",
                            genre=genre or "general",
                            n_chapters=n_chapters, excerpt=(excerpt or "")[:800])
    r = llm_complete(p)
    return extract_json(r) if r else None

def clean_typography(text: str, lang: str = "fr") -> str:
    p = CLEANER_PROMPT.format(text=text[:2000])
    r = llm_complete(p)
    if r and len(r) > 50:
        r = re.sub(r'^```(?:html|xml)?\s*', '', r.strip())
        r = re.sub(r'\s*```$', '', r)
        return r
    return _regex_clean(text, lang)

def _regex_clean(text, lang="fr"):
    text = re.sub(r'"([^"]*)"', r'«\1»', text)
    text = re.sub(r"'([^']*)'", r'’\1’', text)
    text = re.sub(r'\.\.\.', '…', text)
    text = re.sub(r'(?<=[a-zA-Z])--(?=[a-zA-Z])', '—', text)
    if lang == "fr":
        text = re.sub(r'([;:!?])', r' \1', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def design_advisor(title, genre, n_chapters, word_count, features=""):
    p = ADVISOR_PROMPT.format(title=title or "", genre=genre or "",
                              n_chapters=n_chapters, word_count=word_count,
                              features=features or "")
    r = llm_complete(p)
    return extract_json(r) if r else None

def generate_accessibility(title, genre, n_chapters):
    p = ACCESSIBILITY_PROMPT.format(title=title or "", genre=genre or "",
                                    n_chapters=n_chapters)
    r = llm_complete(p)
    return extract_json(r) if r else None
