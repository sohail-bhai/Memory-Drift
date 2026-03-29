"""
test_drift.py
=============
Test suite for drift_engine.py — Member 2
Run with:  python test_drift.py
"""

import sys
import math
from drift_engine import (
    cosine_similarity,
    compute_drift,
    top_changes,
    run_drift_analysis,
)

PASS = "  PASS"
FAIL = "  FAIL"
errors = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        print(f"{PASS}  {name}")
    else:
        print(f"{FAIL}  {name}  {detail}")
        errors.append(name)


# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────
PAST = {
    "action":  0.43,
    "drama":   0.28,
    "romance": 0.14,
    "comedy":  0.14,
}
CURRENT = {
    "comedy":  0.50,
    "horror":  0.33,
    "romance": 0.17,
}
IDENTICAL = dict(PAST)
SINGLE_PAST    = {"action": 1.0}
SINGLE_CURRENT = {"comedy": 1.0}


# ─────────────────────────────────────────
# TEST BLOCK 1: cosine_similarity
# ─────────────────────────────────────────
print("\n── cosine_similarity ──────────────────")

sim_same = cosine_similarity(PAST, IDENTICAL)
check("identical dicts → similarity = 1.0", math.isclose(sim_same, 1.0, abs_tol=1e-6))

sim_diff = cosine_similarity(PAST, CURRENT)
check("different dicts → similarity < 1.0", sim_diff < 1.0)
check("similarity in [0, 1]", 0.0 <= sim_diff <= 1.0)

sim_ortho = cosine_similarity(SINGLE_PAST, SINGLE_CURRENT)
check("orthogonal single-cat dicts → similarity = 0.0",
      math.isclose(sim_ortho, 0.0, abs_tol=1e-6))

sim_empty = cosine_similarity({}, {})
check("empty dicts → similarity = 1.0 (no drift)",
      math.isclose(sim_empty, 1.0, abs_tol=1e-6))


# ─────────────────────────────────────────
# TEST BLOCK 2: compute_drift
# ─────────────────────────────────────────
print("\n── compute_drift ───────────────────────")

d_same = compute_drift(PAST, IDENTICAL)
check("identical → drift_detected = False",  d_same["drift_detected"] is False)
check("identical → drift_rate ≈ 0.0",        math.isclose(d_same["drift_rate"], 0.0, abs_tol=1e-6))
check("identical → label = 'Low'",           d_same["drift_label"] == "Low")
check("identical → confidence ≈ 1.0",        math.isclose(d_same["confidence"], 1.0, abs_tol=1e-6))

d_diff = compute_drift(PAST, CURRENT)
check("different → drift_detected = True",   d_diff["drift_detected"] is True)
check("different → drift_rate > 0",          d_diff["drift_rate"] > 0)
check("different → label in valid set",
      d_diff["drift_label"] in ("Low", "Moderate", "High"))
check("rate + confidence ≈ 1.0",
      math.isclose(d_diff["drift_rate"] + d_diff["confidence"], 1.0, abs_tol=1e-4))

d_ortho = compute_drift(SINGLE_PAST, SINGLE_CURRENT)
check("orthogonal → label = 'High'",         d_ortho["drift_label"] == "High")
check("orthogonal → drift_rate ≈ 1.0",       math.isclose(d_ortho["drift_rate"], 1.0, abs_tol=1e-4))

d_empty = compute_drift({}, {})
check("empty input → drift_detected = False", d_empty["drift_detected"] is False)


# ─────────────────────────────────────────
# TEST BLOCK 3: top_changes
# ─────────────────────────────────────────
print("\n── top_changes ─────────────────────────")

changes = top_changes(PAST, CURRENT)

check("returns top_increased list",           isinstance(changes["top_increased"], list))
check("returns top_decreased list",           isinstance(changes["top_decreased"], list))
check("returns all_deltas dict",              isinstance(changes["all_deltas"], dict))

inc_cats = [c for c, _ in changes["top_increased"]]
dec_cats = [c for c, _ in changes["top_decreased"]]

check("comedy increased",                     "comedy" in inc_cats)
check("horror increased",                     "horror" in inc_cats)
check("action decreased",                     "action" in dec_cats)
check("drama decreased",                      "drama"  in dec_cats)

check("increased values are positive",
      all(v > 0 for _, v in changes["top_increased"]))
check("decreased values are negative",
      all(v < 0 for _, v in changes["top_decreased"]))

check("max top_n = 3 for increased",          len(changes["top_increased"]) <= 3)
check("max top_n = 3 for decreased",          len(changes["top_decreased"]) <= 3)

same_changes = top_changes(PAST, IDENTICAL)
check("identical dicts → no increases",       len(same_changes["top_increased"]) == 0)
check("identical dicts → no decreases",       len(same_changes["top_decreased"]) == 0)


# ─────────────────────────────────────────
# TEST BLOCK 4: run_drift_analysis
# ─────────────────────────────────────────
print("\n── run_drift_analysis (master runner) ──")

result = run_drift_analysis(PAST, CURRENT)

required_keys = [
    "drift_detected", "drift_rate", "drift_label", "confidence",
    "top_increased", "top_decreased", "all_deltas",
    "past_prefs", "current_prefs",
]
for key in required_keys:
    check(f"output contains key '{key}'", key in result)

check("past_prefs echoed correctly",    result["past_prefs"] == PAST)
check("current_prefs echoed correctly", result["current_prefs"] == CURRENT)

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
total  = 32
passed = total - len(errors)
print(f"\n{'='*42}")
print(f"  Results: {passed}/{total} tests passed")
if errors:
    print("  Failed tests:")
    for e in errors:
        print(f"    - {e}")
else:
    print("  All tests passed — module is ready to integrate.")
print(f"{'='*42}\n")

sys.exit(1 if errors else 0)
