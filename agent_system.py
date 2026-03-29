"""
agent_system.py
================
End-to-end memory drift detection pipeline that wraps drift_engine.py.

Architecture coverage:
- Data Layer: BrightDataSimulator (mock interaction source)
- Memory Module: InteractionMemory (past/current temporal windows)
- Processing Layer: extract_preferences + run_drift_analysis
- AI Reasoning Layer: FeatherlessReasoner (API hook + local fallback)
- Output Layer: structured output and optional ASCII visualization
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import random
from typing import Any, Dict, Iterable, List, Optional
from urllib import request
from urllib.error import HTTPError, URLError

from drift_engine import run_drift_analysis

try:
    from data_source import BrightDataSource
    from memory_store import MemoryStore
except Exception:
    BrightDataSource = None
    MemoryStore = None


@dataclass(frozen=True)
class Interaction:
    """Represents a single user interaction event."""

    category: str
    timestamp: datetime
    source: str = "bright_data_sim"
    metadata: Dict[str, str] = field(default_factory=dict)


class BrightDataSimulator:
    """Generates synthetic user interaction data similar to a data vendor feed."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def generate_interactions(
        self,
        days: int,
        daily_events: int,
        category_weights: Dict[str, float],
        now: Optional[datetime] = None,
    ) -> List[Interaction]:
        if days <= 0 or daily_events <= 0:
            return []

        now = now or datetime.now(timezone.utc)
        categories = list(category_weights.keys())
        weights = [max(0.0, category_weights[c]) for c in categories]

        if not categories or sum(weights) == 0:
            return []

        interactions: List[Interaction] = []
        for day_offset in range(days):
            base_day = now - timedelta(days=(days - day_offset))
            for _ in range(daily_events):
                category = self._rng.choices(categories, weights=weights, k=1)[0]
                second_offset = self._rng.randint(0, 86399)
                ts = base_day + timedelta(seconds=second_offset)
                interactions.append(Interaction(category=category, timestamp=ts))

        interactions.sort(key=lambda x: x.timestamp)
        return interactions


def _parse_timestamp(value: Any) -> datetime:
    """Parses timestamps from ISO text, unix int/float, or datetime values."""
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
    elif isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    else:
        raise ValueError(f"Unsupported timestamp format: {value!r}")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_interactions_from_json(
    file_path: str,
    category_field: str = "category",
    timestamp_field: str = "timestamp",
    source: str = "bright_data_json",
) -> List[Interaction]:
    """
    Loads interactions from JSON file.

    Accepted shapes:
    - list[dict]
    - {"interactions": list[dict]}
    """
    raw = json.loads(Path(file_path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        records = raw.get("interactions", [])
    elif isinstance(raw, list):
        records = raw
    else:
        raise ValueError("JSON must be a list or object containing 'interactions'.")

    interactions: List[Interaction] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        category = str(rec.get(category_field, "")).strip().lower()
        timestamp_raw = rec.get(timestamp_field)
        if not category or timestamp_raw is None:
            continue
        timestamp = _parse_timestamp(timestamp_raw)
        meta = {k: str(v) for k, v in rec.items() if k not in {category_field, timestamp_field}}
        interactions.append(
            Interaction(category=category, timestamp=timestamp, source=source, metadata=meta)
        )

    interactions.sort(key=lambda x: x.timestamp)
    return interactions


def load_interactions_from_csv(
    file_path: str,
    category_field: str = "category",
    timestamp_field: str = "timestamp",
    source: str = "bright_data_csv",
) -> List[Interaction]:
    """Loads interactions from a CSV file with category and timestamp columns."""
    interactions: List[Interaction] = []
    with Path(file_path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = str(row.get(category_field, "")).strip().lower()
            timestamp_raw = row.get(timestamp_field)
            if not category or not timestamp_raw:
                continue
            timestamp = _parse_timestamp(timestamp_raw)
            meta = {k: str(v) for k, v in row.items() if k not in {category_field, timestamp_field}}
            interactions.append(
                Interaction(category=category, timestamp=timestamp, source=source, metadata=meta)
            )

    interactions.sort(key=lambda x: x.timestamp)
    return interactions


def interactions_from_records(
    records: Iterable[Dict[str, Any]],
    category_field: str = "category",
    timestamp_field: str = "timestamp",
    source: str = "external_records",
) -> List[Interaction]:
    """Converts external dict records into normalized Interaction objects."""
    interactions: List[Interaction] = []
    for record in records:
        category_raw = record.get(category_field)
        timestamp_raw = record.get(timestamp_field)
        if category_raw is None or timestamp_raw is None:
            continue

        category = str(category_raw).strip().lower()
        if not category:
            continue

        timestamp = _parse_timestamp(timestamp_raw)
        meta = {
            k: str(v)
            for k, v in record.items()
            if k not in {category_field, timestamp_field}
        }
        interactions.append(
            Interaction(category=category, timestamp=timestamp, source=source, metadata=meta)
        )

    interactions.sort(key=lambda x: x.timestamp)
    return interactions


def load_interactions_from_memory_store(
    user_id: str = "user_001",
    past_days: int = 7,
    current_days: int = 2,
) -> List[Interaction]:
    """
    Loads interactions via teammate modules data_source.py + memory_store.py.

    Returns a combined list of past+current events converted to Interaction objects.
    """
    if BrightDataSource is None or MemoryStore is None:
        raise RuntimeError("data_source.py or memory_store.py is unavailable for integration.")

    source = BrightDataSource(user_id=user_id)
    memory = MemoryStore(user_id=user_id)
    memory.load_from_source(source)

    past_records = memory.get_past()
    current_records = memory.get_current()

    past_interactions = interactions_from_records(
        past_records,
        source=f"memory_store_past_{past_days}d",
    )
    current_interactions = interactions_from_records(
        current_records,
        source=f"memory_store_current_{current_days}d",
    )

    combined = past_interactions + current_interactions
    combined.sort(key=lambda x: x.timestamp)
    return combined


class InteractionMemory:
    """Stores interactions and returns past/current windows for drift analysis."""

    def __init__(self, interactions: Optional[Iterable[Interaction]] = None):
        self.interactions: List[Interaction] = sorted(
            list(interactions or []), key=lambda x: x.timestamp
        )

    def add(self, interaction: Interaction) -> None:
        self.interactions.append(interaction)
        self.interactions.sort(key=lambda x: x.timestamp)

    def split_windows(
        self,
        current_days: int = 2,
        past_days: int = 7,
        now: Optional[datetime] = None,
    ) -> Dict[str, List[Interaction]]:
        """
        Splits interactions into two windows:
        - current: [now - current_days, now]
        - past: [now - current_days - past_days, now - current_days)
        """
        now = now or datetime.now(timezone.utc)
        current_start = now - timedelta(days=current_days)
        past_start = current_start - timedelta(days=past_days)

        current = [x for x in self.interactions if current_start <= x.timestamp <= now]
        past = [x for x in self.interactions if past_start <= x.timestamp < current_start]

        return {"past": past, "current": current}


def extract_preferences(interactions: Iterable[Interaction]) -> Dict[str, float]:
    """Converts interaction sequence into normalized category preference distribution."""
    counts = Counter(x.category for x in interactions)
    total = sum(counts.values())

    if total == 0:
        return {}

    return {k: round(v / total, 4) for k, v in sorted(counts.items())}


def recommend_categories(current_prefs: Dict[str, float], top_n: int = 3) -> List[str]:
    """Returns recommendation labels from strongest current preference categories."""
    ranked = sorted(current_prefs.items(), key=lambda kv: kv[1], reverse=True)
    return [f"{cat.title()} content" for cat, _ in ranked[:top_n]]


class FeatherlessReasoner:
    """
    AI reasoning wrapper.

    If FEATHERLESS_API_URL and FEATHERLESS_API_KEY are present, a POST request is made.
    Otherwise a local template explanation is returned.
    """

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.getenv("FEATHERLESS_API_URL", "").strip()
        self.api_key = api_key or os.getenv("FEATHERLESS_API_KEY", "").strip()
        self.model = os.getenv("FEATHERLESS_MODEL", "featherless/default").strip()
        # Supported values: native, chat_completions, responses
        self.schema = os.getenv("FEATHERLESS_SCHEMA", "native").strip().lower()

    def explain(self, analysis: Dict) -> str:
        if self.api_url and self.api_key:
            remote = self._explain_remote(analysis)
            if remote:
                return remote

        return self._explain_local(analysis)

    def _explain_remote(self, analysis: Dict) -> Optional[str]:
        payload = self._build_payload(analysis)

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = request.Request(self.api_url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
        except (HTTPError, URLError, TimeoutError, ValueError):
            return None

        return self._extract_text_from_response(parsed)

    def _build_payload(self, analysis: Dict) -> Dict[str, Any]:
        instruction = "Explain user behavioral drift and infer intent in concise business language."
        analysis_block = {
            "drift_rate": analysis["drift_rate"],
            "drift_label": analysis["drift_label"],
            "top_increased": analysis["top_increased"],
            "top_decreased": analysis["top_decreased"],
            "past_prefs": analysis["past_prefs"],
            "current_prefs": analysis["current_prefs"],
        }

        if self.schema == "chat_completions":
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": instruction},
                    {
                        "role": "user",
                        "content": f"Analyze this drift payload and return explanation only: {json.dumps(analysis_block)}",
                    },
                ],
                "temperature": 0.2,
            }

        if self.schema == "responses":
            return {
                "model": self.model,
                "input": [
                    {"role": "system", "content": instruction},
                    {
                        "role": "user",
                        "content": f"Analyze this drift payload and return explanation only: {json.dumps(analysis_block)}",
                    },
                ],
                "temperature": 0.2,
            }

        return {
            "task": instruction,
            "analysis": analysis_block,
        }

    @staticmethod
    def _extract_text_from_response(parsed: Any) -> Optional[str]:
        """Extracts explanation text across common LLM API response formats."""
        if not isinstance(parsed, dict):
            return None

        direct = parsed.get("explanation") or parsed.get("text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        choices = parsed.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                text = first.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

        output = parsed.get("output")
        if isinstance(output, list):
            text_parts: List[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict):
                            txt = c.get("text")
                            if isinstance(txt, str) and txt.strip():
                                text_parts.append(txt.strip())
            if text_parts:
                return "\n".join(text_parts)

        return None

    @staticmethod
    def _explain_local(analysis: Dict) -> str:
        increases = analysis.get("top_increased", [])
        decreases = analysis.get("top_decreased", [])

        inc_txt = ", ".join(f"{k} ({v:+.2f})" for k, v in increases) or "no meaningful increases"
        dec_txt = ", ".join(f"{k} ({v:+.2f})" for k, v in decreases) or "no meaningful decreases"

        drift_label = analysis.get("drift_label", "Low")
        if drift_label == "High":
            intent = "a strong change in user intent toward different content themes"
        elif drift_label == "Moderate":
            intent = "a partial shift in interest while retaining some prior preferences"
        else:
            intent = "mostly stable preferences with minor variation"

        return (
            "Behavior analysis indicates "
            f"{intent}. Top increases: {inc_txt}. Top decreases: {dec_txt}."
        )


def render_preference_chart(
    past_prefs: Dict[str, float],
    current_prefs: Dict[str, float],
    width: int = 24,
) -> str:
    """Returns an ASCII side-by-side preference chart."""
    all_categories = sorted(set(past_prefs) | set(current_prefs))
    lines = ["Category            Past                      Current"]
    lines.append("-" * 62)

    for cat in all_categories:
        p = past_prefs.get(cat, 0.0)
        c = current_prefs.get(cat, 0.0)
        p_bar = "#" * int(round(p * width))
        c_bar = "#" * int(round(c * width))
        lines.append(
            f"{cat:<18} {p:>5.2f} {p_bar:<24} {c:>5.2f} {c_bar:<24}"
        )

    return "\n".join(lines)


def analyze_user_drift(
    interactions: Iterable[Interaction],
    current_days: int = 2,
    past_days: int = 7,
    now: Optional[datetime] = None,
    include_chart: bool = True,
) -> Dict:
    """Runs the complete workflow and returns a structured explainable output."""
    memory = InteractionMemory(interactions)
    windows = memory.split_windows(current_days=current_days, past_days=past_days, now=now)

    past_prefs = extract_preferences(windows["past"])
    current_prefs = extract_preferences(windows["current"])

    analysis = run_drift_analysis(past_prefs, current_prefs)
    analysis["recommendations"] = recommend_categories(current_prefs, top_n=3)

    reasoner = FeatherlessReasoner()
    analysis["ai_explanation"] = reasoner.explain(analysis)

    if include_chart:
        analysis["preference_chart"] = render_preference_chart(past_prefs, current_prefs)

    analysis["window_summary"] = {
        "past_days": past_days,
        "current_days": current_days,
        "past_events": len(windows["past"]),
        "current_events": len(windows["current"]),
    }
    return analysis
