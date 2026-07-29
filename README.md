# KLEIA-UP Book

> Pipeline open-source de production de livres (EPUB + PDF Print) piloté par IA, basé sur Sigil.
> Dépasse Atticus en ouvert.
>
> **Code name : KLEIA-UP Book**

## Status

**V0 — Pipeline Minimum** ✅ Livré  
**V0.5 — Éditeur Web** ✅ Livré

## Stack

- **Pipeline :** Python 3, DOCX → XHTML sémantique → EPUB 3 + PDF print
- **PDF Print :** Playwright/Chromium (CSS Paged Media complet : gutter, running heads, bleed, trim)
- **Fallback PDF :** pdfkit/wkhtmltopdf (si Playwright indisponible)
- **Plugin Sigil :** plugin.xml + plugin.py — interface GUI dans Sigil
- **CLI Batch :** `sigil -i "*.docx" -f epub,pdf --json`
- **DOCX parsing :** python-docx (styles KDP : Heading 1, Body Text, Title, etc.)
- **IA :** Bridge LLM (presets par genre + LLM optionnel)
- **Éditeur Web :** FastAPI + React/Vite + TipTap (WYSIWYG)

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
    │           ┌───────┴───────┐
    │           ▼               ▼
    │       EPUB 3          PDF Print
    │       (valide)        (CSS Paged Media)
    │
    └── Éditeur Web (V0.5)
            │
        FastAPI backend
            │
    ┌───────┴───────┐
    ▼               ▼
React/Vite      TipTap Editor
 (UI)           (WYSIWYG)
```

## V0.5 — Éditeur Web

| Fonction | Statut |
|---|---|
| Import DOCX (KDP template) | ✅ |
| Édition WYSIWYG (TipTap) | ✅ Texte, H1/H2/H3, gras, italique, alignement, blockquote, images |
| Navigation par chapitres | ✅ Ajout/suppression/réordonnancement |
| Panneau style | ✅ Police, taille, interligne, alignement, couleurs (temps réel) |
| Aperçu live (iframe CSS) | ✅ Reflète les réglages du panneau style |
| Export EPUB 3 | ✅ Valide, avec couverture + métadonnées |
| Export PDF print-ready | ✅ Playwright + CSS Paged Media |
| Templates KDP | ✅ 7 formats (6×9, 5.5×8.5, 8.5×11, A4) |
| Aliases auteur | ✅ Registre, sélection en un clic |
| Couverture | ✅ Upload image → intégrée dans l'EPUB |
| Sessions persistantes | ✅ Sauvegarde + restauration automatique |
| Notifications | ✅ Toasts succès/erreur |

## Démarrage rapide

### Web Editor

```bash
# Terminal 1 — Backend (FastAPI)
python -m uvicorn editor.api.main:app --port 8589 --host 0.0.0.0

# Terminal 2 — Frontend (Vite)
cd editor/frontend
npx vite --port 5173
```

Puis ouvrir http://localhost:5173

### Windows

Double-cliquer sur `start-editor.bat`

### CLI Batch Pipeline

```bash
sigil -i "mon_livre.docx" -f epub pdf -o ./dist
```

### Plugin Sigil

Installer dans Sigil → Plugins → KLEIA-UP Book Pipeline

## Structures des dossiers

```
├── editor/                    ← Éditeur web
│   ├── api/
│   │   ├── main.py            ← FastAPI (routes, export EPUB/PDF)
│   │   ├── models.py          ← Pydantic models
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.tsx        ← Layout, landing, projet, éditeur
│   │   │   ├── api.ts         ← Client API
│   │   │   ├── types.ts       ← Types TypeScript
│   │   │   ├── index.css      ← Design system
│   │   │   └── components/
│   │   │       ├── RichEditor.tsx       ← TipTap
│   │   │       ├── StylePanel.tsx       ← Panneau style (français)
│   │   │       └── ProjectSetupDialog.tsx ← Dialogue création projet
│   │   ├── vite.config.ts
│   │   └── package.json
│   ├── templates/             ← Templates KDP générés
│   └── .data/                 ← Sessions (gitignored)
├── poc/kleia_up_book/         ← Pipeline cœur
│   ├── parser.py              ← DOCX → ParsedBook
│   ├── builder.py             ← EPUB 3 builder
│   ├── pdf_builder.py         ← PDF print builder
│   ├── browser_pdf.py         ← Playwright PDF
│   ├── theme.py               ← Génération CSS
│   ├── validator.py           ← Validation EPUB/PDF
│   └── ai_llm.py              ← Bridge LLM
├── sigil                      ← CLI batch entry point
├── start-editor.bat           ← Démarrage Windows
├── start-editor.sh            ← Démarrage Linux/Mac
└── KLEIA-UP-BOOK.md           ← Plan de delivery
```
