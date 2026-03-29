"""
demo_runbook.py
================
One-command demo orchestrator for presentation.

Runs two scenarios:
1) Stable behavior (low/no drift)
2) High drift behavior

Usage:
  python demo_runbook.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from agent_system import analyze_user_drift, load_interactions_from_json


def run_scenario(name: str, input_path: Path, now: datetime) -> Dict:
    interactions = load_interactions_from_json(str(input_path))
    result = analyze_user_drift(
        interactions=interactions,
        past_days=7,
        current_days=2,
        now=now,
        include_chart=False,
    )

    print("\n" + "=" * 64)
    print(f"Scenario: {name}")
    print("=" * 64)
    print(f"Input file       : {input_path}")
    print(f"Drift detected   : {'YES' if result['drift_detected'] else 'NO'}")
    print(f"Drift rate       : {result['drift_rate']} ({result['drift_label']})")
    print(f"Confidence score : {result['confidence']}")

    print("Top increases    :", result["top_increased"])
    print("Top decreases    :", result["top_decreased"])
    print("Recommendations  :", result["recommendations"])
    print("AI explanation   :", result["ai_explanation"])

    summary = result["window_summary"]
    print(
        "Window summary   : "
        f"past={summary['past_events']} events/{summary['past_days']}d, "
        f"current={summary['current_events']} events/{summary['current_days']}d"
    )

    return result


def main() -> None:
    now = datetime.now(timezone.utc)
    root = Path(__file__).resolve().parent

    stable_path = root / "data" / "interactions_stable.json"
    drift_path = root / "data" / "interactions.json"

    if not stable_path.exists() or not drift_path.exists():
        missing = [str(p) for p in [stable_path, drift_path] if not p.exists()]
        raise FileNotFoundError(f"Missing demo dataset files: {missing}")

    stable = run_scenario("Stable behavior", stable_path, now)
    shifted = run_scenario("High drift behavior", drift_path, now)

    print("\n" + "#" * 64)
    print("DEMO SUMMARY")
    print("#" * 64)
    print(
        f"Stable scenario  -> drift_rate={stable['drift_rate']} "
        f"({stable['drift_label']}) | detected={stable['drift_detected']}"
    )
    print(
        f"Shift scenario   -> drift_rate={shifted['drift_rate']} "
        f"({shifted['drift_label']}) | detected={shifted['drift_detected']}"
    )
    print("Ready to present: adaptive behavior tracking + explainable recommendations.")


if __name__ == "__main__":
    main()
