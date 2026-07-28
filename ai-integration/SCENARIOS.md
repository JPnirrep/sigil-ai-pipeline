# Scénarios d'Usage et Simulations

## Scénario A : Auteur Individuel — Pipeline Automatique Complet

**Profil :** Auteur auto-édité, manuscrit Word, veut EPUB + PDF KDP.

```
INPUT:  manuscrit.docx (template KDP 6×9)
        preferences.json {
          "genre": "roman",
          "audience": "adulte",
          "style": "classique-elegant"
        }

─────────── TEMPS RÉEL ─────────────────────────

[00:00] > sigil batch --input manuscrit.docx --template kdp-6x9
[00:00] → TemplateKDP-Import : parsing DOCX...
[00:01] → 24 styles nommés détectés
         → Template : KDP 6×9 Novel (bleed: 0.125in)
         → 22 chapitres extraits, 78 432 mots
[00:03] → AI-Content-Cleaner : LLM typographie...
         → 147 corrections appliquées
         → Guillemets: 312 remplacés
         → Tirets: 89 normalisés
         → Espaces insécables: 234 insérés
[00:05] → AI-Theme-Generator : LLM design...
         → Thème "Elegant Serif" généré
         → Police: Garamond (print) / Georgia (epub)
         → Palette: #1a1a1a / #faf8f5 / #8b4513
[00:06] → Export EPUB → validé FlightCrew (0 erreur)
[00:07] → Export PDF → WeasyPrint rendering...
[00:09] → PDF généré : vérifié (trim 6×9, gutter OK)

─────────── RÉSULTAT ───────────────────────────

✓ manuscrit.epub   (324 KB, EPUB 3, validé)
✓ manuscrit.pdf    (2.1 MB, print-ready KDP)
✗ Erreurs: 0   Avertissements: 2 (images > 300 DPI)

Temps total : 9 minutes 23 secondes
```

## Scénario B : Designer IA Interactif

**Profil :** Auteur exigeant, veut contrôler le design fin.

```
USER > sigil ai-assist --interactive
IA   > ✋ Assistant design prêt. Ton livre "Les Oubliés" (SF, 120k mots)

USER > "Je veux un thème sombre, cyberpunk, avec une touche rétro 80s"

IA   > Je génère 3 propositions...

┌─────────────────────────────────────────────┐
│ PROPOSITION 1 : NEON NOIR                    │
│ ├ Police: Orbitron (titres) / IBM Plex Mono │
│ ├ Couleurs: #0a0a0a / #00ff41 / #ff00ff     │
│ ├ Ambiance: Matrix meets Blade Runner        │
│ └ Traitement: chapitres avec bordure néon    │
├─────────────────────────────────────────────┤
│ PROPOSITION 2 : CASSETTE FUTURISTE           │
│ ├ Police: Rajdhani + Source Serif            │
│ ├ Couleurs: #1a1a2e / #e94560 / #0f3460     │
│ ├ Ambiance: Retro-futuriste chill            │
│ └ Traitement: lettrines pixelisées           │
├─────────────────────────────────────────────┤
│ PROPOSITION 3 : INDUSTRIEL SÉVÈRE            │
│ ├ Police: Bebas Neue + Crimson Text          │
│ ├ Couleurs: #2d2d2d / #d4af37 / #8b0000     │
│ ├ Ambiance: Métal froid, luxe brutaliste     │
│ └ Traitement: filets de séparation épais     │
└─────────────────────────────────────────────┘

USER > "Proposition 2, mais avec les couleurs de la 3"

IA   > 🎨 Nouveau thème "Cassette Luxe" créé
     > Appliqué en prévisualisation...
     > [Preview Sigil mis à jour]

USER > "Parfait. Valide et exporte."

IA   >  ✓ EPUB exporté
      >  ✓ PDF print exporté (6×9, 408 pages)
      >  Notes : 52 images > 300 DPI optimisées automatiquement
```

## Scénario C : Studio d'Édition — Batch Production

**Profil :** Micro-édition, 50 titres à produire pour un catalogue.

```
$ sigil batch \
  --input "./catalogue/*.docx" \
  --template "kdp-5.5x8.5" \
  --output "./dist" \
  --format epub,pdf \
  --ai-theme "serie-fantasy" \
  --ai-clean true \
  --parallel 8

═══════════════════════════════════════════
  BATCH : 50 LIVRES
═══════════════════════════════════════════

LOT 1/7 ── 8 workers ─────────────────────
  ✓ Chroniques_de_Veridya      (3m12s)
  ✓ L'Epée_de_Kael             (2m48s)
  ✓ La Prophétie des Ombres    (4m01s) ⚠ images non webp
  ✓ Le Cristal d'Aether        (2m55s)
  ✓ Les Héritiers d'Elara      (3m33s)
  ✓ Le Trône de Corail         (2m41s)
  ✓ La Danse des Dragons       (3m07s)
  ✓ Les Jardins de Saphir      (2m22s)

LOT 2/7 ── 8 workers ─────────────────────
  ...

═══════════════════════════════════════════
RÉSULTATS FINAUX
═══════════════════════════════════════════

✓ 50 EPUB 3 produits   (moy. 2.8 Mo)
✓ 50 PDF print produits (moy. 4.2 Mo)
⚠ 7 livres avec warnings (images, voir rapport)
✗ 1 livre en erreur (DOCX corrompu, fichier isolé)

Temps total : 38 minutes 14 secondes
Temps manuel estimé (Atticus) : ~8-10 jours
Efficacité : ×300

Rapport qualité : dist/rapport-batch-20260728.html
```

## Scénario D : Édition Scolaire — PDF + EPUB Accessible

**Profil :** Manuel scolaire, besoin d'accessibilité WCAG, export pour impression et accessibilité numérique.

```
$ sigil batch \
  --input "mathematiques_6e.docx" \
  --template "kdp-8.5x11" \
  --ai-theme "manuel-scolaire" \
  --ai-accessibility wcag-aa \
  --ai-clean true

═══════════════════════════════════════════
  SPÉCIFIQUE : MANUEL SCOLAIRE
═══════════════════════════════════════════

DÉTECTION AUTOMATIQUE :
  ├ 24 chapitres
  ├ 143 figures (dont 87 équations)
  ├ 56 tableaux
  ├ 312 exercices
  └ 2 index (notions + noms)

TRAITEMENT IA ACCESSIBILITÉ :
  ├ Alt texts générés pour 143 figures
  ├ Descriptions longues pour 87 équations
  ├ Labels ARIA pour 56 tableaux
  ├ Structure landmarks complète
  ├ Ordre de lecture logique vérifié
  └ Métadonnées WCAG 2.1 AA injectées

RÉSULTAT :
  ✓ EPUB 3 accessible   (8.3 Mo)
  ✓ PDF print            (12.1 Mo, 340 pages)
  ✓ Rapport WCAG         (100% critères AA validés)
  ✓ Temps total : 14 minutes
```

## Scénario E : Travail Collaboratif — Git + Revue

**Profil :** Équipe de 3 personnes sur un livre technique.

```
1. DESIGNER > Génère le thème "tech-doc" via IA
            > Applique → commit "theme: initial tech documentation theme"

2. AUTEUR   > Importe DOCX chapitre 12 via TemplateKDP
            > Modifie en Code View → commit "chap12: review and corrections"

3. REVISEUR > Lance AI-Content-Cleaner → commit "typo: batch cleanup"
            > Vérifie diff → approve

4. CI       > GitHub Action : sigil batch → valide EPUB/PDF
            > Génère preview → déploie sur page de test

5. TOUS    > Review la preview → merge

AVANTAGE :
  - Historique complet (git log)
  - Branches par chapitre
  - CI/CD pour validation
  - Retour possible sur n'importe quelle version
```

## Scénario F : Pipeline Temps Réel avec Feedback Loop

**Profil :** Service web où l'utilisateur voit le rendu évoluer en direct.

```
UTILISATEUR                     SERVEUR IA                       SIGIL
    │                              │                               │
    ├─ Upload DOCX ──────────────► │                               │
    │                              ├── TemplateKDP-Import ──────► │
    │                              │◄── EPUB prêt ─────────────────│
    │                              │                               │
    │◄── Preview EPUB ────────────┤                               │
    │                              │                               │
    ├─ "Augmente la taille         │                               │
    │   des marges" ─────────────► │                               │
    │                              ├── Modifie CSS ─────────────► │
    │                              │◄── Mise à jour ──────────────│
    │◄── Preview mise à jour ─────┤                               │
    │                              │                               │
    ├─ "Passe en Garamond" ─────► │                               │
    │                              ├── AI-Theme-Generator ──────► │
    │                              │    "Garamond body,           │
    │                              │     style = élégant,          │
    │                              │     genre = littéraire"       │
    │                              │◄── Nouveau CSS ──────────────│
    │◄── Preview rendue ──────────┤                               │
    │                              │                               │
    ├─ "Export PDF" ─────────────► │                               │
    │                              ├── PrintPDF-Exporter ───────► │
    │◄── PDF prêt ────────────────┤◄── PDF ──────────────────────│
    │                              │                               │
```

## Tableau Comparatif des Scénarios

| Scénario | Public | Volume | Temps/livre | Automation | Complexité |
|---|---|---|---|---|---|
| A — Auteur solo | Individuel | 1 | ~9 min | Élevée | Faible |
| B — Designer interactif | Individuel exigeant | 1 | ~30 min (interactif) | Moyenne | Moyenne |
| C — Studio batch | Équipe | 50 | ~45 sec/livre | Totale | Élevée |
| D — Scolaire accessible | Institution | 1-10 | ~14 min/livre | Très élevée | Très élevée |
| E — Git collaboratif | Équipe | Variable | Temps réel | Partielle | Élevée |
| F — Feedback temps réel | Service web | 1 | Temps réel | Interactive | Maximale |
