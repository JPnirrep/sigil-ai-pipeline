# KLEIA-UP Book

> Pipeline open-source de production de livres (EPUB + PDF Print) piloté par IA, basé sur Sigil.
> Dépasse Atticus en ouvert.
>
> **Code name : KLEIA-UP Book**

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

## Équipe

| Rôle | Profil |
|---|---|
| JP (Senior Dev) | Coordination, POC, validation |
| Dev Python/Backend | Plugins Sigil, API, batch, WeasyPrint |
| Dev C++/Qt | sigil-cli, intégration plugin engine |
| Dev Frontend/Design | CSS Paged Media, thèmes, interface web |

## Planning

| Phase | Semaines | Livrable |
|---|---|---|
| POC | 1 | Pipeline fonctionnel de bout en bout |
| V0.1 Import | 2 | `sigil batch --format epub` sur 5 DOCX KDP |
| V0.2 PDF | 3 | + `--format pdf` valide vs Atticus |
| V1.1 Bridge IA | 4 | Nettoyage + thème IA automatisés |
| V1.2 Print final | 5 | PDF print finalisé, tous cas KDP |
| V2.1 Batch | 6 | Batch 50 livres, rapports qualité |
| V2.2 Web UI | 7 | Interface web fonctionnelle |
| Livraison | 8 | Docs, formation, recette, hotfix |

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

- **Base :** Sigil 2.8+ (Qt6, Python 3.14)
- **Plugin API :** Python 3.14, `bookcontainer.py`, `sigil_bs4`
- **PDF Print :** WeasyPrint (CSS Paged Media)
- **Prévisualisation :** Paged.js
- **IA :** Bridge LLM (OpenAI / Claude / Mistral / local)
- **DOCX parsing :** python-docx

## Docs

- [Analyse complète](ANALYSIS.md)
- [Architecture](architecture/ARCHITECTURE.md)
- [Pipeline](pipeline/COMPONENTS.md)
- [Plugins](plugins/INVENTORY.md)
- [Stratégie IA](ai-integration/STRATEGY.md)
- [Scénarios](ai-integration/SCENARIOS.md)
- [Plan de delivery](KLEIA-UP-BOOK.md)

## Licence

GNU General Public License v3.0 — comme Sigil.
