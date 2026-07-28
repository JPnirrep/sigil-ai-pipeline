# Inventaire des Plugins Sigil

> Recensement exhaustif de l'écosystème — Juillet 2026

## Plugins Officiels / Maintenus

| Plugin | Auteur | Stars | Type | Utilité pipeline |
|---|---|---|---|---|
| **ePub3-itizer** | kevinhendricks | 84 ⭐ | Output | Convertit EPUB2 → EPUB3 valide |
| **Access-Aide** | kevinhendricks | 23 ⭐ | Edit | Génère métadonnées WCAG + aria |
| **DOCXImport** | dougmassay | 59 ⭐ | Input | Import DOCX → EPUB (base pour TemplateKDP) |
| **KindleImport** | dougmassay | — | Output | Convertisseur MOBI/KFX → EPUB |
| **EpubJSReader** | Sigil-Ebook | 4 ⭐ | Preview | Lecteur EPUB intégré (FuturePress) |

## Plugins Communautaires

| Plugin | Fonction | Repo / Source |
|---|---|---|
| **Sigil Clip Importer** | Import clips CSS/HTML | GitHub communautaire |
| **Baka-Cleaner** | Nettoyage EPUB (XHTML mal formé) | dreamer2908/Sigil-Plugins |
| **Baka-Img** | Optimisation images batch | dreamer2908/Sigil-Plugins |
| **Baka-Captions** | Gestion sous-titres/légendes figures | dreamer2908/Sigil-Plugins |
| **TagMechanic** | Normalisation structurelle HTML | Mobileread forums |
| **EpubCheck** | Validation IDPF EPUB3 | Mobileread forums |
| **FlightCrew** | Validation avancée EPUB | Sigil (bundlé) |
| **MagicSearch** | Regex cross-fichiers | Mobileread forums |
| **Report** | Statistiques livre (mots, fichiers, CSS) | Mobileread forums |
| **Auto-TOC** | Génération nav.xhtml automatique | Mobileread forums |
| **ConvertEncoding** | Normalisation encodage fichiers | Mobileread forums |

## Plugins à Construire (Gaps Atticus)

| Plugin | Rôle | API | Priorité |
|---|---|---|---|
| **TemplateKDP-Import** | Parse DOCX Amazon KDP → EPUB sémantique | python-docx + sigil_bs4 | P0 |
| **PrintPDF-Exporter** | Export EPUB → PDF print prêt KDP | WeasyPrint + CSS Paged Media | P0 |
| **AI-Theme-Generator** | Génération CSS thème par IA | LLM + CSS template engine | P0 |
| **AI-Content-Cleaner** | Nettoyage typographique intelligent | LLM + regex typo | P0 |
| **AI-Design-Advisor** | Suggestions design selon genre + public | LLM + base de patterns | P1 |
| **AI-Accessibility** | Génération WCAG + aria automatique | LLM + Access-Aide base | P2 |
| **AI-Translation-Bridge** | Traduction XHTML fragmentaire | LLM + DOM patching | P2 |

## Analyse des Plugins Existants (Utilité)

### DOCXImport (base TemplateKDP)

**Forces :** Convertit DOCX en EPUB fonctionnel, garde une structure basique
**Limites :**
- Ne détecte PAS les styles nommés spécifiques KDP
- Pas de mapping template configurable
- Pas de gestion des métadonnées KDP (trim, bleed)
- Sortie = un seul fichier XHTML, pas de split par chapitre

**Stratégie :** Forker ou enrichir plutôt que réécrire

### ePub3-itizer (base validation EPUB3)

**Utilité :** Convertit un EPUB2 produit par DOCXImport en EPUB3 strict
**À intégrer :** Automatiser dans le pipeline après import

### Access-Aide (base accessibilité)

**Ce qu'il fait déjà :**
- Structure landmarks ARIA
- Métadonnées schema:accessibilitySummary
- Labels alternatifs images
- Langues déclarées

**Ce qu'on peut ajouter (IA) :**
- Génération automatique des descriptions d'images
- Détection des contrastes insuffisants
- Suggestions WCAG basées sur le contenu

## Références

- **Plugin Index officiel :** mobileread.com/forums/showthread.php?t=247431
- **Plugin API Guide :** sigil-ebook.com/plugin-api-guide
- **Plugin API Repo :** github.com/Sigil-Ebook/plugin-api-guide
- **DOCXImport :** github.com/dougmassay/docximport-sigil-plugin
- **ePub3-itizer :** github.com/kevinhendricks/ePub3-itizer
- **Access-Aide :** github.com/kevinhendricks/Access-Aide
- **sigil-cli :** github.com/JingMatrix/sigil-cli
