# Pipeline : Composants et Flux

## Pipeline Standard

```
╔══════════════════════════════════════════════════════╗
║                  PHASE 1 : IMPORT                    ║
╠══════════════════════════════════════════════════════╣
║ Entrée : DOCX (template Amazon KDP)                  ║
║                                                      ║
║ 1. python-docx parse le fichier                      ║
║ 2. Extraction des styles nommés                      ║
║ 3. Détection du template (6x9, 5.5x8.5, etc)        ║
║ 4. Conversion en XHTML + CSS via sigil_bs4           ║
║ 5. Split en chapitres (fichiers séparés)            ║
║ 6. Injection métadonnées OPF                         ║
║ 7. Validation structurelle                           ║
║                                                      ║
║ Sortie : EPUB 3 ouvert dans Sigil                    ║
╚══════════════════════════════════════════════════════╝
           │
           ▼
╔══════════════════════════════════════════════════════╗
║               PHASE 2 : ÉDITION IA                   ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║ 1. AI Content Cleaner                                ║
║    ├── Typographie (guillemets, tirets, espaces)     ║
║    ├── Normalisation des variantes Unicode           ║
║    └── Détection et correction erreurs fréquentes    ║
║                                                      ║
║ 2. AI Theme Generator                                ║
║    ├── Analyse du genre (fiction, non-fiction, etc)  ║
║    ├── Génération palette de couleurs                ║
║    ├── Sélection typographique (serif/sans-serif)    ║
║    ├── Calcul des espacements (line-height, margins) ║
║    └── Production CSS EPUB + CSS Print                ║
║                                                      ║
║ 3. AI Accessibility                                  ║
║    ├── Génération landmarks ARIA                     ║
║    ├── Alt texts pour figures                        ║
║    └── Métadonnées WCAG                              ║
║                                                      ║
║ Sortie : EPUB 3 enrichi par IA                        ║
╚══════════════════════════════════════════════════════╝
           │
           ▼
╔══════════════════════════════════════════════════════╗
║              PHASE 3 : EXPORT                        ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║ 3a. Export EPUB                                      ║
║    ├── Validation FlightCrew/EpubCheck                ║
║    └── Empaquetage EPUB 3 final                       ║
║                                                      ║
║ 3b. Export PDF                                        ║
║    ├── Injection CSS Paged Media                      ║
║    ├── WeasyPrint rendering                           ║
║    ├── Contrôle qualité PDF                           ║
║    └── PDF vérifié prêt KDP                          ║
║                                                      ║
║ Sortie : {titre}.epub + {titre}.pdf                   ║
╚══════════════════════════════════════════════════════╝
```

## Composants Détaillés

### 1. TemplateKDP-Import (Plugin Input)

**Fonctionnement :**

```python
class TemplateKDPImport(SigilInputPlugin):
    def run(self, docx_path):
        # 1. Parse DOCX
        doc = Document(docx_path)
        template = self.detect_template(doc)
        # 2. Extract styles
        styles = self.extract_styles(doc, template)
        # 3. Build EPUB structure
        epub = self.build_epub(doc, styles, template)
        # 4. Write via bookcontainer
        self.bk.write(epub)
        return True

    def detect_template(self, doc):
        """Détecte le template KDP par dimensions et styles présents"""
        dims = (doc.sections[0].page_width, doc.sections[0].page_height)
        styles = {s.name for s in doc.styles}
        return match_template(dims, styles)
```

### 2. PrintPDF-Exporter (Plugin Output)

**Architecture :**

```python
class PrintPDFExporter(SigilOutputPlugin):
    def run(self, epub_path):
        # 1. Extract XHTML + CSS from open epub
        content, css = self.extract_content(self.bk)
        # 2. Merge with print-specific CSS
        paged_css = self.generate_paged_css(self.bk)
        combined_css = css + "\n" + paged_css
        # 3. Write temp HTML with Paged Media
        html = self.build_print_html(content, combined_css)
        with tempfile.NamedTemporaryFile(suffix=".html") as f:
            f.write(html)
            # 4. WeasyPrint render
            pdf = subprocess.run([
                "weasyprint", f.name, epub_path.with_suffix(".pdf")
            ])
        return True

    def generate_paged_css(self, bk):
        """Génère le CSS @page à partir des métadonnées EPUB""" """
        template = self.read_template_meta(bk)
        return f"""
        @page {{
            size: {template.trim_width}in {template.trim_height}in;
            margin: {template.margin_top}in {template.margin_outer}in
                     {template.margin_bottom}in {template.margin_inner}in;
            bleed: {template.bleed}in;
        }}
        ...
        """
```

### 3. AI Orchestrator (Processus Externe)

**Architecture asynchrone :**

```python
class AIOrchestrator:
    """Coordonne les appels LLM et les actions Sigil"""

    def __init__(self, llm_client, sigil_client):
        self.llm = llm_client  # OpenAI / Claude / Mistral
        self.sigil = sigil_client  # sigil-cli wrapper
        self.cache = ThemeCache()

    async def process_book(self, docx_path, genre=None, preferences=None):
        """Pipeline complet pour un livre"""
        # Phase 1 — Import
        await self.sigil.execute_plugin("TemplateKDP-Import", docx_path)

        # Phase 2 — IA
        theme = await self.generate_theme(genre, preferences)
        await self.sigil.inject_css(theme.css_epub)
        await self.sigil.execute_plugin("AI-Content-Cleaner")

        # Phase 3 — Export
        epub = await self.sigil.export_epub()
        pdf = await self.sigil.execute_plugin("PrintPDF-Exporter")
        return epub, pdf

    async def generate_theme(self, genre, preferences):
        if cached := self.cache.get(genre, preferences):
            return cached
        prompt = self.build_theme_prompt(genre, preferences)
        llm_response = await self.llm.complete(prompt)
        theme = Theme.parse(llm_response)
        self.cache.set(genre, preferences, theme)
        return theme
```

### 4. sigil-cli (Couche de liaison)

**Commandes prévues :**

```bash
# Pipeline complet batch
sigil batch \
  --input "/books/*.docx" \
  --template "kdp-6x9" \
  --output "/out" \
  --format epub,pdf \
  --ai-theme "elegant-serif" \
  --ai-clean true \
  --parallel 4

# Import seul
sigil import --template kdp-6x9 --docx chapter1.docx

# Export PDF seul (sur EPUB existant)
sigil export-pdf --epub book.epub --print-css print.css --output book.pdf

# Lancement du mode assistant IA
sigil ai-assist --interactive
```

## Métriques de Performance

| Opération | Manuel (Atticus) | Automatisé (Pipeline) | Gain |
|---|---|---|---|
| Import DOCX → EPUB | 15-30 min | 30 sec | ×30 |
| Nettoyage typographique | 20-40 min | 15 sec | ×80 |
| Création thème CSS | 1-2 h | 30 sec (LLM) | ×120 |
| Export PDF print | 5 min | 2 min (rendu) | ×2.5 |
| Contrôle qualité | 10-20 min | 1 min (auto) | ×15 |
| **Livre complet 300p** | **2-4 h** | **3-5 min** | **×40** |
| **Catalogue 50 livres** | **1-2 semaines** | **30-45 min** | **×200** |
