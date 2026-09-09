#!/usr/bin/env python3
"""Persist, resolve, and select Investment Council decision lessons."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
INTENTS = (
    "open_long", "add_long", "hold", "reduce_long", "close_long",
    "open_short", "add_short", "reduce_short", "close_short", "no_trade",
)
ACTION_SIGN = {
    "open_long": 1, "add_long": 1, "reduce_short": 1, "close_short": 1,
    "open_short": -1, "add_short": -1, "reduce_long": -1, "close_long": -1,
    "hold": 0, "no_trade": 0,
}


def load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("memory file must contain a JSON array")
    return value


def atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def common_closes(prices: dict[str, Any], ticker: str, benchmark: str, start: str) -> list[tuple[str, float, float]]:
    asset = {row["date"][:10]: float(row["adj_close"]) for row in prices[ticker] if row["date"][:10] >= start}
    base = {row["date"][:10]: float(row["adj_close"]) for row in prices[benchmark] if row["date"][:10] >= start}
    return [(day, asset[day], base[day]) for day in sorted(set(asset) & set(base))]


def add_entry(args: argparse.Namespace) -> int:
    path = Path(args.memory).expanduser()
    entries = load(path)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    run_id = manifest["run_id"]
    if any(item.get("run_id") == run_id for item in entries):
        print(json.dumps({"status": "exists", "run_id": run_id}))
        return 0

    report_hash = None
    if args.report:
        report_hash = hashlib.sha256(Path(args.report).read_bytes()).hexdigest()
    entry = {
        "run_id": run_id,
        "status": "pending",
        "ticker": manifest["canonical_ticker"],
        "benchmark": manifest["benchmark_ticker"],
        "analysis_date": manifest["requested_analysis_date"],
        "rating": args.rating,
        "trade_intent": args.trade_intent,
        "thesis": args.thesis,
        "neutral_band": float(args.neutral_band),
        "manifest_hash": manifest.get("resume_signature"),
        "evidence_hash": manifest.get("evidence_hash"),
        "report_hash": report_hash,
        "return_basis": "adjusted_close_total_return",
    }
    entries.append(entry)
    atomic_write(path, entries)
    print(json.dumps({"status": "added", "run_id": run_id}))
    return 0


def resolve_entry(args: argparse.Namespace) -> int:
    path = Path(args.memory).expanduser()
    entries = load(path)
    prices = json.loads(Path(args.prices).read_text(encoding="utf-8"))
    changed = 0
    matched = False
    for item in entries:
        if item.get("run_id") != args.run_id:
            continue
        matched = True
        if item.get("status") not in {"pending", "partial"}:
            continue
        closes = common_closes(prices, item["ticker"], item["benchmark"], item["analysis_date"])
        if len(closes) < 2:
            continue
        actual_count = min(len(closes), 6)
        selected = closes[:actual_count]
        entry_day, asset_start, benchmark_start = selected[0]
        exit_day, asset_end, benchmark_end = selected[-1]
        asset_return = asset_end / asset_start - 1
        benchmark_return = benchmark_end / benchmark_start - 1
        raw_alpha = asset_return - benchmark_return
        sign = ACTION_SIGN[item["trade_intent"]]
        decision_return = sign * asset_return
        decision_alpha = sign * raw_alpha
        neutral_band = float(item.get("neutral_band", 0.02))
        rating = item["rating"]
        rating_correct = (
            raw_alpha > 0 if rating in {"Buy", "Overweight"}
            else raw_alpha < 0 if rating in {"Sell", "Underweight"}
            else abs(raw_alpha) <= neutral_band
        )
        intent_correct = decision_alpha > 0 if sign else abs(raw_alpha) <= neutral_band
        partial = actual_count < 6
        item.update({
            "status": "partial" if partial else "resolved",
            "partial_horizon": partial,
            "entry_date": entry_day,
            "exit_date": exit_day,
            "target_close_count": 6,
            "actual_close_count": actual_count,
            "target_intervals": 5,
            "actual_intervals": actual_count - 1,
            "elapsed_calendar_days": (date.fromisoformat(exit_day) - date.fromisoformat(entry_day)).days,
            "asset_return": asset_return,
            "benchmark_return": benchmark_return,
            "raw_alpha": raw_alpha,
            "action_sign": sign,
            "decision_return": decision_return,
            "decision_alpha": decision_alpha,
            "rating_correct": rating_correct,
            "trade_intent_correct": intent_correct,
            "reflection": args.reflection,
            "resolved_at": datetime.now().astimezone().isoformat(),
        })
        changed += 1
    if not matched:
        raise ValueError(f"run_id not found in memory: {args.run_id}")
    atomic_write(path, entries)
    print(json.dumps({"updated": changed}))
    return 0


def select_lessons(args: argparse.Namespace) -> int:
    entries = [item for item in load(Path(args.memory).expanduser()) if item.get("status") == "resolved"]
    entries.sort(key=lambda item: item.get("resolved_at", ""), reverse=True)
    same = [item for item in entries if item["ticker"] == args.ticker][:5]
    cross = [item for item in entries if item["ticker"] != args.ticker][:3]
    print(json.dumps({"same_ticker": same, "cross_ticker": cross}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("--memory", default="~/.investment-council/memory/decisions.json")
    add.add_argument("--manifest", required=True)
    add.add_argument("--rating", choices=RATINGS, required=True)
    add.add_argument("--trade-intent", choices=INTENTS, required=True)
    add.add_argument("--thesis", required=True)
    add.add_argument("--report")
    add.add_argument("--neutral-band", type=float, default=0.02)
    add.set_defaults(func=add_entry)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--memory", default="~/.investment-council/memory/decisions.json")
    resolve.add_argument("--run-id", required=True)
    resolve.add_argument("--prices", required=True)
    resolve.add_argument("--reflection", required=True, help="Codex-authored 2-4 sentence reflection")
    resolve.set_defaults(func=resolve_entry)
    select = sub.add_parser("select")
    select.add_argument("--memory", default="~/.investment-council/memory/decisions.json")
    select.add_argument("--ticker", required=True)
    select.set_defaults(func=select_lessons)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
