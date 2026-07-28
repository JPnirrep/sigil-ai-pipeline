# Analyse Sigil-Ebook : Dépasser Atticus par l'IA

> Analyse complète — Juillet 2026
> Pipeline Print + Digital, Open Source, Piloté par IA

---

## 1. État des lieux : L'écosystème Sigil

### 1.1 L'organisation GitHub (17 repos)

| Repo | Stars | Langage | Rôle |
|---|---|---|---|
| **Sigil** | 6 892 | C++ (Qt6) | Éditeur EPUB multi-plateforme |
| **PageEdit** | 305 | C++ (Qt6) | Éditeur visuel WYSIWYG XHTML |
| **sigil-user-guide** | 127 | HTML | Documentation utilisateur |
| **plugin-api-guide** | 1 | HTML | Guide API pour développeurs de plugins |
| **sigil-ebook.github.io** | — | HTML | Site vitrine |
| **EpubJSReader** | 4 | Python/JS | Lecteur EPUB intégré dans Sigil |
| **cssparser** | — | C++ | Parseur CSS (archivé, remplacé par Lexbor) |
| **sigil-icon-themes** | — | — | Thèmes d'icônes |
| **FlightCrew** | — | C++ | Validateur EPUB (indépendant) |

**Poids du projet :** ~6 900 étoiles, ~620 forks, ~60 contributeurs, développement actif (dernière version : Sigil 2.8.1, Qt6 + Python 3.14 embarqué).

### 1.2 Architecture technique de Sigil

```
┌─────────────────────────────────────────────────┐
│                   Sigil (C++/Qt6)                │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Code View  │  │  Preview │  │  PageEdit   │ │
│  │  (WebEngine)│  │(WebEngine)│  │(WYSIWYG Vis)│ │
│  └──────┬──────┘  └────┬─────┘  └─────┬──────┘ │
│         │              │              │         │
│  ┌──────┴──────────────┴──────────────┴──────┐ │
│  │        Python 3.14 Plugin Engine           │ │
│  │  ┌─────────────┐ ┌──────────────┐         │ │
│  │  │bookcontainer │ │sigil_bs4 (BS4)│         │ │
│  │  └─────────────┘ └──────────────┘         │ │
│  └───────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │  Lexbor CSS3 Parser + Gumbo HTML5 Parser   │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │  Hunspell, PCRE2, MiniZip, MathJax, jQuery │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 1.3 Forces de Sigil face à Atticus

| Critère | Atticus ($147) | Sigil (Gratuit) | Verdict |
|---|---|---|---|
| **Prix** | $147 one-time | **Gratuit (GPLv3)** | Sigil ++ |
| **Multi-plateforme** | Browser (Web) | **Desktop natif** (Win/Mac/Linux) | Égal |
| **Code source** | Propriétaire | **Open Source** | Sigil ++ |
| **Personnalisation CSS** | Limitée au constructeur de thèmes | **Totale** (éditeur CSS + preview temps réel) | Sigil ++ |
| **Plugins** | Aucun | **~50+ plugins Python** | Sigil ++ |
| **EPUB 3** | Oui | **Oui, validation FlightCrew incluse** | Égal |
| **Accessibilité** | Basique | **Plugin Access-Aide + WCAG** | Sigil ++ |
| **Format Kindle (KPF)** | Oui (export direct) | **Import/Export via KindleImport plugin** | Égal |
| **Print PDF** | Oui (natif) | **Non (gap critique)** | Atticus ++ |
| **WYSIWYG** | Oui (natif browser) | Oui (PageEdit séparé) | Égal |
| **Cloud sync** | Oui | Non | Atticus + |
| **Templates KDP** | Intégrés | **À construire** | Atticus ++ |
| **Export DOCX** | Non (lock-in partiel) | **Oui (via plugin Calibre)** | Sigil + |

---

## 2. Le Gap Critique : Print PDF

### 2.1 Le problème

Sigil ne produit **que des EPUB**. Il n'a pas de pipeline de génération PDF imprimable avec :
- Marges de reliure (gutter) spécifiques au POD
- En-têtes alternés recto/verso (running heads)
- Numéros de page
- Format de découpe précis (trim size 5×8, 6×9, etc.)
- Gestion du bleed (débordement)
- Orphelins/veufs controlés

### 2.2 La solution : CSS Paged Media

C'est la spécification W3C exactement conçue pour ça. Deux implémentations open-source majeures :

| Outil | Langage | Type | CSS Paged Media | Force |
|---|---|---|---|---|
| **Paged.js** | JavaScript | Bibliothèque navigateur | ✅ Excellent | Rend visuel temps réel |
| **WeasyPrint** | Python | Utilitaire CLI | ✅ Très bon (sauf JS) | S'intègre au pipeline Python Sigil |

**Architecture de la conversion EPUB → Print PDF :**

```
EPUB (XHTML + CSS)
    │
    ▼
Extraction des XHTML + CSS sémantiques
    │
    ▼
Injection du CSS Paged Media (trim, margins, running elements)
    │
    ├── Paged.js → Rendu navigateur → Export manuel PDF
    │         (usage éditeur, prévisualisation)
    │
    └── WeasyPrint → PDF final automatisé
              (usage pipeline, batch)
```

---

## 3. L'Écosystème des Plugins (Inventaire complet)

### 3.1 Plugins officiels/maintenus

| Plugin | Auteur | Stars | Utilité |
|---|---|---|---|
| **ePub3-itizer** | kevinhendricks | 84 ⭐ | Convertit EPUB2 → EPUB3 valide |
| **Access-Aide** | kevinhendricks | 23 ⭐ | Génère métadonnées WCAG + aria, sémantique accessible |
| **DOCXImport** | dougmassay | 59 ⭐ | Import DOCX → EPUB (critique pour templates KDP) |
| **KindleImport** | dougmassay | — | Convertit KFX/MOBI → EPUB |
| **EpubJSReader** | Sigil-Ebook | 4 ⭐ | Lecteur intégré FuturePress |

### 3.2 Plugins communautaires notables

| Plugin | Fonction | Utilité pipeline |
|---|---|---|
| **FlightCrew** | Validation EPUB exhaustive | Contrôle qualité automatisé |
| **EpubCheck** | Validation IDPF | Conformité spec EPUB |
| **TagMechanic** | Nettoyage/normalisation HTML | Préparation template KDP |
| **Baka-Cleaner** | Nettoyage EPUB | Post-traitement |
| **Baka-Img** | Optimisation images | Compression batch |
| **Sigil-Clip-Importer** | Import clips CSS/HTML snippets | Standardisation |
| **Auto-TOC** | Génération TOC | Automatisation front/back matter |
| **MagicSearch** | Recherche regex cross-fichiers | Refactoring |
| **Report** | Statistiques livre (mots, structure) | Métriques qualité |
| **ConvertEncoding** | Conversion encodage fichier | Normalisation |

### 3.3 Le plugin engine Sigil en détail

```
Plugin Types ─────────────────────────────────
│
├── Input Plugin   → Import (DOCX, EPUB, MOBI...)
├── Output Plugin  → Export transformé (EPUB3, KPF...)
└── Edit Plugin    → Opère sur l'EPUB ouvert (nettoyage, validation...)

API disponible ──────────────────────────────────
│
├── bookcontainer.py    → Manipulation EPUB complète
│   ├── Text/Html IO    → Lire/écrire fichiers XHTML
│   ├── Metadata        → OPF metadata editing
│   ├── Manifest        → Gestion fichiers/ressources
│   ├── Spine           → Ordre de lecture
│   ├── TOC / Nav       → Table des matières
│   └── CSS management  → Édition des feuilles de style
│
├── sigil_bs4           → BeautifulSoup 4 modifié (compatible Python 3.14)
│   ├── Parse XHTML     → DOM navigation/édition
│   └── CSS selector    → Sélection par sélecteurs CSS
│
├── sigil_gumtree       → Gumbo-parser wrapper
│   └── HTML5 parsing   → Parseur tolérant
│
├── sigil_css_parser    → Lexbor CSS3 parser
│   └── CSSOM access    → Arbre CSS complet
│
└── Qt WebEngine API    → Preview, rendering, screenshots
```

---

## 4. Pilotage IA : Architecture et Stratégie

### 4.1 État de l'art

- **sigil-cli** (JingMatrix) : Preuve de concept — lance un script plugin Sigil depuis le terminal en extrayant l'EPUB, exécutant le plugin Python et rempaquetant
- **Aucune API REST/HTTP** : Sigil est une app desktop Qt, pas un serveur
- **Aucune CLI officielle** : Pas de `sigil --batch --convert`
- **Plugin engine Python** : C'est la porte d'entrée pour l'IA

### 4.2 Architecture proposée

```
┌─ Utilisateur ───────────────────────────────┐
│  │                                            │
│  ├── Interface graphique (Qt6 desktop)         │
│  ├── Console (python shell)                   │
│  └── Web UI (Flask/FastAPI locale)            │
└─────────────┬────────────────────────────────┘
              │
              ▼
┌─ Agent IA Orchestrateur ────────────────────┐
│  │  Python 3.14 (embarqué dans Sigil          │
│  │  OU externe avec sigil-cli bridge)         │
│  │                                            │
│  │  ┌────────────────────────────────────┐   │
│  │  │  LLM Router                        │   │
│  │  │  ├── GPT-4 / Claude / Mistral      │   │
│  │  │  ├── Décisions stylistiques         │   │
│  │  │  ├── Génération CSS themes         │   │
│  │  │  └── Validation sémantique          │   │
│  │  └────────────────────────────────────┘   │
│  └───────────────────────────────────────────┘
              │
              ▼
┌─ Pipeline Édition ──────────────────────────┐
│                                              │
│  [PHASE 1] IMPORT TEMPLATE KDP               │
│  ┌────────────────────────────────────┐      │
│  │  DOCX → python-docx → XHTML+CSS    │      │
│  │  ↓                                  │      │
│  │  Detect named styles (Heading 1,    │      │
│  │  Body Text, First Paragraph, etc.)  │      │
│  │  ↓                                  │      │
│  │  Map to semantic EPUB3 structure    │      │
│  └────────────────────────────────────┘      │
│                                              │
│  [PHASE 2] ÉDITION IA                       │
│  ┌────────────────────────────────────┐      │
│  │  Content cleaning (typographie)     │      │
│  │  CSS generation (theme IA)          │      │
│  │  Metadata/accessibility injection   │      │
│  │  Image optimization                  │      │
│  │  Cross-reference validation         │      │
│  └────────────────────────────────────┘      │
│                                              │
│  [PHASE 3] EXPORT MULTI-FORMAT              │
│  ┌────────────────────────────────────┐      │
│  │  Sigil natif : EPUB3 ✓             │      │
│  │  ├── Reflowable (standard)         │      │
│  │  └── Fixed-layout (si nécessaire)  │      │
│  │  ↓                                  │      │
│  │  CSS Paged Media Pipeline : PDF ✓   │      │
│  │  ├── WeasyPrint auto (CLI batch)    │      │
│  │  ├── Paged.js (visual preview)      │      │
│  │  ├── Trim size from template        │      │
│  │  ├── Gutter/binding margins         │      │
│  │  ├── Running heads A/B              │      │
│  │  ├── Page numbers + front matter    │      │
│  │  └── Bleed handling                 │      │
│  └────────────────────────────────────┘      │
└──────────────────────────────────────────────┘
```

### 4.3 Les plugins IA à créer (7 gaps critiques)

| Plugin IA | Fonction | Base technique | Priorité |
|---|---|---|---|
| **TemplateKDP-Import** | Parse DOCX KDP → EPUB sémantique structuré | python-docx + sigil_bs4 | 🔴 P0 |
| **AI-Theme-Generator** | Génère CSS theme complet (couleurs, typos, espacement) | LLM + CSS template engine | 🔴 P0 |
| **AI-Content-Cleaner** | Nettoie typographie, guillemets, espaces insécables | LLM + regex intelligents | 🔴 P0 |
| **AI-Design-Advisor** | Suggère mises en page selon genre (roman, essai, technique) | LLM + base de patterns | 🟡 P1 |
| **PrintPDF-Exporter** | Export EPUB → Print PDF avec CSS Paged Media | WeasyPrint wrapper plugin | 🔴 P0 |
| **AI-Accessibility** | Génère métadonnées WCAG, landmarks, aria automatiquement | LLM + Access-Aide base | 🟡 P1 |
| **AI-Translation-Bridge** | Traduction et ré-import de contenu multilingue | LLM + XHTML fragment patching | 🟢 P2 |

### 4.4 Scénarios d'utilisation

#### Scénario A : Pipeline Automatique Complet

```
Input: DOCX template KDP (6×9, avec bleed)
    │
    ├── 1. TemplateKDP-Import parse les styles
    │    ├── Mapping: "Heading 1" → "h1.chapter-title" + page-break
    │    ├── Mapping: "Body Text" → "p.body-text" + indent
    │    ├── Mapping: "First Paragraph" → "p.first-para" (no indent, dropcap)
    │    └── Mapping: "Normal" → "p.body-text"
    │
    ├── 2. AI-Content-Cleaner (LLM)
    │    ├── Remplace "..." par "…" (ellipse unifiée)
    │    ├── Remplace "--" par "—" (tiret cadratin)
    │    ├── Smart quotes (guillemets français « » si besoin)
    │    └── Espaces insécables avant ;:!?
    │
    ├── 3. AI-Theme-Generator (LLM)
    │    ├── Analyse le genre → proposition palette
    │    ├── Suggère police (serif print, sans-serif digital)
    │    ├── Calcule line-height, margins, espaces
    │    └── Génère CSS complet (EPUB + Print)
    │
    ├── 4. Export EPUB 3 (natif Sigil, validé)
    │
    └── 5. PrintPDF-Exporter (WeasyPrint)
         ├── Charge trim size du template
         ├── Applique CSS @page :first, :left, :right
         ├── Génère running heads
         ├── Gère les blanks (recto vierge)
         └── Sortie: PDF prêt KDP
```

**Temps estimé :** 3-5 minutes par livre standard (200-400 pages)

#### Scénario B : Assistant IA Interactif

```
┌─ Dialogue IA ──────────────────────────────────┐
│                                                  │
│  Auteur : "Je veux un thème sombre élégant,     │
│            police serif, marges confortables"    │
│                                                  │
│  IA :    → Génère 3 variantes CSS               │
│         → Les prévisualise dans le Preview Sigil │
│         → Ajuste selon feedback                  │
│                                                  │
│  Auteur : "Plus d'espace entre les chapitres,    │
│            et des lettrines pour les 5 premiers" │
│                                                  │
│  IA :    → Modifie CSS @page:chapter             │
│         → Injecte CSS dropcap + ::first-letter   │
│         → Re-prévisualise                        │
│                                                  │
└──────────────────────────────────────────────────┘
```

#### Scénario C : Batch Production Multi-Titres

```
📚 Catalogue 50 livres → Pipeline automatisé

Input: 50× DOCX + metadata JSON
    │
    ├── Paralélise sur N workers
    ├── Chaque job:
    │   ├── Détection template auto
    │   ├── Génération theme cohérent série
    │   ├── Production EPUB + PDF
    │   └── Validation + rapport qualité
    │
    └── Output: 50 EPUB + 50 PDF prêts déploiement
```

**Temps estimé :** 30-45 minutes pour 50 livres

---

## 5. Comparaison Finale : Notre Pipeline vs Atticus

| Critère | Atticus | Pipeline Sigil + IA | Avantage |
|---|---|---|---|
| **Prix licence** | $147 (à vie, mais limité à un utilisateur) | **$0** (GPLv3) | Sigil |
| **Print PDF** | ✅ Oui, templates intégrés | ✅ Oui (via CSS Paged Media) | Égal |
| **EPUB reflowable** | ✅ Oui | ✅ Oui (natif, validé) | Sigil (validation incluse) |
| **Personnalisation CSS** | Limitée (Custom Theme Builder) | **Totale** (CSS + médias queries) | Sigil |
| **Plugins** | Aucun | **50+** et extensible Python | Sigil |
| **IA intégrée** | Non | **Oui, agent LLM orchestrateur** | Sigil |
| **Accessibilité** | Basique | **WCAG 2.0 AA+ via Access-Aide + IA** | Sigil |
| **Batch processing** | Manuel (un par un) | **Automated via pipeline CLI** | Sigil |
| **Contrôle version** | Cloud fermé | **Git** (fichiers XHTML texte) | Sigil |
| **Collaboration** | Cloud partagé | **Git + PRs** (développeurs) | Sigil |
| **Templates KDP** | ✅ Intégrés | ✅ Import template DOCX | Égal |
| **Ouverture / Pérennité** | Propriétaire, risque de fermeture | **Open Source, communauté active** | Sigil |
| **KDP Native PDF** | Oui (print ready) | Oui (via WeasyPrint) | Égal |
| **Bleed handling** | Oui | **Oui, paramétrable en CSS** | Égal |

---

## 6. Feuille de Route d'Implémentation

### Phase 1 — Fondations (4-6 semaines)

- [ ] **P0** — Fork Sigil avec le plugin engine Python comme porte d'entrée
- [ ] **P0** — Plugin `TemplateKDP-Import` : parse DOCX KDP → EPUB structuré
- [ ] **P0** — Plugin `PrintPDF-Exporter` : wrapper WeasyPrint pour export PDF
- [ ] **P0** — Création du `sigil-cli` étendu (batch mode, pipeline mode)
- [ ] **P1** — Validation : EPUB + PDF identiques à ce que produit Atticus

### Phase 2 — Intelligence (4-6 semaines)

- [ ] **P0** — Plugin `AI-Theme-Generator` : génération CSS par LLM
- [ ] **P0** — Plugin `AI-Content-Cleaner` : typographie + nettoyage
- [ ] **P1** — Bridge LLM (OpenAI / Claude / Mistral API)
- [ ] **P1** — Template matching auto : détecter quel template KDP est utilisé

### Phase 3 — Scale (4-6 semaines)

- [ ] **P1** — Pipeline batch multi-titres
- [ ] **P2** — Interface web locale (Flask) pour pilotage IA sans GUI Sigil
- [ ] **P2** — Git integration (versioning des sources XHTML)
- [ ] **P2** — Plugins marketplace / registry pour distribution

---

## 7. Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| WeasyPrint ne gère pas tous les cas de CSS Paged Media | Moyenne | Élevé | Fallback Paged.js (browser) + tests comparatifs |
| DOCX KDP templates changent de structure | Faible | Moyen | Mapping configurable (YAML) + tests de régression |
| Verrouillage Amazon sur KPF | Faible | Faible | Notre pipeline peut ignorer KPF, le PDF est accepté directement |
| Performance des LLM trop lente en batch | Moyenne | Moyen | Cache de thèmes, paralélisation, fallback sur règles heuristiques |
| La communauté Sigil rejette les changements | Faible | Élevé | Distribution via plugins externes (pas de fork hostile) |
| Qualité du PDF print inférieure à Atticus | Faible | Élevé | Tests comparatifs automatisés pixel-perfect |

---

## 8. Conclusion

**Atticus est surpassable sur tous les plans** sauf le confort WYSIWYG immédiat — mais PageEdit + Preview Sigil comblent ce gap.

La différence décisive est l'**ouverture** : Sigil offre un contrôle total du pipeline, une API Python extensible, et 50+ plugins existants. En ajoutant :
1. L'import des templates KDP (DOCX → sémantique EPUB)
2. La génération PDF print via CSS Paged Media (WeasyPrint/Paged.js)
3. Un orchestrateur IA pour le design, le nettoyage et la validation

...on obtient un outil **strictement plus puissant qu'Atticus, gratuit, open-source, et pilotable par IA**.

Le coût ? 3-4 mois de développement, un investissement en ingénierie qu'Atticus ne peut pas rattraper car il est architecturé autour d'un modèle fermé.

**Le moment est bon :** Sigil 2.8+ est stable avec Qt6 + Python 3.14. Le CSS Paged Media est une spécification mature. Les LLM sont suffisamment fiables pour les décisions stylistiques. L'écosystème open-source de l'édition n'attend que ça.
