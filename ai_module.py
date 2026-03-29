"""
ai_module.py
============
Thin wrapper for AI explanation that reuses the project's Featherless integration.
"""

from typing import Dict, List, Tuple

from agent_system import FeatherlessReasoner


def get_ai_explanation(
    drift_rate: float,
    drift_label: str,
    top_changes: Dict[str, List[Tuple[str, float]]],
    past_prefs: Dict[str, float],
    current_prefs: Dict[str, float],
) -> str:
    """Returns an AI explanation using FeatherlessReasoner (with fallback)."""
    analysis = {
        "drift_rate": drift_rate,
        "drift_label": drift_label,
        "top_increased": top_changes.get("top_increased", []),
        "top_decreased": top_changes.get("top_decreased", []),
        "past_prefs": past_prefs,
        "current_prefs": current_prefs,
    }

    reasoner = FeatherlessReasoner()
    return reasoner.explain(analysis)
