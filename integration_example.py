"""
integration_example.py
=======================
Shows exactly how Member 1 and Member 3 connect to drift_engine.py.
This is NOT production code — it is a wiring demo for the full team.

Run:  python integration_example.py
"""

from drift_engine import run_drift_analysis, print_drift_report


# ─────────────────────────────────────────────────────────
# STEP 1: Receive from Member 1 (data + memory module)
#   In the real system, Member 1 calls extract_preferences()
#   and passes the two dicts here.
# ─────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────
# STEP 2: Run the drift analysis (Member 2's module)
# ─────────────────────────────────────────────────────────

drift_output = run_drift_analysis(past_prefs, current_prefs)
print_drift_report(drift_output)


# ─────────────────────────────────────────────────────────
# STEP 3: Pass drift_output to Member 3 (AI + Output module)
#   Member 3 only needs to import run_drift_analysis and
#   call it — they don't touch any internal functions.
#
#   Member 3's code looks like this:
#
#   from drift_engine import run_drift_analysis
#   result = run_drift_analysis(past_prefs, current_prefs)
#
#   They then pass result into their Featherless AI prompt:
#
#   prompt = f"""
#   Past preferences:    {result['past_prefs']}
#   Current preferences: {result['current_prefs']}
#   Drift rate:          {result['drift_rate']} ({result['drift_label']})
#   Top increases:       {result['top_increased']}
#   Top decreases:       {result['top_decreased']}
#   Explain why this shift occurred and recommend 3 categories.
#   """
# ─────────────────────────────────────────────────────────

print("drift_output keys available for Member 3:")
for k, v in drift_output.items():
    print(f"  result['{k}'] = {v}")
