#!/usr/bin/env python3
"""
ontology_engine.py — Moteur de validation ontologique
====================================================

Valide des contenus XHTML et des actions de plugins IA
contre l'ontologie KLEIA-UP Book (book-ontology.ttl) via SHACL.

Usage:
    engine = OntologyEngine("ontology/book-ontology.ttl")
    violations = engine.validate_content(xhtml_string)
    valid = engine.validate_plugin_action("AI-Content-Cleaner", action_dict)

Dépendances : rdflib, pyshacl, lxml, html5lib
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import rdflib
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD

try:
    from pyshacl import validate as shacl_validate
except ImportError:
    shacl_validate = None  # fallback géré dans validate()


# ── Namespace ───────────────────────────────────────────────────────────────
BOOK = Namespace("http://kleia-up.fr/ontology/book#")

# Types structurels que le LLM ne doit jamais supprimer/downgrader
PROTECTED_CLASSES = frozenset({
    "h1", "h2", "h3", "h4", "h5", "h6",
    "section", "nav", "figure", "table", "blockquote",
})
CHAPTER_TITLE_TAGS = frozenset({"h1"})


class OntologyError(Exception):
    """Erreur de validation ontologique."""


class OntologyViolationError(OntologyError):
    """Une ou plusieurs violations SHACL ont bloqué l'action."""

    def __init__(self, violations: list[dict]):
        self.violations = violations
        messages = "; ".join(v.get("message", "violation") for v in violations)
        super().__init__(f"Ontologie violée ({len(violations)}): {messages}")


class OntologyEngine:
    """Moteur de validation neurosymbolique.

    Charge l'ontologie RDFS/OWL + shapes SHACL une fois,
    puis expose des validateurs pour les contenus XHTML et les actions IA.
    """

    def __init__(self, ontology_path: str | Path | None = None):
        self.graph = Graph()
        self._load_ontology(ontology_path)
        self._schema_graph = self._extract_shapes()

    # ── Chargement ─────────────────────────────────────────────────────

    def _load_ontology(self, path: str | Path | None) -> None:
        """Charge l'ontologie depuis le fichier Turtle."""
        p = Path(path or __file__).parent.parent / "ontology" / "book-ontology.ttl"
        if not p.exists():
            raise OntologyError(f"Ontologie introuvable : {p}")
        self.graph.parse(str(p), format="turtle")

    def _extract_shapes(self) -> Graph:
        """Extrait les shapes SHACL du graphe principal.

        On duplique dans un graphe dédié pour que PySHACL
        puisse valider sans modifier l'ontologie source.
        """
        shapes = Graph()
        for s, p, o in self.graph.triples((None, RDF.type, URIRef(str(sh.NodeShape)))):
            for stmt in self.graph.triples((s, None, None)):
                shapes.add(stmt)
            for stmt in self.graph.triples((None, None, s)):
                shapes.add(stmt)
        return shapes

    # ── Validation de contenu XHTML ────────────────────────────────────

    def validate_content(self, xhtml: str) -> list[dict]:
        """Parse du XHTML → graphe RDF → validation SHACL.

        Retourne la liste des violations (dict avec path, message, severity).
        """
        data = self._xhtml_to_rdf(xhtml)
        return self._run_shacl(data)

    def _xhtml_to_rdf(self, html: str) -> Graph:
        """Transforme un fragment XHTML en graphe RDF.

        On mappe les éléments HTML vers les classes de l'ontologie :
            <h1 class="chapter-title">  →  :Chapter + :hasTitle
            <p class="body-text">       →  :Paragraph + :content
            <p class="first-para">      →  :FirstParagraph
            <blockquote>                →  :BlockQuote
            <figure>                    →  :Figure
            <table>                     →  :Table
            <section class="copyright"> →  :CopyrightPage
            <section class="dedication">→  :Dedication
        """
        from lxml import etree

        g = Graph()
        # Namespace défaut pour les éléments du document
        DOC = Namespace("http://kleia-up.fr/book/document#")

        try:
            root = etree.fromstring(f"<root>{html}</root>".encode("utf-8"),
                                    parser=etree.HTMLParser())
        except Exception:
            return g

        counter = [0]

        def _elem_rdf(el) -> URIRef:
            counter[0] += 1
            return DOC[f"elem-{counter[0]}"]

        def _tag_to_class(tag: str, classes: str) -> URIRef | None:
            """Mappe (tag, classe CSS) → classe RDF de l'ontologie."""
            tag_lower = tag.lower()
            css_classes = set(classes.split()) if classes else set()

            # Mapping tag+classe → classe ontologie
            if tag_lower == "h1":
                if "chapter-title" in css_classes:
                    return BOOK.Chapter
                elif any(c in css_classes for c in ("book-title", "toc-title")):
                    return BOOK.BookTitle
                return BOOK.Section
            if tag_lower in ("h2", "h3"):
                return BOOK.Section
            if tag_lower == "p":
                if "first-para" in css_classes:
                    return BOOK.FirstParagraph
                return BOOK.Paragraph
            if tag_lower == "blockquote":
                if "epigraph" in css_classes:
                    return BOOK.Epigraph
                return BOOK.BlockQuote
            if tag_lower == "figure":
                return BOOK.Figure
            if tag_lower == "table":
                return BOOK.Table
            if tag_lower == "section":
                if "copyright" in css_classes:
                    return BOOK.CopyrightPage
                if "dedication" in css_classes:
                    return BOOK.Dedication
                return BOOK.Section
            return None

        def _walk(parent_uri: URIRef | None, el, depth: int = 0):
            """Parcourt le DOM et construit le graphe RDF."""
            if depth > 10:
                return  # sécurité anti-récursion

            uri = _elem_rdf(el)
            classes = el.get("class", "")
            tag = el.tag if isinstance(el.tag, str) else ""

            # Détermination du type ontologique
            cls = _tag_to_class(tag, classes)
            if cls is not None:
                g.add((uri, RDF.type, cls))
            else:
                # Élément non mappé → pas de nœud ontologique
                pass

            # Titres
            if tag in ("h1", "h2", "h3", "h4") and el.text and el.text.strip():
                g.add((uri, BOOK.hasTitle, Literal(el.text.strip(), datatype=XSD.string)))

            # Contenu textuel des paragraphes
            if tag == "p":
                txt = "".join(el.itertext()).strip()
                if txt:
                    g.add((uri, BOOK.content, Literal(txt, datatype=XSD.string)))

            # Relations de contenance
            if parent_uri is not None and cls is not None:
                g.add((parent_uri, BOOK.contains, uri))

            # Enfants
            for child in el:
                _walk(uri, child, depth + 1)

        _walk(None, root)
        return g

    def _run_shacl(self, data: Graph) -> list[dict]:
        """Exécute la validation SHACL sur le graphe de données."""
        if shacl_validate is None:
            return [{"path": "engine", "message": "pyshacl non installé — validation désactivée",
                     "severity": "Warning"}]

        conforms, results_graph, report_text = shacl_validate(
            data_graph=data,
            shacl_graph=self._schema_graph,
            advanced=True,
            meta_shacl=True,
        )

        if conforms:
            return []

        return self._parse_shacl_results(results_graph)

    def _parse_shacl_results(self, results: Graph) -> list[dict]:
        """Parse le graphe de résultats SHACL en liste de dict."""
        violations = []

        for result in results.subjects(RDF.type, sh.Violation):
            v = self._extract_result(results, result, "Violation")
            if v:
                violations.append(v)

        for result in results.subjects(RDF.type, sh.Warning):
            v = self._extract_result(results, result, "Warning")
            if v:
                violations.append(v)

        return violations

    def _extract_result(self, g: Graph, node, severity: str) -> dict | None:
        """Extrait une violation/warning SHACL."""
        msg = g.value(node, sh.message)
        path = g.value(node, sh.focusNode)
        if msg is None and path is None:
            return None
        return {
            "severity": severity,
            "message": str(msg) if msg else "No message",
            "path": str(path) if path else "unknown",
            "node": str(node),
        }

    # ── Validation d'actions IA ─────────────────────────────────────────

    def validate_plugin_action(self, plugin_name: str, action: dict) -> bool:
        """Valide qu'une action proposée par un plugin IA respecte l'ontologie.

        Règles programmatiques (non exprimables en SHACL pur) :

        1. PROTECTION STRUCTURELLE :
           - Le Content Cleaner ne peut pas supprimer de titres (h1-h6)
           - Le Content Cleaner ne peut pas vider un paragraphe
           - Le Content Cleaner ne peut pas downgrader un h1 en p

        2. CONTRAINTES KDP :
           - Le Theme Generator ne peut pas générer un bleeed hors {0.0, 0.125}
           - Le Theme Generator doit produire 2 variantes (EPUB + Print)

        3. SÉQUENCE PIPELINE :
           - AI-Theme-Generator ne peut pas tourner avant TemplateKDP-Import

        Retourne True si valide, lève OntologyViolationError sinon.
        """
        violations: list[str] = []

        if plugin_name == "AI-Content-Cleaner":
            violations += self._check_content_cleaner(action)

        elif plugin_name == "AI-Theme-Generator":
            violations += self._check_theme_generator(action)

        elif plugin_name == "PrintPDF-Exporter":
            violations += self._check_pdf_exporter(action)

        if violations:
            raise OntologyViolationError(
                [{"message": v, "severity": "Violation", "path": plugin_name}
                 for v in violations]
            )

        return True

    # ── Règles par plugin ───────────────────────────────────────────────

    def _check_content_cleaner(self, action: dict) -> list[str]:
        """Règles pour AI-Content-Cleaner."""
        violations: list[str] = []
        change_type = action.get("change_type", "")
        target_tag = action.get("target_tag", "").lower()

        if change_type in ("delete", "remove", "strip"):
            if target_tag in PROTECTED_CLASSES:
                violations.append(
                    f"Le Content Cleaner ne peut pas supprimer "
                    f"un élément structurel <{target_tag}>."
                )

        if change_type == "downgrade":
            if target_tag in CHAPTER_TITLE_TAGS:
                violations.append(
                    "Le Content Cleaner ne peut pas rétrograder "
                    "un titre de chapitre (<h1>)."
                )

        # Vérification : pas de paragraphe vidé
        if change_type == "empty":
            violations.append(
                "Le Content Cleaner ne peut pas vider un paragraphe."
            )

        return violations

    def _check_theme_generator(self, action: dict) -> list[str]:
        """Règles pour AI-Theme-Generator."""
        violations: list[str] = []
        theme = action.get("theme", {})

        bleed = theme.get("print", {}).get("bleed")
        if bleed is not None and bleed not in (0.0, 0.125):
            violations.append(
                f"Bleed invalide : {bleed}. Valeurs autorisées : 0.0, 0.125."
            )

        formats = set(theme.get("formats", []))
        if "epub" not in formats or "pdf" not in formats:
            violations.append(
                "Le thème doit inclure les deux formats : epub ET pdf."
            )

        trim_width = theme.get("print", {}).get("trim_width")
        trim_height = theme.get("print", {}).get("trim_height")
        if trim_width and not (4.0 <= trim_width <= 8.5):
            violations.append(f"Trim width {trim_width} hors plage KDP (4-8.5).")
        if trim_height and not (6.0 <= trim_height <= 11.0):
            violations.append(f"Trim height {trim_height} hors plage KDP (6-11).")

        return violations

    def _check_pdf_exporter(self, action: dict) -> list[str]:
        """Règles pour PrintPDF-Exporter."""
        violations: list[str] = []
        config = action.get("config", {})

        # Vérifie que le template est connu
        template = config.get("template", "")
        valid_templates = {"kdp-5x8", "kdp-5.5x8.5", "kdp-6x9", "kdp-8.5x11"}
        if template and template not in valid_templates:
            violations.append(
                f"Template KDP inconnu : {template}. "
                f"Valides : {', '.join(sorted(valid_templates))}."
            )

        # Vérifie la présence des running heads
        if config.get("running_heads") is False:
            violations.append(
                "Le PDF print doit avoir des running heads."
            )

        return violations

    # ── Utilitaires ────────────────────────────────────────────────────

    def validate_xhtml_structure(self, xhtml: str) -> list[dict]:
        """Valide la structure XHTML sans passer par PySHACL (fallback).

        Utilise des regex pour les vérifications rapides :
        - Titres de chapitre non vides
        - Pas de paragraphes vides
        - Au moins un chapitre
        """
        violations: list[dict] = []

        # Vérification : chaque h1.chapter-title a du contenu
        chapter_titles = re.findall(
            r'<h1[^>]*class="[^"]*chapter-title[^"]*"[^>]*>(.*?)</h1>',
            xhtml, re.IGNORECASE | re.DOTALL
        )
        for i, title in enumerate(chapter_titles):
            stripped = re.sub(r'<[^>]+>', '', title).strip()
            if not stripped:
                violations.append({
                    "severity": "Violation",
                    "message": f"Chapitre {i + 1} : titre vide.",
                    "path": f"chapter-{i + 1}",
                })

        if not chapter_titles:
            violations.append({
                "severity": "Warning",
                "message": "Aucun titre de chapitre (<h1 class=\"chapter-title\">) trouvé.",
                "path": "document",
            })

        # Vérification : pas de paragraphes vides
        paragraphs = re.findall(
            r'<p[^>]*>(?:\s|&nbsp;)*</p>', xhtml, re.IGNORECASE
        )
        for p in paragraphs:
            violations.append({
                "severity": "Violation",
                "message": "Paragraphe vide détecté.",
                "path": "paragraph",
            })

        return violations


def scan_for_structure_risks(plugin_name: str, before: str, after: str) -> list[dict]:
    """Compare avant/après pour détecter des suppressions structurelles.

    Utile pour les plugins IA qui risquent de supprimer des éléments.
    """
    violations: list[dict] = []

    def _count_tags(html: str, tag: str) -> int:
        return len(re.findall(f'<{tag}[\\s>]', html, re.IGNORECASE))

    for tag in PROTECTED_CLASSES:
        before_count = _count_tags(before, tag)
        after_count = _count_tags(after, tag)
        if after_count < before_count:
            violations.append({
                "severity": "Violation",
                "message": f"Plugin {plugin_name} a supprimé {before_count - after_count}x <{tag}>.",
                "path": tag,
            })

    return violations
