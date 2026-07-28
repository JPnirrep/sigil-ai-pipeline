#!/usr/bin/env python3
"""
neuro_symbolic_agent.py — Wrapper Agent Neurosymbolique
=======================================================

Enrobe n'importe quel plugin IA du pipeline KLEIA-UP Book
d'une couche de validation ontologique.

Principe :
    LLM → proposition → OntologyEngine.valider() → OK → appliquer
                                                   → KO → re-générer avec feedback
                                                   → KO² → fallback heuristique

Usage :
    agent = NeuroSymbolicAgent(llm_client, OntologyEngine())
    result = agent.execute("AI-Content-Cleaner", {"xhtml": "<p>...</p>"})
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from ontology_engine import (
    OntologyEngine,
    OntologyViolationError,
    scan_for_structure_risks,
)


class NeuroSymbolicAgent:
    """Wrapper de validation ontologique pour les plugins IA.

    Attributes:
        llm:      Client LLM (n'importe quelle API compatible .generate()).
        ontology: Moteur de validation SHACL + règles programmatiques.
        verbose:  Logger optionnel pour le feedback LLM.
    """

    def __init__(
        self,
        llm_client: Any,
        ontology: OntologyEngine,
        verbose: bool = False,
        max_retries: int = 1,
        fallback_handler: Callable | None = None,
    ):
        self.llm = llm_client
        self.ontology = ontology
        self.verbose = verbose
        self.max_retries = max_retries
        self.fallback_handler = fallback_handler

    # ── Cycle de vie d'une action ──────────────────────────────────────

    def execute(self, plugin_name: str, context: dict) -> dict:
        """Exécute une action IA avec validation ontologique.

        1. Le LLM génère une proposition à partir du contexte.
        2. L'OntologyEngine la valide (SHACL + règles programmatiques).
        3. Si valide → retourne la proposition.
        4. Si invalide → re-génère avec feedback, puis re-valide.
        5. Si encore invalide → fallback heuristique.

        Args:
            plugin_name: Nom du plugin (ex: "AI-Content-Cleaner").
            context:     Contexte d'exécution (xhtml, genre, format...).

        Returns:
            Proposition validée (dict).

        Raises:
            OntologyViolationError: Si même le fallback échoue.
        """
        # ── Étape 1 : génération LLM ──
        proposal = self._llm_generate(plugin_name, context)

        # Sauvegarde de l'état avant (pour scan de différences structurelles)
        before = context.get("xhtml", "")

        # ── Étape 2 : validation ontologique ──
        try:
            self._validate(plugin_name, proposal, before)
            self._log(f"[✓] {plugin_name} : validation ontologique OK")
            return proposal

        except OntologyViolationError as e:
            self._log(f"[!] {plugin_name} : {len(e.violations)} violation(s) — "
                      f"tentative {1}/{self.max_retries + 1}")

            # ── Étape 3 : re-génération avec feedback ──
            for attempt in range(1, self.max_retries + 1):
                feedback = [v["message"] for v in e.violations]
                proposal = self._llm_regenerate(plugin_name, context, feedback)

                try:
                    self._validate(plugin_name, proposal, before)
                    self._log(f"[✓] {plugin_name} : corrigé après feedback "
                              f"(tentative {attempt + 1})")
                    return proposal

                except OntologyViolationError as e2:
                    self._log(f"[!] {plugin_name} : toujours invalide "
                              f"(tentative {attempt + 1})")
                    e = e2  # dernière exception pour le fallback

            # ── Étape 4 : fallback heuristique ──
            if self.fallback_handler:
                self._log(f"[→] {plugin_name} : fallback heuristique")
                fallback = self.fallback_handler(plugin_name, context, e.violations)
                self._validate(plugin_name, fallback, before)
                return fallback

            raise  # propagation de la dernière OntologyViolationError

    # ── Validation complète ────────────────────────────────────────────

    def _validate(self, plugin_name: str, proposal: dict, before: str) -> None:
        """Valide une proposition (SHACL + différences structurelles + règles)."""

        # 1. Validation SHACL du contenu XHTML
        if "xhtml" in proposal:
            shacl_violations = self.ontology.validate_content(proposal["xhtml"])
            if shacl_violations:
                raise OntologyViolationError(shacl_violations)

        # 2. Validation structurelle (avant/après)
        if before and "xhtml" in proposal:
            diff_violations = scan_for_structure_risks(
                plugin_name, before, proposal["xhtml"]
            )
            if diff_violations:
                raise OntologyViolationError(diff_violations)

        # 3. Validation des règles programmatiques par plugin
        self.ontology.validate_plugin_action(plugin_name, proposal)

    # ── LLM bridge ─────────────────────────────────────────────────────

    def _llm_generate(self, plugin_name: str, context: dict) -> dict:
        """Appelle le LLM pour générer une proposition initiale."""
        prompt = self._build_prompt(plugin_name, context)
        response = self.llm.complete(prompt)
        return self._parse_llm_response(response)

    def _llm_regenerate(self, plugin_name: str, context: dict,
                        feedback: list[str]) -> dict:
        """Re-génère avec feedback de l'ontologie."""
        prompt = self._build_prompt(plugin_name, context, feedback)
        response = self.llm.complete(prompt)
        return self._parse_llm_response(response)

    def _build_prompt(self, plugin_name: str, context: dict,
                      feedback: list[str] | None = None) -> str:
        """Construit le prompt LLM avec instructions ontologiques."""
        base = _PROMPT_TEMPLATES.get(plugin_name, _DEFAULT_PROMPT)
        prompt = base.format(**context)

        if feedback:
            prompt += (
                "\n\n"
                "⚠️ CORRECTIONS REQUISES PAR LE VALIDEUR ONTOLOGIQUE :\n"
                + "\n".join(f"  - {f}" for f in feedback)
                + "\n\nCorrige ta proposition pour respecter ces contraintes."
            )

        return prompt

    def _parse_llm_response(self, response: Any) -> dict:
        """Parse la réponse LLM en dict structuré."""
        if isinstance(response, dict):
            return response
        text = str(response)
        # Tente d'extraire un bloc JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Fallback : wrapper textuel
        return {"xhtml": text}

    # ── Cache de validation (anti boucle) ──────────────────────────────

    def _cache_key(self, plugin_name: str, context: dict) -> str:
        """Clé de cache pour éviter de re-valider deux fois la même chose."""
        raw = plugin_name + json.dumps(context, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[NeuroSymbolicAgent] {msg}")


# ── Templates de prompts par plugin ─────────────────────────────────────

_PROMPT_TEMPLATES = {
    "AI-Content-Cleaner": (
        "Tu es un correcteur typographique pour livre imprimé.\n"
        "Nettoie le XHTML ci-dessous selon les règles typographiques françaises :\n"
        "1. Guillemets français « » (pas de \"\")\n"
        "2. Espaces insécables avant ; : ! ?\n"
        "3. Ellipses unifiées … (pas trois points)\n"
        "4. Tirets cadratins — (pas --)\n"
        "5. Apostrophes courbes ’ (pas ')\n"
        "6. Pas d'espaces doubles\n"
        "7. NE JAMAIS supprimer les balises structurelles (h1, h2, section, figure, blockquote)\n"
        "8. NE JAMAIS vider un paragraphe\n\n"
        "{xhtml}"
    ),
    "AI-Theme-Generator": (
        "Tu es un designer de livres professionnel.\n"
        "Génère un thème CSS complet pour ce livre.\n\n"
        "Genre : {genre}\n"
        "Format : {format}\n"
        "Préférences : {preferences}\n\n"
        "CONTRAINTES ONTOLOGIQUES :\n"
        "- Le thème doit inclure les deux formats : epub ET pdf\n"
        "- Bleed autorisé : 0.0 ou 0.125 (pas d'autre valeur)\n"
        "- Trim width : entre 4 et 8.5 pouces\n"
        "- Trim height : entre 6 et 11 pouces\n"
        "- Police body : serif recommandé pour print\n"
        "- Génère au format JSON structuré"
    ),
    "PrintPDF-Exporter": (
        "Tu prépares la configuration d'export PDF print.\n\n"
        "Template : {template}\n"
        "Format : {format}\n\n"
        "CONTRAINTES ONTOLOGIQUES :\n"
        "- Utilise un template KDP valide (kdp-5x8, kdp-5.5x8.5, kdp-6x9, kdp-8.5x11)\n"
        "- Les running heads sont obligatoires\n"
        "- Les marges alternées gauche/droite sont obligatoires\n"
        "- Le bleed doit correspondre au template\n"
        "- Génère au format JSON."
    ),
}

_DEFAULT_PROMPT = (
    "Exécute l'action demandée en respectant les contraintes ontologiques.\n"
    "{context}"
)
