# Sigil AI Pipeline

> Pipeline open-source de production de livres (EPUB + PDF Print) piloté par IA, basé sur Sigil.
> Dépasser Atticus en ouvert.

## Pourquoi

**Atticus** ($147) est le standard actuel pour les auteurs auto-édités : templates KDP, export EPUB + PDF print. Mais c'est un logiciel propriétaire, sans plugins, sans API, sans IA.

**Sigil** (6 900 ⭐, GPLv3) est un éditeur EPUB open-source mature avec 50+ plugins Python. Il lui manque deux choses :
1. L'export PDF print (avec pagination, running heads, gutter, bleed)
2. Le pilotage par IA

Ce projet comble ces deux gaps.

## Architecture

```
Template KDP (DOCX)
    │
    ▼
TemplateKDP-Import plugin ───────────┐
    │  Parse les styles DOCX          │  AI-Theme-Generator
    │  → XHTML + CSS sémantique       │  (LLM → CSS)
    ▼                                 │
Sigil (édition / validation)  ◄───────┘
    │
    ├── Export EPUB 3 (natif)
    │
    └── PrintPDF-Exporter (WeasyPrint + CSS Paged Media)
         → PDF prêt KDP (trim, gutter, running heads, bleed)
```

## Plugins à construire

| Plugin | Rôle | Priorité |
|---|---|---|
| `TemplateKDP-Import` | Parse DOCX KDP → EPUB sémantique | P0 |
| `PrintPDF-Exporter` | Export PDF print via WeasyPrint | P0 |
| `AI-Theme-Generator` | Génération CSS thème par LLM | P0 |
| `AI-Content-Cleaner` | Typographie intelligente | P0 |
| `AI-Design-Advisor` | Suggestions design selon genre | P1 |
| `AI-Accessibility` | Génération WCAG automatique | P2 |

## Stack

- **Base :** Sigil 2.8+ (Qt6, Python 3.14) — [github.com/Sigil-Ebook/Sigil](https://github.com/Sigil-Ebook/Sigil)
- **Plugin API :** Python 3.14, `bookcontainer.py`, `sigil_bs4`
- **PDF Print :** WeasyPrint (CSS Paged Media)
- **Prévisualisation :** Paged.js
- **IA :** Bridge LLM (OpenAI / Claude / Mistral / local)
- **DOCX parsing :** python-docx

## Progression

- [x] Analyse complète de l'écosystème Sigil
- [x] Identification des 7 gaps plugins
- [x] Architecture du pipeline Print + Digital
- [x] 4 scénarios d'usage IA documentés
- [ ] Phase 1 — Fondations (en cours)
- [ ] Phase 2 — Intelligence
- [ ] Phase 3 — Scale

## Licence

GNU General Public License v3.0 — comme Sigil.
