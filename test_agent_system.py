"""
test_agent_system.py
====================
Integration tests for the full drift detection workflow.

Run:
  python test_agent_system.py
"""

import math
import json
import os
import tempfile
from datetime import datetime, timezone

from agent_system import (
    BrightDataSimulator,
    FeatherlessReasoner,
    analyze_user_drift,
    extract_preferences,
    load_interactions_from_csv,
    load_interactions_from_json,
    load_interactions_from_memory_store,
)


PASS = "  PASS"
FAIL = "  FAIL"
errors = []
checks_run = 0


def check(name: str, condition: bool, detail: str = ""):
    global checks_run
    checks_run += 1
    if condition:
        print(f"{PASS}  {name}")
    else:
        print(f"{FAIL}  {name}  {detail}")
        errors.append(name)


def test_extract_preferences():
    now = datetime.now(timezone.utc)
    simulator = BrightDataSimulator(seed=10)
    interactions = simulator.generate_interactions(
        days=1,
        daily_events=10,
        category_weights={"action": 1.0},
        now=now,
    )
    prefs = extract_preferences(interactions)
    check("extract_preferences returns dict", isinstance(prefs, dict))
    check("single category normalized to 1.0", math.isclose(prefs.get("action", 0), 1.0, abs_tol=1e-4))


def test_end_to_end_drift_detection():
    now = datetime.now(timezone.utc)
    simulator = BrightDataSimulator(seed=42)

    past = simulator.generate_interactions(
        days=7,
        daily_events=25,
        category_weights={"action": 0.7, "comedy": 0.2, "drama": 0.1},
        now=now,
    )
    current = simulator.generate_interactions(
        days=2,
        daily_events=25,
        category_weights={"romance": 0.6, "drama": 0.3, "action": 0.1},
        now=now,
    )

    result = analyze_user_drift(
        interactions=past + current,
        past_days=7,
        current_days=2,
        now=now,
        include_chart=True,
    )

    required_keys = [
        "drift_detected",
        "drift_rate",
        "drift_label",
        "confidence",
        "top_increased",
        "top_decreased",
        "recommendations",
        "ai_explanation",
        "window_summary",
        "preference_chart",
    ]
    for key in required_keys:
        check(f"result includes '{key}'", key in result)

    check("drift detected for shifted behavior", result["drift_detected"] is True)
    check("drift label in valid set", result["drift_label"] in ("Low", "Moderate", "High"))
    check("recommendations list not empty", len(result["recommendations"]) > 0)
    check("ai explanation is string", isinstance(result["ai_explanation"], str) and len(result["ai_explanation"]) > 10)


def test_json_csv_ingestion():
    records = [
        {"category": "action", "timestamp": "2026-03-20T10:00:00+00:00", "user_id": "u1"},
        {"category": "romance", "timestamp": "2026-03-21T11:00:00+00:00", "user_id": "u1"},
    ]

    with tempfile.TemporaryDirectory() as tmp:
        json_path = os.path.join(tmp, "interactions.json")
        csv_path = os.path.join(tmp, "interactions.csv")

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump({"interactions": records}, jf)

        with open(csv_path, "w", encoding="utf-8") as cf:
            cf.write("category,timestamp,user_id\n")
            for row in records:
                cf.write(f"{row['category']},{row['timestamp']},{row['user_id']}\n")

        json_items = load_interactions_from_json(json_path)
        csv_items = load_interactions_from_csv(csv_path)

    check("json ingestion returns all rows", len(json_items) == 2)
    check("csv ingestion returns all rows", len(csv_items) == 2)
    check("json categories normalized", json_items[0].category == "action")
    check("csv categories normalized", csv_items[1].category == "romance")


def test_featherless_response_parsing():
    native = {"explanation": "User shifted toward narrative content."}
    chat = {"choices": [{"message": {"content": "Drift is high due to rise in romance."}}]}
    responses = {
        "output": [
            {"content": [{"type": "output_text", "text": "Intent shifted to emotional genres."}]}
        ]
    }

    native_text = FeatherlessReasoner._extract_text_from_response(native)
    chat_text = FeatherlessReasoner._extract_text_from_response(chat)
    responses_text = FeatherlessReasoner._extract_text_from_response(responses)

    check("native explanation parsing works", isinstance(native_text, str) and "shifted" in native_text)
    check("chat completions parsing works", isinstance(chat_text, str) and "romance" in chat_text)
    check("responses parsing works", isinstance(responses_text, str) and "Intent" in responses_text)


def test_team_data_memory_integration():
    now = datetime.now(timezone.utc)
    interactions = load_interactions_from_memory_store(user_id="user_001", past_days=7, current_days=2)
    check("team integration returns interactions", len(interactions) > 0)
    check("team integration normalizes category case", interactions[0].category == interactions[0].category.lower())

    result = analyze_user_drift(
        interactions=interactions,
        past_days=7,
        current_days=2,
        now=now,
        include_chart=False,
    )
    check("team integration result has drift_rate", "drift_rate" in result)
    check("team integration result has recommendations", "recommendations" in result)


if __name__ == "__main__":
    print("\n-- test_extract_preferences --")
    test_extract_preferences()

    print("\n-- test_end_to_end_drift_detection --")
    test_end_to_end_drift_detection()

    print("\n-- test_json_csv_ingestion --")
    test_json_csv_ingestion()

    print("\n-- test_featherless_response_parsing --")
    test_featherless_response_parsing()

    print("\n-- test_team_data_memory_integration --")
    test_team_data_memory_integration()

    total = checks_run
    passed = total - len(errors)

    print("\n" + "=" * 42)
    print(f"  Results: {passed}/{total} tests passed")
    if errors:
        print("  Failed tests:")
        for name in errors:
            print(f"    - {name}")
    else:
        print("  All tests passed.")
    print("=" * 42 + "\n")

    raise SystemExit(1 if errors else 0)
