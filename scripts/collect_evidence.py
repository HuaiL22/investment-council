#!/usr/bin/env python3
"""Collect a frozen, source-attributed, no-key evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import pandas as pd
import yfinance as yf

EVIDENCE_STRENGTHS = {"strong", "medium", "weak", "unverified"}
EVIDENCE_KINDS = {
    "observed_fact", "management_claim", "analytical_input", "unverified_lead",
}
EVIDENCE_SCOPES = {"shared", "candidate"}
RECORD_STATUSES = {
    "available", "partial", "conflict", "stale", "unavailable",
    "historical_unavailable", "quarantined", "inapplicable",
}
DEFAULT_MACRO_SERIES = (
    {
        "key": "vix",
        "ticker": "^VIX",
        "label": "CBOE Volatility Index",
        "kind": "index",
        "unit": "index",
    },
    {
        "key": "us_2y",
        "ticker": "^UST2Y",
        "label": "US 2-year Treasury yield",
        "kind": "yield",
        "unit": "percent",
    },
    {
        "key": "us_10y",
        "ticker": "^TNX",
        "label": "US 10-year Treasury yield",
        "kind": "yield",
        "unit": "percent",
    },
    {
        "key": "dxy",
        "ticker": "DX-Y.NYB",
        "label": "US Dollar Index",
        "kind": "index",
        "unit": "index",
    },
)


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().astimezone(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def parse_cutoff(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("analysis_cutoff must be timezone-aware")
    return parsed


def daily_available(value: str) -> str:
    """Use the next local midnight as a conservative daily-bar availability."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (parsed + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def content_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def status(name: str, state: str, fetched_at: str, error: str | None = None) -> dict[str, Any]:
    return {"source": name, "status": state, "fetched_at": fetched_at, "error": error}


def attempt(name: str, fetched_at: str, fn: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    try:
        value = fn()
        if value is None:
            empty = True
        elif isinstance(value, pd.DataFrame):
            empty = value.empty
        else:
            empty = value == [] or value == {}
        return value, status(name, "unavailable" if empty else "available", fetched_at, "empty result" if empty else None)
    except Exception as exc:
        return None, status(name, "unavailable", fetched_at, f"{type(exc).__name__}: {exc}")


def frame_records(frame: pd.DataFrame, field: str = "date") -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    frame = frame.copy().reset_index()
    first = frame.columns[0]
    frame = frame.rename(columns={first: field})
    frame.columns = [str(c).lower().replace(" ", "_") for c in frame.columns]
    records = []
    for row in frame.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if pd.isna(value):
                clean[key] = None
            elif isinstance(value, (pd.Timestamp, datetime)):
                clean[key] = iso(value)
            elif hasattr(value, "item"):
                clean[key] = value.item()
            else:
                clean[key] = value
        records.append(clean)
    return records


def validate_macro_series(value: Any) -> list[dict[str, str]]:
    raw_series = list(DEFAULT_MACRO_SERIES) if value is None else value
    if not isinstance(raw_series, list):
        raise ValueError("macro_series must be an array")
    output = []
    seen = set()
    for index, raw in enumerate(raw_series):
        if not isinstance(raw, dict):
            raise ValueError(f"macro_series entry {index} must be an object")
        entry = {
            "key": str(raw.get("key") or "").strip(),
            "ticker": str(raw.get("ticker") or "").strip(),
            "label": str(raw.get("label") or raw.get("key") or "").strip(),
            "kind": str(raw.get("kind") or "index").strip(),
            "unit": str(raw.get("unit") or "index").strip(),
        }
        if not entry["key"] or not entry["ticker"] or not entry["label"]:
            raise ValueError(f"macro_series entry {index} requires key, ticker, and label")
        if entry["kind"] not in {"index", "yield", "fx"}:
            raise ValueError(f"macro_series entry {index} kind must be index, yield, or fx")
        if entry["key"] in seen:
            raise ValueError(f"duplicate macro_series key: {entry['key']}")
        seen.add(entry["key"])
        output.append(entry)
    if not output:
        raise ValueError("macro_series must not be empty when macro context is enabled")
    return output


def macro_metric(value: float | None, status_value: str, unit: str, **extra: Any) -> dict[str, Any]:
    output = {"status": status_value, "value": value, "unit": unit}
    output.update(extra)
    return output


def summarize_macro_history(
    frame: pd.DataFrame,
    spec: dict[str, str],
    cutoff: datetime,
    percentile_window: int = 252,
) -> dict[str, Any]:
    if percentile_window < 20:
        raise ValueError("macro percentile window must be at least 20 sessions")
    admitted = []
    for row in frame_records(frame):
        observed = row.get("date")
        if not observed:
            continue
        available_at = daily_available(str(observed))
        available = parse_cutoff(available_at)
        value = row.get("adj_close")
        if value is None:
            value = row.get("close")
        if available > cutoff or value is None:
            continue
        admitted.append({
            "observed_at": iso(parse_cutoff(str(observed))),
            "available_at": iso(available),
            "value": float(value),
        })
    admitted.sort(key=lambda row: row["observed_at"])
    if not admitted:
        return {
            "status": "unavailable",
            "key": spec["key"],
            "ticker": spec["ticker"],
            "label": spec["label"],
            "kind": spec["kind"],
            "latest": macro_metric(None, "unavailable", spec["unit"]),
            "change_20": macro_metric(None, "unavailable", "basis_points" if spec["kind"] == "yield" else "percent"),
            "change_60": macro_metric(None, "unavailable", "basis_points" if spec["kind"] == "yield" else "percent"),
            "percentile": macro_metric(None, "unavailable", "percentile", window_sessions=percentile_window),
        }

    values = pd.Series([row["value"] for row in admitted], dtype=float)

    def change(window: int) -> dict[str, Any]:
        unit = "basis_points" if spec["kind"] == "yield" else "percent"
        if len(values) < window + 1:
            return macro_metric(None, "insufficient_history", unit, window_sessions=window)
        if spec["kind"] == "yield":
            value = float((values.iloc[-1] - values.iloc[-window - 1]) * 100)
        elif float(values.iloc[-window - 1]) == 0:
            return macro_metric(None, "unavailable", unit, window_sessions=window)
        else:
            value = float((values.iloc[-1] / values.iloc[-window - 1] - 1) * 100)
        return macro_metric(value, "available", unit, window_sessions=window)

    if len(values) < percentile_window:
        percentile = macro_metric(
            None,
            "insufficient_history",
            "percentile",
            window_sessions=percentile_window,
            observed_sessions=len(values),
        )
    else:
        sample = values.tail(percentile_window)
        rank = float(sample.rank(method="average", pct=True).iloc[-1] * 100)
        percentile = macro_metric(
            rank,
            "available",
            "percentile",
            window_sessions=percentile_window,
            observed_sessions=percentile_window,
        )
    latest = admitted[-1]
    return {
        "status": "available",
        "key": spec["key"],
        "ticker": spec["ticker"],
        "label": spec["label"],
        "kind": spec["kind"],
        "as_of": latest["observed_at"],
        "available_at": latest["available_at"],
        "history_sessions": len(admitted),
        "latest": macro_metric(latest["value"], "available", spec["unit"]),
        "change_20": change(20),
        "change_60": change(60),
        "percentile": percentile,
    }


def collect_macro_context(
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    history_loader: Callable[[str, str, str], pd.DataFrame] | None = None,
) -> None:
    cutoff = parse_cutoff(bundle["analysis_cutoff"])
    fetched_at = bundle["fetched_at"]
    specs = validate_macro_series(manifest.get("macro_series"))
    percentile_window = int(manifest.get("macro_percentile_window", 252))
    start = (cutoff - timedelta(days=550)).date().isoformat()
    end = (cutoff + timedelta(days=1)).date().isoformat()
    loader = history_loader or (
        lambda ticker, start_date, end_date: yf.Ticker(ticker).history(
            start=start_date,
            end=end_date,
            auto_adjust=False,
            actions=False,
        )
    )
    summaries: dict[str, Any] = {}
    incoming = []
    for spec in specs:
        frame, source_status = attempt(
            f"yfinance_macro:{spec['key']}",
            fetched_at,
            lambda spec=spec: loader(spec["ticker"], start, end),
        )
        if frame is None:
            summary = summarize_macro_history(pd.DataFrame(), spec, cutoff, percentile_window)
        else:
            summary = summarize_macro_history(frame, spec, cutoff, percentile_window)
        if source_status["status"] == "available" and summary["status"] != "available":
            source_status["status"] = summary["status"]
            source_status["error"] = "no completed macro observation at or before cutoff"
        bundle.setdefault("source_statuses", []).append(source_status)
        summaries[spec["key"]] = summary
        if summary["status"] != "available":
            continue
        source_url = f"https://finance.yahoo.com/quote/{quote(spec['ticker'], safe='')}/history"
        record = {
            "evidence_id": "macro-" + content_hash([spec["key"], summary])[:16],
            "source": "yfinance_macro",
            "source_url": source_url,
            "fetched_at": fetched_at,
            "observed_at": summary["as_of"],
            "available_at": summary["available_at"],
            "status": "available",
            "subject_id": spec["key"],
            "field": "macro_snapshot",
            "value": summary,
            "unit_or_currency": spec["unit"],
            "adjustment_basis": "raw_unadjusted",
        }
        if bundle.get("bundle_kind") == "screening":
            record.update({
                "evidence_strength": "medium",
                "evidence_kind": "analytical_input",
                "scope": "shared",
                "candidate_ids": [],
            })
        record["content_hash"] = content_hash(record)
        incoming.append(record)
    two_year = summaries.get("us_2y", {})
    ten_year = summaries.get("us_10y", {})
    if (
        two_year.get("status") == "available"
        and ten_year.get("status") == "available"
        and two_year.get("as_of") == ten_year.get("as_of")
    ):
        spread = float((ten_year["latest"]["value"] - two_year["latest"]["value"]) * 100)
        spread_changes = {}
        for field in ("change_20", "change_60"):
            short_change = two_year.get(field, {})
            long_change = ten_year.get(field, {})
            if short_change.get("status") == "available" and long_change.get("status") == "available":
                spread_changes[field] = macro_metric(
                    float(long_change["value"] - short_change["value"]),
                    "available",
                    "basis_points",
                    window_sessions=long_change.get("window_sessions"),
                )
            else:
                spread_changes[field] = macro_metric(
                    None,
                    "insufficient_history",
                    "basis_points",
                    window_sessions=long_change.get("window_sessions") or short_change.get("window_sessions"),
                )
        summaries["us_2s10s"] = {
            "status": "available",
            "key": "us_2s10s",
            "label": "US 2s10s Treasury spread",
            "kind": "spread",
            "as_of": ten_year["as_of"],
            "available_at": max(two_year["available_at"], ten_year["available_at"]),
            "latest": macro_metric(spread, "available", "basis_points"),
            **spread_changes,
            "derivation": "us_10y minus us_2y",
        }
    else:
        summaries["us_2s10s"] = {
            "status": "unavailable",
            "key": "us_2s10s",
            "label": "US 2s10s Treasury spread",
            "kind": "spread",
            "latest": macro_metric(None, "unavailable", "basis_points"),
            "change_20": macro_metric(None, "unavailable", "basis_points", window_sessions=20),
            "change_60": macro_metric(None, "unavailable", "basis_points", window_sessions=60),
            "reason": "requires same-date available us_2y and us_10y observations",
        }
    merge_records(bundle, incoming)
    requested_summaries = [summaries[spec["key"]] for spec in specs]
    available_count = sum(item.get("status") == "available" for item in requested_summaries)
    coverage = "available" if available_count == len(requested_summaries) else "partial" if available_count else "unavailable"
    bundle.setdefault("blocks", {})["macro_environment"] = {
        "status": coverage,
        "analysis_cutoff": cutoff.isoformat(),
        "percentile_window_sessions": percentile_window,
        "series": summaries,
        "interpretation_policy": "numeric context only; council roles infer the market regime",
    }


def refresh_macro_block_from_records(bundle: dict[str, Any]) -> None:
    if bundle.get("blocks", {}).get("macro_environment"):
        return
    summaries = {
        record["subject_id"]: record["value"]
        for record in bundle.get("records", [])
        if record.get("field") == "macro_snapshot" and record.get("status") == "available"
    }
    if not summaries:
        return
    bundle.setdefault("blocks", {})["macro_environment"] = {
        "status": "available",
        "analysis_cutoff": bundle["analysis_cutoff"],
        "percentile_window_sessions": next(iter(summaries.values())).get("percentile", {}).get("window_sessions"),
        "series": summaries,
        "interpretation_policy": "numeric context only; council roles infer the market regime",
    }


def news_body(item: dict[str, Any]) -> dict[str, Any]:
    content = item.get("content")
    return content if isinstance(content, dict) else item


def news_url(item: dict[str, Any]) -> str | None:
    body = news_body(item)
    canonical = body.get("canonicalUrl") or item.get("canonicalUrl")
    if isinstance(canonical, dict):
        return canonical.get("url")
    return canonical or body.get("link") or item.get("link")


def filter_news(items: list[dict[str, Any]], cutoff: datetime, historical: bool) -> tuple[list[dict[str, Any]], int]:
    admitted, quarantined = [], 0
    for item in items:
        body = news_body(item)
        provider = (
            body.get("providerPublishTime")
            or body.get("pubDate")
            or item.get("providerPublishTime")
            or item.get("pubDate")
        )
        if isinstance(provider, (int, float)):
            available = datetime.fromtimestamp(provider, timezone.utc)
        elif provider:
            try:
                available = datetime.fromisoformat(str(provider).replace("Z", "+00:00"))
            except ValueError:
                available = None
        else:
            available = None
        if available is None or available > cutoff:
            quarantined += 1
            continue
        item = dict(item)
        item["available_at"] = iso(available)
        admitted.append(item)
    return admitted, quarantined


def empty_bundle(manifest: dict[str, Any]) -> dict[str, Any]:
    cutoff = parse_cutoff(manifest["analysis_cutoff"])
    now = datetime.now(timezone.utc)
    if cutoff.astimezone(timezone.utc) > now + timedelta(minutes=5):
        raise ValueError("analysis_cutoff cannot be in the future")
    run_type = str(manifest.get("run_type") or "instrument")
    return {
        "schema_version": "1.0",
        "bundle_kind": run_type,
        "run_id": manifest.get("run_id"),
        "requested_ticker": manifest.get("requested_ticker"),
        "canonical_ticker": manifest.get("canonical_ticker") or manifest.get("requested_ticker"),
        "theme": manifest.get("theme") or manifest.get("comparison_label"),
        "market": manifest.get("market"),
        "analysis_cutoff": cutoff.isoformat(),
        "technical_percentile_window": int(manifest.get("technical_percentile_window", 252)),
        "historical": cutoff.date() < now.astimezone(cutoff.tzinfo).date(),
        "fetched_at": now.isoformat(),
        "source_statuses": [],
        "supplement_rejections": [],
        "ohlcv": [],
        "records": [],
        "blocks": {},
        "collection_policy": {
            "untrusted_content": True,
            "historical_current_only_rejected": cutoff.date() < now.astimezone(cutoff.tzinfo).date(),
        },
    }


def parse_record_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a timezone-aware RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{field} must be a timezone-aware RFC 3339 timestamp") from None
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def stable_identity(record: dict[str, Any]) -> str:
    return canonical_hash([
        record.get("source"),
        record.get("source_url"),
        record.get("subject_id"),
        record.get("field"),
        record.get("observed_at"),
        record.get("available_at"),
        record.get("value"),
    ])


def validate_supplement(
    payload: Any,
    cutoff: datetime,
    historical: bool,
    source_file: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise ValueError("supplement must be a JSON object with a records array")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, raw in enumerate(payload["records"]):
        try:
            if not isinstance(raw, dict):
                raise ValueError("record must be an object")
            record = dict(raw)
            for field in ("source", "subject_id", "field"):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    raise ValueError(f"{field} must be a non-empty string")
            if "value" not in record:
                raise ValueError("value is required")

            available = parse_record_time(record.get("available_at"), "available_at")
            parse_record_time(record.get("fetched_at"), "fetched_at")
            if available > cutoff:
                raise ValueError("available_at exceeds analysis_cutoff")
            observed = record.get("observed_at")
            if observed is not None:
                parse_record_time(observed, "observed_at")

            strength = record.get("evidence_strength")
            if strength not in EVIDENCE_STRENGTHS:
                raise ValueError("evidence_strength is invalid")
            kind = record.get("evidence_kind")
            if kind not in EVIDENCE_KINDS:
                raise ValueError("evidence_kind is invalid")
            scope = record.get("scope")
            if scope not in EVIDENCE_SCOPES:
                raise ValueError("scope is invalid")
            candidate_ids = record.get("candidate_ids")
            if not isinstance(candidate_ids, list) or not all(
                isinstance(item, str) and item.strip() for item in candidate_ids
            ):
                raise ValueError("candidate_ids must be an array of non-empty strings")
            if scope == "shared" and candidate_ids:
                raise ValueError("shared records must have empty candidate_ids")
            if scope == "candidate" and not candidate_ids:
                raise ValueError("candidate records require candidate_ids")

            url = record.get("source_url")
            if url is not None and (
                not isinstance(url, str) or not re.match(r"^https?://", url)
            ):
                raise ValueError("source_url must be an absolute HTTP(S) URL or null")
            if not url:
                if historical:
                    raise ValueError("historical supplemental evidence requires source_url")
                record["evidence_strength"] = "unverified"
                record["evidence_kind"] = "unverified_lead"

            record_status = record.get("status", "available")
            if record_status not in RECORD_STATUSES:
                raise ValueError("status is invalid")
            record["status"] = record_status
            record["observed_at"] = iso(parse_record_time(observed, "observed_at")) if observed else None
            record["available_at"] = iso(available)
            record["fetched_at"] = iso(parse_record_time(record["fetched_at"], "fetched_at"))
            record["candidate_ids"] = sorted(set(candidate_ids))
            record.setdefault("unit_or_currency", None)
            record.setdefault("adjustment_basis", "not_applicable")
            identity = stable_identity(record)
            record["evidence_id"] = record.get("evidence_id") or "web-" + identity[:16]
            record["identity_hash"] = identity
            record["content_hash"] = content_hash({
                key: value for key, value in record.items() if key != "content_hash"
            })
            accepted.append(record)
        except ValueError as exc:
            rejected.append({
                "source_file": source_file,
                "record_index": index,
                "reason": str(exc),
            })
    return accepted, rejected


def mark_conflicts(records: list[dict[str, Any]]) -> None:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for record in records:
        if record.get("status") not in {"available", "conflict"}:
            continue
        key = (
            record.get("subject_id"),
            record.get("field"),
            record.get("observed_at"),
            record.get("available_at"),
        )
        groups.setdefault(key, []).append(record)
    for group in groups.values():
        values = {
            canonical_hash(record.get("value"))
            for record in group
        }
        if len(values) > 1:
            for record in group:
                record["status"] = "conflict"
                record["content_hash"] = content_hash({
                    key: value for key, value in record.items() if key != "content_hash"
                })


def merge_records(bundle: dict[str, Any], incoming: list[dict[str, Any]]) -> int:
    seen = {
        record.get("identity_hash") or stable_identity(record)
        for record in bundle.get("records", [])
    }
    added = 0
    for record in incoming:
        identity = record.get("identity_hash") or stable_identity(record)
        if identity in seen:
            continue
        seen.add(identity)
        bundle.setdefault("records", []).append(record)
        added += 1
    mark_conflicts(bundle["records"])
    return added


def load_json_source(source: str | Path) -> Any:
    """Read JSON from a path or stdin when source is '-'."""
    if str(source) == "-":
        return json.load(sys.stdin)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def write_json_target(target: str | Path, value: Any) -> None:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n"
    if str(target) == "-":
        sys.stdout.write(rendered)
        return
    Path(target).write_text(rendered, encoding="utf-8")


def merge_supplement_payload(bundle: dict[str, Any], payload: Any, source_label: str) -> None:
    cutoff = parse_cutoff(bundle["analysis_cutoff"])
    accepted, rejected = validate_supplement(
        payload,
        cutoff,
        bool(bundle.get("historical")),
        source_label,
    )
    added = merge_records(bundle, accepted)
    bundle.setdefault("supplement_rejections", []).extend(rejected)
    source_name = "stdin" if source_label == "-" else Path(source_label).name
    bundle.setdefault("source_statuses", []).append(status(
        f"supplement:{source_name}",
        "available" if added else ("partial" if accepted else "unavailable"),
        bundle["fetched_at"],
        None if added else "no new valid records",
    ))
    bundle.setdefault("blocks", {})["supplemental_evidence_ids"] = [
        record["evidence_id"]
        for record in bundle.get("records", [])
        if record.get("evidence_kind") in EVIDENCE_KINDS
    ]


def merge_supplement_file(bundle: dict[str, Any], path: Path) -> None:
    merge_supplement_payload(bundle, load_json_source(path), str(path))


def inherit_parent_records(
    bundle: dict[str, Any],
    manifest: dict[str, Any],
    parent_path: Path,
    candidate_id: str,
    relevant_subject_ids: list[str],
) -> None:
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    if parent.get("bundle_kind") != "screening":
        raise ValueError("parent evidence must be a screening bundle")
    expected_bundle_hash = content_hash({
        key: value for key, value in parent.items() if key != "bundle_hash"
    })
    if parent.get("bundle_hash") != expected_bundle_hash:
        raise ValueError("parent evidence bundle_hash mismatch")
    expected_run = manifest.get("parent_screening_run_id")
    if not expected_run or parent.get("run_id") != expected_run:
        raise ValueError("parent_screening_run_id does not match parent evidence")
    expected_hash = manifest.get("parent_evidence_hash")
    actual_hash = canonical_hash(parent)
    if not expected_hash or expected_hash != actual_hash:
        raise ValueError("parent_evidence_hash does not match parent evidence")
    parent_manifest_path = parent_path.parent / "manifest.json"
    parent_state_path = parent_path.parent / "state.json"
    if not parent_manifest_path.exists() or not parent_state_path.exists():
        raise ValueError("parent manifest.json or state.json is missing")
    parent_manifest = json.loads(parent_manifest_path.read_text(encoding="utf-8"))
    parent_state = json.loads(parent_state_path.read_text(encoding="utf-8"))
    if (
        parent_manifest.get("run_type") != "screening"
        or parent_manifest.get("run_id") != expected_run
        or parent_manifest.get("evidence_hash") != actual_hash
        or parent_state.get("manifest_hash") != canonical_hash(parent_manifest)
        or parent_state.get("evidence_hash") != actual_hash
    ):
        raise ValueError("parent manifest or state is not linked to frozen evidence")
    if parent_state.get("lifecycle") not in {
        "councils_running", "comparison_ready", "complete",
    }:
        raise ValueError("parent screening run has not started finalist councils")
    if manifest.get("candidate_id") != candidate_id:
        raise ValueError("candidate_id does not match child manifest")
    manifest_subjects = manifest.get("relevant_subject_ids")
    if not isinstance(manifest_subjects, list) or sorted(set(manifest_subjects)) != sorted(set(relevant_subject_ids)):
        raise ValueError("relevant_subject_ids do not match child manifest")
    finalists_path = parent_path.parent / "finalists.json"
    if not finalists_path.exists():
        raise ValueError("parent finalists.json is missing")
    finalists_value = json.loads(finalists_path.read_text(encoding="utf-8"))
    if parent_state.get("finalists_hash") != canonical_hash(finalists_value):
        raise ValueError("parent finalists hash mismatch")
    finalists = [
        item for item in finalists_value.get("finalists", [])
        if item.get("candidate_id") == candidate_id
    ]
    if len(finalists) != 1:
        raise ValueError("candidate_id is not a unique registered finalist")
    finalist = finalists[0]
    child_requested = str(manifest.get("requested_ticker") or "").upper()
    child_canonical = str(manifest.get("canonical_ticker") or child_requested).upper()
    finalist_requested = str(finalist.get("requested_ticker") or "").upper()
    finalist_canonical = str(finalist.get("canonical_ticker") or finalist_requested).upper()
    if child_requested != finalist_requested or child_canonical != finalist_canonical:
        raise ValueError("child ticker does not match registered finalist")
    if manifest.get("market") != finalist.get("market"):
        raise ValueError("child market does not match registered finalist")
    if sorted(set(finalist.get("relevant_subject_ids", []))) != sorted(set(relevant_subject_ids)):
        raise ValueError("relevant_subject_ids do not match registered finalist")
    subjects = set(relevant_subject_ids)
    inherited = []
    cutoff = parse_cutoff(bundle["analysis_cutoff"])
    for record in parent.get("records", []):
        relevant = (
            record.get("scope") == "shared"
            or candidate_id in record.get("candidate_ids", [])
            or record.get("subject_id") in subjects
        )
        if not relevant:
            continue
        available = parse_record_time(record.get("available_at"), "available_at")
        if available > cutoff:
            continue
        inherited.append(dict(record))
    merge_records(bundle, inherited)
    parent_macro = parent.get("blocks", {}).get("macro_environment")
    if isinstance(parent_macro, dict):
        bundle.setdefault("blocks", {})["macro_environment"] = dict(parent_macro)
        inherited_macro_statuses = [
            dict(item) for item in parent.get("source_statuses", [])
            if str(item.get("source") or "").startswith("yfinance_macro:")
        ]
        existing_sources = {
            item.get("source") for item in bundle.get("source_statuses", [])
        }
        bundle.setdefault("source_statuses", []).extend(
            item for item in inherited_macro_statuses
            if item.get("source") not in existing_sources
        )
    bundle["parent_screening_run_id"] = expected_run
    bundle["parent_evidence_hash"] = expected_hash
    bundle["inherited_evidence_ids"] = [
        record.get("evidence_id") for record in inherited if record.get("evidence_id")
    ]


def collect(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("run_type") == "screening":
        return empty_bundle(manifest)
    requested = str(manifest["requested_ticker"])
    canonical = str(manifest.get("canonical_ticker") or requested)
    cutoff = parse_cutoff(manifest["analysis_cutoff"])
    now = datetime.now(timezone.utc)
    if cutoff.astimezone(timezone.utc) > now + timedelta(minutes=5):
        raise ValueError("analysis_cutoff cannot be in the future")
    historical = cutoff.astimezone(cutoff.tzinfo).date() < now.astimezone(cutoff.tzinfo).date()
    current_snapshot_eligible = now.astimezone(timezone.utc) <= cutoff.astimezone(timezone.utc)
    fetched_at = now.isoformat()
    ticker = yf.Ticker(canonical)

    start = (cutoff - timedelta(days=550)).date().isoformat()
    end = (cutoff + timedelta(days=1)).date().isoformat()
    history, history_status = attempt(
        "yfinance_ohlcv",
        fetched_at,
        lambda: frame_records(ticker.history(start=start, end=end, auto_adjust=False, actions=True)),
    )
    history = history or []
    ohlcv = []
    actions = []
    quarantined_bars = 0
    for row in history:
        price = {
            "date": row.get("date"),
            "available_at": daily_available(row.get("date")),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "adj_close": row.get("adj_close", row.get("close")),
            "volume": row.get("volume"),
        }
        available_at = datetime.fromisoformat(str(price["available_at"]).replace("Z", "+00:00"))
        if available_at > cutoff:
            quarantined_bars += 1
            continue
        ohlcv.append(price)
        if row.get("dividends") or row.get("stock_splits"):
            actions.append({
                "date": row.get("date"),
                "dividends": row.get("dividends"),
                "stock_splits": row.get("stock_splits"),
            })
    history_status["quarantined_count"] = quarantined_bars

    raw_identity, identity_status = attempt("yfinance_identity", fetched_at, lambda: ticker.info)
    raw_identity = raw_identity or {"symbol": canonical}
    if (historical or not current_snapshot_eligible) and identity_status["status"] == "available":
        identity_status["status"] = "quarantined"
        identity_status["error"] = "current-only identity was not available at analysis_cutoff"
    identity = raw_identity if current_snapshot_eligible and not historical else {"symbol": canonical}

    raw_news, news_status = attempt("yfinance_news", fetched_at, lambda: ticker.news)
    news, quarantined_news = filter_news(raw_news or [], cutoff, historical)
    if not news and news_status["status"] == "available":
        news_status["status"] = "historical_unavailable" if historical else "unavailable"
    news_status["quarantined_count"] = quarantined_news

    source_statuses = [history_status, identity_status, news_status]
    blocks: dict[str, Any] = {
        "identity": identity,
        "ticker_news": news,
        "corporate_actions": actions,
    }

    if historical:
        for name in ("global_news", "fundamentals"):
            source_statuses.append(status(name, "historical_unavailable", fetched_at, "current-only or no verified vintage"))
        blocks.update({
            "global_news": [],
            "fundamentals": None,
        })
    else:
        raw_global_news, global_news_status = attempt(
            "yfinance_global_news",
            fetched_at,
            lambda: yf.Search(
                "global markets",
                max_results=10,
                news_count=10,
                enable_fuzzy_query=False,
            ).news,
        )
        global_news, quarantined_global = filter_news(raw_global_news or [], cutoff, False)
        if not global_news and global_news_status["status"] == "available":
            global_news_status["status"] = "unavailable"
            global_news_status["error"] = "no eligible dated results"
        global_news_status["quarantined_count"] = quarantined_global
        if current_snapshot_eligible:
            fundamentals, fundamentals_status = attempt(
                "yfinance_fundamentals",
                fetched_at,
                lambda: {
                    "overview": identity,
                    "income_statement": frame_records(ticker.income_stmt, "line_item"),
                    "balance_sheet": frame_records(ticker.balance_sheet, "line_item"),
                    "cash_flow": frame_records(ticker.cashflow, "line_item"),
                    "insider_transactions": frame_records(ticker.insider_transactions, "row"),
                },
            )
        else:
            fundamentals = None
            fundamentals_status = status(
                "yfinance_fundamentals",
                "quarantined",
                fetched_at,
                "current-only fundamentals were not available at analysis_cutoff",
            )
        source_statuses.extend([
            global_news_status,
            fundamentals_status,
        ])
        blocks.update({
            "global_news": global_news,
            "fundamentals": fundamentals,
        })

    evidence_records = []
    for row in ohlcv:
        for field in ("open", "high", "low", "close", "adj_close", "volume"):
            if row.get(field) is None:
                continue
            evidence_id = "yf-" + content_hash([canonical, row["date"], field, row[field]])[:16]
            evidence_records.append({
                "evidence_id": evidence_id,
                "source": "yfinance",
                "source_url": f"https://finance.yahoo.com/quote/{canonical}/history",
                "fetched_at": fetched_at,
                "observed_at": row["date"],
                "available_at": row["available_at"],
                "status": history_status["status"],
                "subject_id": canonical,
                "field": field,
                "value": row[field],
                "unit_or_currency": identity.get("currency") if field != "volume" else "shares",
                "adjustment_basis": "adjusted_total_return" if field == "adj_close" else "raw_unadjusted",
            })

    def append_record(
        source: str,
        field: str,
        value: Any,
        observed_at: str | None,
        available_at: str | None,
        record_status: str = "available",
        source_url: str | None = None,
    ) -> None:
        evidence_id = source[:8] + "-" + content_hash([canonical, field, observed_at, value])[:16]
        evidence_records.append({
            "evidence_id": evidence_id,
            "source": source,
            "source_url": source_url,
            "fetched_at": fetched_at,
            "observed_at": observed_at,
            "available_at": available_at,
            "status": record_status,
            "subject_id": canonical,
            "field": field,
            "value": value,
            "unit_or_currency": None,
            "adjustment_basis": "not_applicable",
        })

    if not historical and current_snapshot_eligible:
        append_record(
            "yfinance_identity",
            "instrument_identity",
            identity,
            None,
            fetched_at,
            identity_status["status"],
            f"https://finance.yahoo.com/quote/{canonical}",
        )
    for item in news:
        append_record(
            "yfinance_news",
            "ticker_news_item",
            item,
            item.get("available_at"),
            item.get("available_at"),
            "available",
            news_url(item),
        )
    for item in blocks.get("global_news", []):
        append_record(
            "yfinance_global_news",
            "global_news_item",
            item,
            item.get("available_at"),
            item.get("available_at"),
            "available",
            news_url(item),
        )
    if not historical and current_snapshot_eligible:
        for field, value in (blocks.get("fundamentals") or {}).items():
            if value not in (None, [], {}):
                append_record(
                    "yfinance_fundamentals",
                    field,
                    value,
                    None,
                    fetched_at,
                )
    for record in evidence_records:
        record["content_hash"] = content_hash(record)

    return {
        "schema_version": "1.0",
        "bundle_kind": "instrument",
        "run_id": manifest.get("run_id"),
        "requested_ticker": requested,
        "canonical_ticker": canonical,
        "analysis_cutoff": cutoff.isoformat(),
        "technical_percentile_window": int(manifest.get("technical_percentile_window", 252)),
        "historical": historical,
        "fetched_at": fetched_at,
        "source_statuses": source_statuses,
        "supplement_rejections": [],
        "ohlcv": ohlcv,
        "records": evidence_records,
        "blocks": blocks,
        "collection_policy": {
            "untrusted_content": True,
            "vendor_end_date_exclusive": True,
            "historical_current_only_rejected": historical,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="Manifest JSON path or - for stdin")
    parser.add_argument("--output", required=True, help="Evidence JSON path or - for stdout")
    parser.add_argument("--fixture", help="Copy an offline frozen fixture path or - for stdin instead of networking")
    parser.add_argument("--supplement", action="append", default=[], help="Supplemental evidence JSON path or - for stdin; repeatable")
    parser.add_argument("--supplement-only", action="store_true", help="Skip Yahoo collection for screening runs")
    parser.add_argument("--inherit-parent-evidence", help="Frozen parent screening evidence bundle")
    parser.add_argument("--candidate-id", help="Registered finalist candidate ID")
    parser.add_argument("--relevant-subject-id", action="append", default=[])
    args = parser.parse_args()
    if sum(source == "-" for source in [args.manifest, args.fixture, *args.supplement] if source) > 1:
        raise ValueError("stdin may be used by only one JSON input")
    manifest = load_json_source(args.manifest)
    if args.fixture:
        result = load_json_source(args.fixture)
        result.setdefault("fixture", True)
    elif args.supplement_only:
        if manifest.get("run_type") != "screening":
            raise ValueError("--supplement-only requires a screening manifest")
        result = empty_bundle(manifest)
    else:
        result = collect(manifest)
    result.setdefault("bundle_kind", manifest.get("run_type") or "instrument")
    result.setdefault("run_id", manifest.get("run_id"))
    result.setdefault("analysis_cutoff", manifest["analysis_cutoff"])
    result.setdefault("technical_percentile_window", int(manifest.get("technical_percentile_window", 252)))
    result.setdefault("historical", False)
    result.setdefault("fetched_at", datetime.now(timezone.utc).isoformat())
    result.setdefault("source_statuses", [])
    result.setdefault("supplement_rejections", [])
    result.setdefault("records", [])
    result.setdefault("ohlcv", [])
    result.setdefault("blocks", {})
    if (
        not args.fixture
        and not args.inherit_parent_evidence
        and manifest.get("macro_context_enabled", True)
    ):
        collect_macro_context(result, manifest)
    if args.inherit_parent_evidence:
        if not args.candidate_id:
            raise ValueError("--candidate-id is required with --inherit-parent-evidence")
        inherit_parent_records(
            result,
            manifest,
            Path(args.inherit_parent_evidence),
            args.candidate_id,
            args.relevant_subject_id,
        )
    for supplement in args.supplement:
        if supplement == "-":
            merge_supplement_payload(result, load_json_source("-"), "-")
        else:
            merge_supplement_file(result, Path(supplement))
    refresh_macro_block_from_records(result)
    result["bundle_hash"] = content_hash({k: v for k, v in result.items() if k != "bundle_hash"})
    write_json_target(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
