"""
run_project.py
===============
Executable demo for the full Agent with Memory Drift Detection project.

Run:
    python run_project.py
    python run_project.py --input data/interactions.json --format json
    python run_project.py --input data/interactions.csv --format csv
"""

import argparse
from datetime import datetime, timedelta, timezone

from agent_system import (
        BrightDataSimulator,
        analyze_user_drift,
        load_interactions_from_csv,
        load_interactions_from_json,
)


def build_demo_interactions(now: datetime):
    simulator = BrightDataSimulator(seed=42)
    past_now = now - timedelta(days=2)

    # Historical behavior: action-heavy
    past_interactions = simulator.generate_interactions(
        days=7,
        daily_events=20,
        category_weights={
            "action": 0.60,
            "comedy": 0.15,
            "drama": 0.15,
            "romance": 0.10,
        },
        now=past_now,
    )

    # Recent behavior: romance + drama heavy
    current_interactions = simulator.generate_interactions(
        days=2,
        daily_events=20,
        category_weights={
            "romance": 0.45,
            "drama": 0.35,
            "comedy": 0.10,
            "action": 0.10,
        },
        now=now,
    )

    return past_interactions + current_interactions


def print_output(result):
    print("\n=== Agent with Memory Drift Detection ===")
    print(f"Drift Detected: {'YES' if result['drift_detected'] else 'NO'}")
    print(f"Drift Rate: {result['drift_rate']} ({result['drift_label']})")
    print(f"Confidence Score: {result['confidence']}")

    print("\nTop Changes:")
    for cat, delta in result["top_increased"]:
        print(f"  + {cat}: {delta:+.2f}")
    for cat, delta in result["top_decreased"]:
        print(f"  - {cat}: {delta:+.2f}")

    print("\nAI Explanation:")
    print(result["ai_explanation"])

    print("\nUpdated Recommendations:")
    for item in result["recommendations"]:
        print(f"  - {item}")

    print("\nWindow Summary:")
    summary = result["window_summary"]
    print(
        f"  Past: {summary['past_events']} events over {summary['past_days']} days | "
        f"Current: {summary['current_events']} events over {summary['current_days']} days"
    )

    if "preference_chart" in result:
        print("\nPreference Comparison:")
        print(result["preference_chart"])


def parse_args():
    parser = argparse.ArgumentParser(description="Run memory drift detection demo")
    parser.add_argument("--input", help="Path to input interactions file")
    parser.add_argument("--format", choices=["csv", "json"], help="Input file format")
    parser.add_argument("--category-field", default="category", help="Category field name")
    parser.add_argument("--timestamp-field", default="timestamp", help="Timestamp field name")
    parser.add_argument("--past-days", type=int, default=7, help="Past window size in days")
    parser.add_argument("--current-days", type=int, default=2, help="Current window size in days")
    parser.add_argument("--no-chart", action="store_true", help="Disable preference chart")
    return parser.parse_args()


def main():
    args = parse_args()
    now = datetime.now(timezone.utc)

    if args.input and args.format == "json":
        interactions = load_interactions_from_json(
            args.input,
            category_field=args.category_field,
            timestamp_field=args.timestamp_field,
        )
    elif args.input and args.format == "csv":
        interactions = load_interactions_from_csv(
            args.input,
            category_field=args.category_field,
            timestamp_field=args.timestamp_field,
        )
    else:
        interactions = build_demo_interactions(now=now)

    result = analyze_user_drift(
        interactions=interactions,
        past_days=args.past_days,
        current_days=args.current_days,
        now=now,
        include_chart=not args.no_chart,
    )
    print_output(result)


if __name__ == "__main__":
    main()
