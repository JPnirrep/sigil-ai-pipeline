# Architecture Technique

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌──────┐   ┌──────────────┐   ┌────────────┐   ┌───────────┐  │
│  │ DOCX │──▶│ TemplateKDP  │──▶│    Sigil   │──▶│   EPUB 3  │  │
│  │ KDP  │   │ -Import      │   │  (Core +   │   │ (natif)   │  │
│  │      │   │ sigil_bs4    │   │   Plugins) │   └───────────┘  │
│  └──────┘   │ python-docx  │   └─────┬──────┘                 │
│             └──────────────┘         │                        │
│                                      ▼                        │
│                             ┌────────────────┐                │
│                             │  PrintPDF      │                │
│                             │  -Exporter     │                │
│                             │  (WeasyPrint)  │                │
│                             └───────┬────────┘                │
│                                     ▼                         │
│                             ┌──────────────┐                  │
│                             │  PDF print   │                  │
│                             │  (KDP ready) │                  │
│                             └──────────────┘                  │
│                                                                │
│  ┌─────────────┐   ┌────────────────────────┐                  │
│  │ LLM (API)   │──▶│  AI Orchestrator       │                  │
│  │ Claude/GPT/ │   │  (Python, async)        │                  │
│  │ Mistral     │   │  ┌─────────────────┐   │                  │
│  │             │   │  │ Theme Generator │   │                  │
│  │             │   │  │ Content Cleaner │   │                  │
│  │             │   │  │ Design Advisor  │   │                  │
│  │             │   │  └─────────────────┘   │                  │
│  └─────────────┘   └────────────────────────┘                  │
│                                                                │
└──────────────────────────────────────────────────────────────────┘
```

## Composants

### 1. TemplateKDP-Import (Plugin Input Sigil)

Lit un DOCX Amazon KDP, extrait la structure via `python-docx`, et produit un EPUB sémantique.

**Mapping Styles DOCX → EPUB HTML :**

| Style KDP | Élément HTML | Rôle |
|---|---|---|
| `Heading 1` | `<h1 class="chapter-title">` | Titre de chapitre |
| `Heading 2` | `<h2 class="section-title">` | Section |
| `Body Text` | `<p class="body-text">` | Corps premier niveau |
| `Body Text First Paragraph` | `<p class="first-para">` | Premier § (pas d'indent) |
| `Normal` | `<p class="body-text">` | Corps standard |
| `Image` | `<figure class="image">` | Illustration |
| `Block Quote` | `<blockquote>` | Citation |
| `Title` | `<h1 class="book-title">` | Titre du livre |
| `Subtitle` | `<h2 class="book-subtitle">` | Sous-titre |
| `Author` | `<p class="author">` | Auteur |
| `Copyright Page` | `<section class="copyright">` | Mentions légales |
| `TOC Heading` | `<h1 class="toc-title">` | Titre de la table des matières |
| `Dedication` | `<section class="dedication">` | Dédicace |
| `Epigraph` | `<blockquote class="epigraph">` | Épigraphe |

**Extraction des métadonnées KDP depuis le DOCX :**
- Trim size (détecté via dimensions page)
- Bleed (via marges)
- Marges intérieures
- Polices embarquées

### 2. PrintPDF-Exporter (Plugin Output Sigil)

Convertit l'EPUB ouvert en PDF print-ready via WeasyPrint.

**CSS Paged Media injecté :**

```css
/* Taille de page — détectée depuis le template KDP */
@page {
  size: 6in 9in;
  margin: 0.75in;
  margin-bottom: 0.85in;
  bleed: 0.125in;
}

/* Pages gauche/droite — marges de reliure alternées */
@page :left {
  margin-left: 0.6in;
  margin-right: 0.9in;
  @top-left {
    content: string(book-title);
    font-size: 8pt;
    font-style: italic;
  }
  @bottom-left {
    content: counter(page);
    font-size: 8pt;
  }
}

@page :right {
  margin-left: 0.9in;
  margin-right: 0.6in;
  @top-right {
    content: string(chapter-title);
    font-size: 8pt;
    font-style: italic;
  }
  @bottom-right {
    content: counter(page);
    font-size: 8pt;
  }
}

/* Première page de chapitre — pas d'en-tête */
@page chapter:first {
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-left { content: none; }
  @bottom-right {
    content: counter(page);
    font-size: 8pt;
  }
}

/* Pages blanches volontaires (verso de fin de partie) */
@page blank {
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}

/* Running elements */
h1.chapter-title {
  string-set: chapter-title content(text);
  page: chapter;
  break-before: right;
}
```

### 3. AI Orchestrator (Processus Python externe)

Communique avec Sigil via `sigil-cli` (mode batch) ou plugin engine direct.

**Architecture interne :**

```
AI Orchestrator
├── Config Loader — lit le profil utilisateur (genre, préférences)
├── LLM Router — distribue les appels aux modèles
│   ├── Décisions stylistiques → modèle rapide (flash)
│   └── Génération CSS complexe → modèle lent (pro)
├── Plugin Client — envoie les commandes à Sigil via sigil-cli
├── Cache — évite les appels LLM redondants (CSS patterns)
└── Fallback Engine — règles heuristiques si LLM indisponible
```

### 4. sigil-cli étendu

Fork de JingMatrix/sigil-cli avec :

```
sigil batch --input "*.docx" --template "kdp-6x9" --output ./out/
            --format epub,pdf --ai-theme "elegant-serif"
            --ai-clean true --parallel 4
```

## Formats de données

### Fichier de mapping template (YAML)

```yaml
template:
  name: "KDP 6×9 Novel"
  trim_size: [6, 9]       # inches
  bleed: 0.125            # inches
  margins:
    inside: 0.9
    outside: 0.6
    top: 0.75
    bottom: 0.85
  styles:
    "Heading 1": { tag: "h1", class: "chapter-title", page-break: "right" }
    "Body Text": { tag: "p", class: "body-text", indent: "1.5em" }
    "First Paragraph": { tag: "p", class: "first-para", indent: "0" }
  fonts:
    body: "Georgia, serif"
    heading: "Helvetica, sans-serif"
    size: 11pt
```

### Fichier de thème CSS (sortie LLM)

```json
{
  "theme": {
    "name": "Elegant Serif",
    "genre": ["fiction", "literary"],
    "epub": { "body-font": "Georgia", "heading-font": "Lora" },
    "print": { "body-font": "Garamond", "heading-font": "Helvetica" },
    "colors": { "text": "#1a1a1a", "paper": "#faf8f5", "accent": "#8b4513" },
    "spacing": { "line-height": 1.45, "paragraph-spacing": "0.3em" },
    "typography": {
      "hyphenation": true,
      "ligatures": true,
      "dropcaps": true,
      "quotes": "french"
    }
  }
}
```
