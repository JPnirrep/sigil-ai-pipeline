#!/usr/bin/env python3
"""
sigil_ai_ontology.py — Plugin de validation ontologique pour Sigil
====================================================================

Plugin d'édition Sigil (Edit Plugin) qui valide l'EPUB ouvert
contre l'ontologie KLEIA-UP Book avant export.

Installation dans Sigil :
    Copier dans ~/.sigil/plugins/ValidateOntology/
    puis Sigil → Plugins → Manage Plugins → Add → ValidateOntology

Utilisation :
    Menu Plugins → Validate Ontology (ou hook pre_export automatique)

Dépendances :
    - rdflib, pyshacl, lxml (installés dans l'environnement Python de Sigil)
    - OntologyEngine depuis ai-integration/ontology_engine.py

Compatibilité : Sigil 2.8+, Python 3.14, Qt6
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Résolution des imports ───────────────────────────────────────────
# Le plugin tourne dans l'environnement Python embarqué de Sigil.
# On ajoute le chemin du projet pour importer l'OntologyEngine.

_PLUGIN_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _PLUGIN_DIR.parent

if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from ai_integration.ontology_engine import OntologyEngine, OntologyError

try:
    import sigil_bs4
    from bookcontainer import BookContainer
except ImportError:
    # Environnement hors Sigil (tests)
    sigil_bs4 = None
    BookContainer = None


# ── Constantes ───────────────────────────────────────────────────────

ONTOLOGY_PATH = _PROJECT_DIR / "ontology" / "book-ontology.ttl"
SEVERITY_ICONS = {
    "Violation": "❌",
    "Warning": "⚠️",
    "Info": "ℹ️",
}


# ── Plugin principal ─────────────────────────────────────────────────

class ValidateOntologyPlugin:
    """Plugin de validation ontologique pour Sigil.

    Se lance manuellement depuis Plugins → Validate Ontology,
    ou automatiquement avant tout export (via hook pre_commit).
    """

    def __init__(self):
        self.name = "Validate Ontology"
        self.type = "edit"  # Edit Plugin
        self.version = "0.1.0"
        self.author = "KLEIA-UP Book"
        self.description = (
            "Valide la structure du livre contre l'ontologie KLEIA-UP Book. "
            "Vérifie les titres, paragraphes, figures et contraintes KDP."
        )
        self.exit_code = 0
        self.error_messages: list[str] = []

    def run(self, container: BookContainer) -> int:
        """Point d'entrée appelé par Sigil.

        Args:
            container: Instance de BookContainer (EPUB ouvert dans Sigil).

        Returns:
            0 = succès, 1 = violations mineures (warnings), 2 = violations bloquantes.
        """
        # ── Initialisation du moteur ──
        try:
            engine = OntologyEngine(ONTOLOGY_PATH)
        except OntologyError as e:
            self._error(f"Erreur de chargement de l'ontologie : {e}")
            return 2

        all_violations = []
        total_checked = 0

        # ── Parcours des fichiers XHTML du livre ──
        for text_id in container.get_texts():
            try:
                html = container.readfile(text_id)
            except Exception:
                continue

            violations = engine.validate_xhtml_structure(html)
            if violations:
                all_violations.append((text_id, violations))
            total_checked += 1

        # ── Rapport ──
        violations_count = sum(len(v) for _, v in all_violations)

        if violations_count == 0:
            self._info(
                f"✅ Validation ontologique réussie : {total_checked} fichier(s) OK."
            )
            return 0

        self._report_violations(all_violations, total_checked)

        # Détermination du code de retour
        has_violations = any(
            v["severity"] == "Violation"
            for _, violations in all_violations
            for v in violations
        )
        return 2 if has_violations else 1

    # ── Rapport dans Sigil ────────────────────────────────────────────

    def _report_violations(self, violations: list, total: int) -> None:
        """Affiche le rapport dans la console/UI Sigil."""
        self._separator()
        self._info(f"📋 RAPPORT DE VALIDATION ONTOLOGIQUE ({total} fichiers)")

        for text_id, file_violations in violations:
            self._separator()
            self._info(f"📄 {text_id} : {len(file_violations)} problème(s)")

            for v in file_violations:
                icon = SEVERITY_ICONS.get(v["severity"], "•")
                self._info(f"  {icon} [{v['severity']}] {v['message']}")
                if v.get("path"):
                    self._info(f"      → {v['path']}")

        self._separator()
        total_v = sum(len(v) for _, v in violations)
        n_violations = sum(
            1 for _, vv in violations for v in vv if v["severity"] == "Violation"
        )
        n_warnings = total_v - n_violations

        summary = (
            f"{'❌' if n_violations else '⚠️'} "
            f"{n_violations} violation(s), {n_warnings} warning(s)"
        )
        self._info(summary)

        if n_violations:
            self._info(
                "Corrige les violations avant d'exporter. "
                "Les warnings sont des suggestions."
            )

    # ── Logging ───────────────────────────────────────────────────────

    def _info(self, msg: str) -> None:
        """Affiche un message dans la console Sigil."""
        print(msg)

    def _error(self, msg: str) -> None:
        self.error_messages.append(msg)
        print(f"ERROR: {msg}")

    def _separator(self) -> None:
        print("-" * 60)

    # ── Hook pre_export (appelé par l'orchestrateur, pas par Sigil) ──

    def pre_export_check(self, container: BookContainer, format_type: str) -> bool:
        """Vérification rapide avant export.

        Appelée par PrintPDF-Exporter avant de lancer WeasyPrint.
        Retourne False si l'export doit être bloqué.
        """
        result = self.run(container)
        if result == 2:
            print("❌ Export bloqué : violations ontologiques critiques.")
            return False
        if result == 1:
            print("⚠️ Export autorisé avec warnings.")
        return True


# ── CLI pour tests hors Sigil ────────────────────────────────────────

def _main_cli():
    """Point d'entrée CLI pour tester le plugin en dehors de Sigil.

    Usage:
        python sigil_ai_ontology.py <epub_path>

    Simule un BookContainer minimal (lecture des fichiers depuis un ZIP EPUB).
    """
    import zipfile
    import tempfile

    if len(sys.argv) < 2:
        print("Usage: sigil_ai_ontology.py <chemin.epub>")
        sys.exit(1)

    epub_path = sys.argv[1]

    # ── BookContainer simulé ──
    class MockContainer:
        def __init__(self, path):
            self.path = path
            self._files = {}
            with zipfile.ZipFile(path, "r") as z:
                for name in z.namelist():
                    if name.endswith(".xhtml") or name.endswith(".html"):
                        self._files[name] = z.read(name).decode("utf-8")

        def get_texts(self):
            return list(self._files.keys())

        def readfile(self, text_id):
            return self._files.get(text_id, "")

    container = MockContainer(epub_path)
    plugin = ValidateOntologyPlugin()
    exit_code = plugin.run(container)
    sys.exit(exit_code)


if __name__ == "__main__":
    _main_cli()
