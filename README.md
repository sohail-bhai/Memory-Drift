# Agent with Memory Drift Detection

End-to-end adaptive recommendation project with memory-based drift detection and explainable output.

This workspace now includes:
- Core drift engine (`drift_engine.py`)
- Full workflow pipeline (`agent_system.py`)
- End-to-end runnable demo (`run_project.py`)
- Core and integration tests (`test_drift.py`, `test_agent_system.py`)

## Files

| File | What it does |
|---|---|
| `drift_engine.py` | Core logic (cosine similarity, drift scoring, labels, top changes) |
| `agent_system.py` | Full architecture: data source, memory windows, extraction, AI reasoning, recommendations, output |
| `run_project.py` | Run complete workflow with simulated user behavior drift |
| `integration_example.py` | Wiring example for team integration |
| `test_drift.py` | Unit tests for core drift engine |
| `test_agent_system.py` | End-to-end tests for full pipeline |
| `requirements.txt` | Python dependencies |

## Setup

```bash
pip install -r requirements.txt
```

## Run the Project

```bash
python run_project.py
python run_project.py --input data/interactions.json --format json
python run_project.py --input data/interactions.csv --format csv
```

## One-Command Demo (Recommended)

```bash
python demo_runbook.py
```

This runs two scenarios in sequence:
- Stable behavior using `data/interactions_stable.json`
- High drift behavior using `data/interactions.json`

It prints a final side-by-side summary so judges can quickly compare adaptive behavior.

The script prints:
- Drift detected flag
- Drift rate and label
- Top increases/decreases
- AI explanation (Featherless API if configured, otherwise local reasoning)
- Updated recommendations
- Past vs current preference chart

## Run Tests

```bash
python test_drift.py
python test_agent_system.py
```

## Optional Featherless AI Integration

Set environment variables before running:

```bash
set FEATHERLESS_API_URL=https://your-featherless-endpoint
set FEATHERLESS_API_KEY=your_api_key
set FEATHERLESS_SCHEMA=native
set FEATHERLESS_MODEL=featherless/default
```

`FEATHERLESS_SCHEMA` supported values:
- `native` (default): expects a custom endpoint with `{task, analysis}` payload
- `chat_completions`: sends OpenAI-like `messages` payload and parses `choices[0].message.content`
- `responses`: sends OpenAI-like Responses API payload and parses `output[].content[].text`

If these are not set, the system uses built-in local reasoning templates.

## Bright Data File Input Contract

JSON accepted shapes:

```json
[
    {"category": "action", "timestamp": "2026-03-20T10:00:00+00:00"}
]
```

or

```json
{
    "interactions": [
        {"category": "romance", "timestamp": "2026-03-21T11:00:00+00:00"}
    ]
}
```

CSV required columns (default):
- `category`
- `timestamp`

Override column names if needed:

```bash
python run_project.py --input data/events.csv --format csv --category-field genre --timestamp-field event_time
```

## Demo Readiness Checklist

Before presenting:
- Run `python test_drift.py` and `python test_agent_system.py` (both must pass).
- Prepare one sample dataset with obvious drift and one with stable behavior.
- Set Featherless environment variables and verify API call once.
- Keep a fallback path ready (local explanation mode works without API).
- Freeze thresholds (`DRIFT_DETECT_THRESHOLD`, `LOW_THRESHOLD`, `MODERATE_THRESHOLD`) and do not retune during live demo.
- Record one expected output snapshot (drift rate + top changes + recommendations) to compare quickly if behavior looks off.
- Ensure system clock and timezone are stable if you use recent-window analysis on live data.

## Core API

```python
from drift_engine import run_drift_analysis  # ← Member 3 only needs this

result = run_drift_analysis(past_prefs, current_prefs)
```

Output dict shape:
```python
{
    "drift_detected": True,
    "drift_rate":     0.67,
    "drift_label":    "High",        # Low / Moderate / High
    "confidence":     0.33,
    "top_increased":  [("comedy", 0.36), ("horror", 0.33)],
    "top_decreased":  [("action", -0.43), ("drama", -0.28)],
    "all_deltas":     {"comedy": 0.36, "horror": 0.33, ...},
    "past_prefs":     {...},          # echoed for AI explainer
    "current_prefs":  {...},          # echoed for AI explainer
}
```

## Adjusting thresholds

All tunable values are at the top of `drift_engine.py`:

```python
DRIFT_DETECT_THRESHOLD = 0.10   # minimum rate to declare drift
LOW_THRESHOLD          = 0.15   # below this → Low
MODERATE_THRESHOLD     = 0.45   # below this → Moderate, above → High
TOP_N_CHANGES          = 3      # how many categories to report
MIN_DELTA              = 0.01   # ignore tiny noise changes
```

Change these values only — do not touch the function logic.

## Interface contract with teammates

**From Member 1** — expects two normalized dicts:
```python
past_prefs    = {"action": 0.43, "drama": 0.28, "comedy": 0.14, "romance": 0.14}
current_prefs = {"comedy": 0.50, "horror": 0.33, "romance": 0.17}
```
Values must sum to ~1.0 per dict. Missing categories are treated as 0.0.

**To Member 3** — delivers one flat result dict (see shape above).
Member 3 imports `run_drift_analysis` and calls it directly. They touch nothing else.
