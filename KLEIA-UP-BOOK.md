# KLEIA-UP Book

> Code name : **KLEIA-UP Book**
> Pipeline open-source de production EPUB + PDF print piloté par IA
> Basé sur Sigil — Dépasse Atticus en ouvert
>
> **Équipe :** JP (Senior Dev) + 3 développeurs
> **Durée :** 8 semaines
> **Livraison :** pipeline batch + interface web + documentation

---

## Semaine 1 — POC de faisabilité (JP seul)

Valider que le concept tient avant d'engager l'équipe.

```
LUN   → Fork Sigil + compilation Qt6 + Python 3.14
       → Plugin engine : script bidon qui tourne
MAR   → python-docx sur un vrai template KDP 6×9
       → Détection des styles : Heading 1, Body Text, First Para
MER   → Mini plugin Sigil : XHTML → bookcontainer → EPUB valide
       → WeasyPrint : XHTML → PDF avec @page basique
JEU   → Prompt LLM → thème CSS → preview dans Sigil
       → Benchmark qualité/temps sur 3 genres
VEN   → Comparaison pixel-diff PDF Pipeline vs Atticus
       → Décision GO/NO-GO
```

**Critères de GO :** EPUB valide + PDF print avec bon trim/gutter — LLM produit du CSS acceptable 2/3 — Pipeline tient 10 livres sans crasher.

---

## Sprints V0 — Pipeline Minimum (Semaines 2-3)

### Sprint 1 — Import + Export (Semaine 2)

```
MOI : Spec template KDP (tous styles), validation nightly
B    : Plugin TemplateKDP-Import (python-docx → XHTML → EPUB)
C    : sigil-cli étendu (fork, mode batch --input --format --parallel)
```

**Livré :** `sigil batch --input *.docx --format epub` sur 5 vrais templates KDP.

### Sprint 2 — PDF Print (Semaine 3)

```
MOI : Spec CSS Paged Media complète, validation pixel-diff vs Atticus
B    : Plugin PrintPDF-Exporter (wrapper WeasyPrint)
D    : CSS @page :left/:right, running heads, string-set, bleed
```

**Livré :** `sigil batch --input *.docx --format epub,pdf` — PDF prêt KDP.

---

## Sprints V1 — Boucle IA (Semaines 4-5)

### Sprint 3 — Bridge LLM + Cleaner (Semaine 4)

```
MOI : Architecture agent IA (router, cache, fallback)
B    : Bridge LLM (OpenAI/Claude/Mistral) + cache Redis/fichier
D    : Prompt engineering (genre→thème, nettoyage typo)
```

**Livré :** `sigil batch --ai-clean --ai-theme auto` nettoie + thématise en < 2 min.

### Sprint 4 — Export Print Final (Semaine 5)

```
MOI : Spec finale Print PDF (tous cas KDP : 6×9, 5.5×8.5, 8.5×11, bleed)
B    : PrintPDF-Exporter v2 (orphelins, dropcaps, notes)
C    : Optimisation perf (mémoire 800p, temps < 3 min)
```

**Livré :** PDF Pipeline = PDF Atticus (documenté).

---

## Sprint V2 — Production (Semaines 6-7)

### Sprint 5 — Batch + Qualité (Semaine 6)

```
MOI : Spec tests comparatifs (50 livres, 5 critères)
B    : Batch multi-worker (pool 8, queue, retry, logging)
D    : Rapport qualité HTML (score/livre, screenshot comparison)
```

### Sprint 6 — Interface Web (Semaine 7)

```
MOI : Spec API web (upload, preview, export, status)
B    : Backend FastAPI (async, WebSocket preview temps réel)
D    : Interface React (upload DOCX, réglages, preview, export)
```

---

## Semaine 8 — Livraison

```
LUN-MAR : Tests finaux, formation utilisateur (1h vidéo + doc PDF)
MER-JEU : Recette client, ajustements, bug fixing
VEN     : Livraison finale, repo GitHub, docs, SLA hotfix 48h
```

---

## Équipe

| Rôle | Profil | Missions |
|---|---|---|
| **JP (Senior Dev)** | Coordination + validation | Spec, POC, review nightly, décisions |
| **B — Python/Backend** | Développeur | Plugins Sigil, API, batch, WeasyPrint |
| **C — C++/Qt** | Développeur | sigil-cli, intégration plugin engine |
| **D — Frontend/Design** | Développeur | CSS Paged Media, thèmes, interface web |

Pas de chef de projet, pas d'ops.

---

## Ce qui est exclus

- ❌ Pas de rewriting de Sigil (API plugin seulement)
- ❌ Pas de base de données (tout fichier)
- ❌ Pas de cloud propriétaire (LLM au choix du client)
- ❌ Pas de marketplace plugins
- ❌ Pas de dépendance à l'IA (fallback heuristique toujours là)

---

## Références

- **Analyse complète :** `ANALYSIS.md`
- **Architecture technique :** `architecture/ARCHITECTURE.md`
- **Pipeline composants :** `pipeline/COMPONENTS.md`
- **Inventaire plugins :** `plugins/INVENTORY.md`
- **Stratégie IA :** `ai-integration/STRATEGY.md`
- **Scénarios d'usage :** `ai-integration/SCENARIOS.md`
- **Repo GitHub :** https://github.com/JPnirrep/sigil-ai-pipeline
- **Ontologie neurosymbolique :** `ontology/book-ontology.ttl`
- **Moteur SHACL :** `ai-integration/ontology_engine.py`
- **Wrapper agent :** `ai-integration/neuro_symbolic_agent.py`
- **Plugin Sigil :** `plugins/sigil_ai_ontology.py`
