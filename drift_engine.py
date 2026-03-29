"""
drift_engine.py
================
Member 2 — Core Logic & Intelligence Module
Agent with Memory Drift Detection | Hackathon Project

Responsibilities:
  - Cosine similarity between past and current preference dicts
  - Drift rate computation and labeling (Low / Moderate / High)
  - Top category change detection (increased / decreased)
  - Confidence score output
  - Single master runner: run_drift_analysis()

Interface contract:
  INPUT  → past_prefs: dict, current_prefs: dict
             e.g. {"action": 0.43, "drama": 0.28, ...}
  OUTPUT → drift_output: dict (see run_drift_analysis docstring)
"""

import numpy as np
from typing import Dict, List, Tuple


# ─────────────────────────────────────────────
# THRESHOLDS  (tweak here, nowhere else)
# ─────────────────────────────────────────────
DRIFT_DETECT_THRESHOLD = 0.10   # below this → no drift declared
LOW_THRESHOLD          = 0.15   # 0.00–0.15  → Low
MODERATE_THRESHOLD     = 0.45   # 0.15–0.45  → Moderate
                                # 0.45–1.00  → High
TOP_N_CHANGES          = 3      # how many increased / decreased to return
MIN_DELTA              = 0.01   # ignore noise below this delta


# ─────────────────────────────────────────────
# 1. COSINE SIMILARITY
# ─────────────────────────────────────────────
def cosine_similarity(past: Dict[str, float],
                      current: Dict[str, float]) -> float:
    """
    Compute cosine similarity between two preference distributions.
    Handles mismatched keys by filling missing categories with 0.0.

    Returns a float in [0.0, 1.0]:
      1.0 = identical preference vectors (no drift)
      0.0 = completely orthogonal (maximum drift)
    """
    all_keys = sorted(set(past) | set(current))

    v1 = np.array([past.get(k, 0.0)    for k in all_keys], dtype=float)
    v2 = np.array([current.get(k, 0.0) for k in all_keys], dtype=float)

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 1.0  # treat empty / zero vectors as identical (no drift)

    return float(np.dot(v1, v2) / (norm1 * norm2))


# ─────────────────────────────────────────────
# 2. DRIFT RATE + LABEL
# ─────────────────────────────────────────────
def compute_drift(past: Dict[str, float],
                  current: Dict[str, float]) -> Dict:
    """
    Compute drift rate (1 - cosine_similarity) and assign a label.

    Returns:
      {
        "drift_detected": bool,
        "drift_rate":     float,   # 0.0 → 1.0
        "drift_label":    str,     # "Low" | "Moderate" | "High"
        "confidence":     float,   # 1.0 - drift_rate
      }
    """
    if not past or not current:
        return {
            "drift_detected": False,
            "drift_rate":     0.0,
            "drift_label":    "Low",
            "confidence":     1.0,
        }

    similarity = cosine_similarity(past, current)
    drift_rate = round(1.0 - similarity, 4)

    if drift_rate < LOW_THRESHOLD:
        label = "Low"
    elif drift_rate < MODERATE_THRESHOLD:
        label = "Moderate"
    else:
        label = "High"

    return {
        "drift_detected": drift_rate > DRIFT_DETECT_THRESHOLD,
        "drift_rate":     drift_rate,
        "drift_label":    label,
        "confidence":     round(1.0 - drift_rate, 4),
    }


# ─────────────────────────────────────────────
# 3. TOP CHANGES
# ─────────────────────────────────────────────
def top_changes(past: Dict[str, float],
                current: Dict[str, float],
                top_n: int = TOP_N_CHANGES) -> Dict:
    """
    Find which categories increased and decreased the most.

    Returns:
      {
        "top_increased": [("comedy", +0.36), ("horror", +0.33), ...],
        "top_decreased": [("action", -0.43), ("drama", -0.28), ...],
        "all_deltas":    {"comedy": +0.36, "action": -0.43, ...}
      }
    """
    all_keys = set(past) | set(current)

    all_deltas = {
        k: round(current.get(k, 0.0) - past.get(k, 0.0), 4)
        for k in all_keys
    }

    ranked     = sorted(all_deltas.items(), key=lambda x: x[1], reverse=True)
    increased  = [(k, v) for k, v in ranked if v >  MIN_DELTA][:top_n]
    decreased  = [(k, v) for k, v in ranked if v < -MIN_DELTA][:top_n]

    return {
        "top_increased": increased,
        "top_decreased": decreased,
        "all_deltas":    all_deltas,
    }


# ─────────────────────────────────────────────
# 4. MASTER RUNNER  ← Member 3 calls this
# ─────────────────────────────────────────────
def run_drift_analysis(past: Dict[str, float],
                       current: Dict[str, float]) -> Dict:
    """
    Full drift analysis pipeline. Single entry point for the rest of the team.

    Args:
      past    — normalized preference dict from older interactions
      current — normalized preference dict from recent interactions
                e.g. {"action": 0.43, "drama": 0.28, "comedy": 0.14}

    Returns a flat dict:
      {
        "drift_detected": bool,
        "drift_rate":     float,
        "drift_label":    str,
        "confidence":     float,
        "top_increased":  [(category, delta), ...],
        "top_decreased":  [(category, delta), ...],
        "all_deltas":     {category: delta, ...},
        "past_prefs":     dict,    (echo for AI explainer)
        "current_prefs":  dict,    (echo for AI explainer)
      }
    """
    drift   = compute_drift(past, current)
    changes = top_changes(past, current)

    return {
        **drift,
        **changes,
        "past_prefs":    past,
        "current_prefs": current,
    }


# ─────────────────────────────────────────────
# 5. PRETTY PRINT (CLI helper)
# ─────────────────────────────────────────────
def print_drift_report(result: Dict) -> None:
    """Print a formatted drift report to stdout."""
    d  = result["drift_detected"]
    dr = result["drift_rate"]
    dl = result["drift_label"]
    cf = result["confidence"]

    print("\n" + "=" * 48)
    print("  DRIFT DETECTION REPORT")
    print("=" * 48)
    print(f"  Drift Detected : {'YES  ← behavior shifted' if d else 'NO   ← stable user'}")
    print(f"  Drift Rate     : {dr}  ({dl})")
    print(f"  Confidence     : {cf}")
    print("-" * 48)
    print("  Top Increases:")
    for cat, delta in result["top_increased"]:
        print(f"    + {cat:<14}  {delta:+.3f}")
    print("  Top Decreases:")
    for cat, delta in result["top_decreased"]:
        print(f"    - {cat:<14}  {delta:+.3f}")
    print("=" * 48 + "\n")


# ─────────────────────────────────────────────
# QUICK DEMO (run file directly to verify)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    past_prefs = {
        "action":  0.43,
        "drama":   0.28,
        "romance": 0.14,
        "comedy":  0.14,
    }
    current_prefs = {
        "comedy":  0.50,
        "horror":  0.33,
        "romance": 0.17,
    }

    result = run_drift_analysis(past_prefs, current_prefs)
    print_drift_report(result)
