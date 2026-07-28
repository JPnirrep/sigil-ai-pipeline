# Stratégie d'Intégration IA

## 1. Architecture de l'Agent IA

### Niveaux d'intégration

```
NIVEAU 1 — Plugin IA intégré (Python dans Sigil)
├── S'exécute dans le processus Sigil
├── Accès direct à bookcontainer + sigil_bs4
├── Communication LLM via HTTP (API externe)
├── Usage : nettoyage, génération CSS, validation
├── Latence : faible (appels API parallélisés)
└── Validation ontologique avant chaque action
       (SHACL + règles programmatiques)

NIVEAU 2 — Agent externe (Processus séparé)
├── S'exécute dans son propre process Python
├── Communique avec Sigil via sigil-cli
├── Possède sa propre mémoire/état
├── Usage : orchestration multi-livre, décisions complexes
├── Latence : moyenne (I/O fichiers)
└── Validation ontologique (ontologie externe)

NIVEAU 3 — Service web (API REST)
├── Serveur FastAPI/Flask local
├── Interface web pour « designer IA »
├── Usage : mode interactif, prévisualisation, feedback
├── Latence : plus élevée (serveur web + LLM)
└── Validation ontologique (via NeuroSymbolicAgent)
```

### Stack LLM

| Modèle | Rôle | Coût | Qualité |
|---|---|---|---|
| **Claude 4** / **GPT-4** | Décisions stylistiques complexes, thèmes | €€€ | Excellente |
| **Mistral Large** | Génération CSS, nettoyage typo | €€ | Très bonne |
| **DeepSeek V4** | Analyses rapides, fallback | € | Bonne |
| **Llama 3 (local)** | Usage hors-ligne, données sensibles | Gratuit | Correcte |

### 1.5 Couche de Validation Ontologique (NEUVE)

Chaque appel LLM est enrobé par `NeuroSymbolicAgent` :

```
LLM → proposition → OntologyEngine → valide → appliquer
                                    → invalide → feedback → LLM re-génère
                                                         → fallback
```

Voir `../ontology/book-ontology.ttl` pour le schéma complet
et `../ai-integration/ontology_engine.py` pour l'implémentation.

## 2. Prompts et Templates LLM

### Template : Génération de Thème CSS

```
Tu es un designer de livres spécialisé dans la mise en page éditoriale.
Genre du livre : {genre}
Public cible : {audience}
Format : {format} (print / ebook)
Préférences utilisateur : {preferences}

Génère un thème CSS complet, valide, avec :
1. Polices (body, headings) adaptées au genre
2. Palette de couleurs (texte, fond, accents)
3. Espacements (line-height, margins, padding)
4. Traitement des chapitres (dropcaps, ornements, page-break)
5. Version EPUB (reflowable) + version Print (paginée)
6. Variables CSS pour personnalisation facile

Format de sortie : JSON structuré avec embedded CSS.
```

### Template : Nettoyage Typographique

```
Nettoie ce texte XHTML selon les règles typographiques françaises :
1. Guillemets français « » (pas de "")
2. Espaces insécables avant ; : ! ?
3. Ellipses unifiées … (pas trois points)
4. Tirets cadratins — (pas --)
5. Apostrophes courbes ' (pas ')
6. Ligatures automatiques (fi, fl, ff, ffi, ffl)
7. Pas d'espaces doubles

Règles spécifiques au genre {genre} :
- {règles additionnelles}

Réponds uniquement le XHTML nettoyé, sans commentaires.
```

### Template : Suggestions Design

```
Analyse ce manuscrit et suggère 3 mises en page possibles :

Structure détectée :
- Nombre de chapitres : {n_chapters}
- Présence de : {features} (images, tableaux, notes, citations)
- Genre : {genre}
- Longueur : {word_count} mots

Pour chaque proposition, donne :
1. Nom du style
2. Police body + heading
3. Palette couleurs
4. Traitement particulier (lettrines, ornements, etc)
5. Ambiance / public visé
6. Pourquoi ce choix est pertinent
```

## 3. Cache et Performance

### Stratégie de Cache

```yaml
cache:
  themes:
    ttl: 7 jours
    key: genre + audience + format
    stock: 200+ thèmes pré-générés par genre
  css_patterns:
    ttl: permanent
    key: pattern_hash
    stock: bibliothèque de motifs CSS réutilisables
  typo_rules:
    ttl: permanent
    stock: règles par langue (fr, en, de, es, it)
```

### Pipeline de Traitement Parallèle

Pour le batch multi-livres :

```
Worker 1: [Livre A] Import → Nettoyage → Thème → Export
Worker 2: [Livre B] Import → Nettoyage → Thème → Export
Worker 3: [Livre C] Import → Nettoyage → Thème → Export
...
```

Chaque worker est un processus Python indépendant. Le goulot d'étranglement est le LLM — mitigé par :
- Cache de thèmes (hit ≥ 60%)
- Parallélisation des appels LLM (asyncio)
- Fallback heuristique si LLM saturé

## 4. Scénarios d'Échec

| Panne | Comportement | Récupération |
|---|---|---|
| LLM indisponible | Fallback heuristique (règles CSS prédéfinies) | Reprise automatique |
| WeasyPrint échoue | Fallback Paged.js (rendu browser) | Rapport d'erreur |
| DOCX mal formé | Extraction partielle + rapport warning | Correction manuelle puis reprise |
| Plugin Sigil crashe | Isolation process + redémarrage | État sauvegardé (checkpoint) |
| **Validation ontologique bloquante** | **Boucle feedback LLM (N max) → fallback** | **Rapport de dégradation** |
| **Structure détectée supprimée** | **Rejet immédiat (scan diff avant/après)** | **Aucun fallback — revue manuelle** |

## 5. Roadmap Technique

### Sprint 0 (1 semaine) — Fondation Ontologique
- [ ] Définir ontologie RDFS/OWL (BookContent, PublishingConstraints, PipelinePhases)
- [ ] Implémenter OntologyEngine (pySHACL + rdflib)
- [ ] Implémenter NeuroSymbolicAgent (wrapper LLM + validation)
- [ ] Plugin Sigil ValidateOntology
- [ ] Tests unitaires de validation

### Sprint 1 (2 semaines) — Bridge
- [ ] Fork sigil-cli avec API batch
- [ ] Plugin TemplateKDP-Import v0.1 (styles de base)
- [ ] Wrapper Python pour appels LLM
- [ ] Export EPUB valide

### Sprint 2 (2 semaines) — Print
- [ ] CSS Paged Media base template
- [ ] Plugin PrintPDF-Exporter v0.1 (WeasyPrint)
- [ ] Mapping marges KDP → CSS @page
- [ ] Export PDF valide KDP

### Sprint 3 (2 semaines) — IA
- [ ] AI-Theme-Generator v0.1 (genre détection)
- [ ] AI-Content-Cleaner v0.1 (français)
- [ ] Cache de thèmes
- [ ] Validation comparative EPUB/PDF

### Sprint 4 (2 semaines) — Polish
- [ ] Batch processing parallèle
- [ ] Interface web basique (Flask)
- [ ] Documentation
- [ ] Tests comparatifs Atticus vs Pipeline
