# KLEIA-UP Book

> Pipeline open-source de production de livres (EPUB + PDF Print) piloté par IA, basé sur Sigil.
> Dépasse Atticus en ouvert.
>
> **Code name : KLEIA-UP Book**

## Status

**V0 — Pipeline Minimum** ✅ Livré

## Stack

- **Pipeline :** Python 3, DOCX → XHTML sémantique → EPUB 3 + PDF print
- **PDF Print :** Playwright/Chromium (CSS Paged Media complet : gutter, running heads, bleed, trim)
- **Fallback PDF :** pdfkit/wkhtmltopdf (si Playwright indisponible)
- **Plugin Sigil :** plugin.xml + plugin.py — interface GUI dans Sigil
- **CLI Batch :** `sigil -i "*.docx" -f epub,pdf --json`
- **DOCX parsing :** python-docx (styles KDP : Heading 1, Body Text, Title, etc.)
- **IA :** Bridge LLM (presets par genre + LLM optionnel)

## Architecture

```
DOCX (KDP template)
    │
    ├── CLI batch     ──┐
    ├── Sigil plugin  ──┤
    ├── API Python    ──┤
    │                   ▼
    │           TemplateKDP-Import
    │           (parse styles → XHTML sémantique)
    │                   │
    │                   ▼
    │           AI-Theme-Generator
    │           (genre detection → CSS EPUB + Print)
    │                   │
    │           ┌───────┴───────┐
    │           ▼               ▼
    │       EPUB 3          PDF Print
    │       (valide)        (CSS Paged Media)
```

## V0 Livré

| Composant | Statut | Technologie |
|---|---|---|
| Parser DOCX KDP | ✅ | python-docx, 7+ styles |
| Builder EPUB 3 | ✅ | ZIP + OPF + Nav |
| Builder PDF print | ✅ | Playwright/Chromium (ou WeasyPrint, ou pdfkit) |
| Détection template | ✅ | Trim, marges, bleed depuis DOCX |
| Cartographie genre | ✅ | scifi, fiction, fantasy, nonfiction + presets |
| Génération thème CSS | ✅ | EPUB + Print, par genre |
| Plugin Sigil | ✅ | Interface graphique (tkinter) |
| CLI batch | ✅ | `sigil -i "*.docx" -f epub,pdf --json` |
| Adaptateur TXT | ✅ | TXT → DOCX structuré |
| Espacement paragraphe | ✅ | 0.5em EPUB / 0.3em Print |
| Rapport JSON | ✅ | Timing, erreurs, métriques |

## Roadmap

- **V1 — Boucle IA** : LLM theme gen, content cleaner, accessibility
- **V2 — Production** : Batch multi-worker, Web UI, validation comparative

## Usage

```bash
# CLI Batch
sigil -i "mon_livre.docx" -f epub pdf -o ./dist

# TXT → EPUB + PDF
python adaptateur_txt.py mon_fichier.txt

# Plugin Sigil
# Installer dans Sigil → Plugins → KLEIA-UP Book Pipeline
```

## Docs

- [Analyse complète](ANALYSIS.md)
- [Architecture](architecture/ARCHITECTURE.md)
- [Pipeline](pipeline/COMPONENTS.md)
- [Plugins](plugins/INVENTORY.md)
- [Stratégie IA](ai-integration/STRATEGY.md)
- [Scénarios](ai-integration/SCENARIOS.md)
- [Plan de delivery](KLEIA-UP-BOOK.md)
