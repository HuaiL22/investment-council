#!/usr/bin/env python3
"""Calculate technical indicators and reconcile the effective market snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CATALOG = {
    "sma_50", "sma_200", "ema_10", "macd", "rsi_14",
    "bollinger", "atr_14", "vwma_20",
}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def time_key(value: Any) -> str:
    return pd.to_datetime(value, utc=True).isoformat()


def reconcile(payload: dict[str, Any], cutoff: str, secondary: float | None) -> dict[str, Any]:
    cutoff_dt = parse_time(cutoff)
    eligible = []
    for row in payload.get("ohlcv", []):
        date = row.get("date")
        if not date:
            continue
        row_dt = pd.to_datetime(date, utc=True).to_pydatetime()
        available = row.get("available_at")
        available_dt = parse_time(available) if available else row_dt + timedelta(days=1)
        if available_dt <= cutoff_dt:
            eligible.append((row_dt, row))
    if not eligible:
        return {"status": "unavailable", "error": "no completed row at or before cutoff"}
    row_dt, row = max(eligible, key=lambda item: item[0])
    canonical = float(row["close"])
    tolerance = max(1e-8, abs(canonical) * 1e-6)
    status = "available"
    conflict = None
    if secondary is not None and abs(canonical - secondary) > tolerance:
        status = "conflict"
        conflict = {
            "canonical": canonical,
            "secondary": secondary,
            "tolerance": tolerance,
        }
    return {
        "status": status,
        "effective_date": row_dt.isoformat(),
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "close": canonical,
        "volume": row.get("volume"),
        "adjustment_basis": "raw_unadjusted",
        "tolerance": tolerance,
        "conflict": conflict,
    }


def wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def metric(value: Any, status: str, *, unit: str | None = None) -> dict[str, Any]:
    output = {"status": status, "value": None if value is None or pd.isna(value) else value}
    if unit:
        output["unit"] = unit
    return output


def percentile_rank(series: pd.Series, window: int) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if len(values) < window:
        return {
            **metric(None, "insufficient_history", unit="percentile"),
            "window_sessions": window,
            "observed_sessions": len(values),
        }
    sample = values.tail(window)
    value = float(sample.rank(method="average", pct=True).iloc[-1] * 100)
    return {
        **metric(value, "available", unit="percentile"),
        "window_sessions": window,
        "observed_sessions": window,
    }


def latest_metric(series: pd.Series, unit: str) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return metric(None, "insufficient_history", unit=unit)
    return metric(float(values.iloc[-1]), "available", unit=unit)


def slope_metric(series: pd.Series, window: int = 20) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if len(values) < window + 1 or float(values.iloc[-window - 1]) == 0:
        return {
            **metric(None, "insufficient_history", unit="percent"),
            "window_sessions": window,
        }
    value = (float(values.iloc[-1]) / float(values.iloc[-window - 1]) - 1) * 100
    return {**metric(value, "available", unit="percent"), "window_sessions": window}


def calculate(frame: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    unknown = sorted(set(selected) - CATALOG)
    if unknown:
        raise ValueError("unsupported indicators: " + ", ".join(unknown))
    if len(selected) > 8:
        raise ValueError("select at most eight indicator families")
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("OHLCV missing: " + ", ".join(sorted(missing)))
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], utc=True)
    out = out.sort_values("date").drop_duplicates("date")
    numeric = ["open", "high", "low", "close", "volume"]
    out[numeric] = out[numeric].apply(pd.to_numeric, errors="coerce")
    close = out["close"]

    if "sma_50" in selected:
        out["sma_50"] = close.rolling(50, min_periods=50).mean()
    if "sma_200" in selected:
        out["sma_200"] = close.rolling(200, min_periods=200).mean()
    if "ema_10" in selected:
        out["ema_10"] = close.ewm(span=10, adjust=False, min_periods=10).mean()
    if "macd" in selected:
        fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
        slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
        out["macd"] = fast - slow
        out["macd_signal"] = out["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
        out["macd_hist"] = out["macd"] - out["macd_signal"]
    if "rsi_14" in selected:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        average_gain = wilder(gain, 14)
        average_loss = wilder(loss, 14)
        rs = average_gain / average_loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)
        rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100.0)
        rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50.0)
        out["rsi_14"] = rsi
    if "bollinger" in selected:
        out["boll_mid"] = close.rolling(20, min_periods=20).mean()
        std = close.rolling(20, min_periods=20).std(ddof=0)
        out["boll_upper"] = out["boll_mid"] + 2 * std
        out["boll_lower"] = out["boll_mid"] - 2 * std
    if "atr_14" in selected:
        previous = close.shift(1)
        true_range = pd.concat([
            out["high"] - out["low"],
            (out["high"] - previous).abs(),
            (out["low"] - previous).abs(),
        ], axis=1).max(axis=1)
        out["atr_14"] = wilder(true_range, 14)
    if "vwma_20" in selected:
        pv = close * out["volume"]
        denominator = out["volume"].rolling(20, min_periods=20).sum().replace(0, np.nan)
        out["vwma_20"] = pv.rolling(20, min_periods=20).sum() / denominator
    return out


def build_snapshot(
    frame: pd.DataFrame,
    calculated: pd.DataFrame | None = None,
    percentile_window: int = 252,
) -> dict[str, Any]:
    if percentile_window < 20:
        raise ValueError("percentile_window must be at least 20 sessions")
    result = calculated if calculated is not None else calculate(frame, sorted(CATALOG))
    if result.empty:
        return {
            "status": "unavailable",
            "as_of": None,
            "price_basis": "raw_close",
            "percentile_window_sessions": percentile_window,
            "metrics": {},
            "trend_regime": {"status": "unavailable", "value": None},
        }
    result = result.sort_values("date").reset_index(drop=True)
    close = pd.to_numeric(result["close"], errors="coerce")
    rsi = result.get("rsi_14", pd.Series(dtype=float))
    atr = pd.to_numeric(result.get("atr_14", pd.Series(dtype=float)), errors="coerce")
    atr_pct = atr / close.replace(0, np.nan) * 100
    sma_50 = result.get("sma_50", pd.Series(dtype=float))
    sma_200 = result.get("sma_200", pd.Series(dtype=float))
    metrics = {
        "close": latest_metric(close, "price"),
        "rsi_14": latest_metric(rsi, "index"),
        "price_percentile": percentile_rank(close, percentile_window),
        "rsi_percentile": percentile_rank(rsi, percentile_window),
        "atr_14_pct": latest_metric(atr_pct, "percent"),
        "atr_percentile": percentile_rank(atr_pct, percentile_window),
        "sma_50_slope_20": slope_metric(sma_50),
        "sma_200_slope_20": slope_metric(sma_200),
    }

    required = [
        metrics["close"], metrics["sma_50_slope_20"], metrics["sma_200_slope_20"],
    ]
    latest_close = metrics["close"].get("value")
    latest_sma_50 = latest_metric(sma_50, "price")
    latest_sma_200 = latest_metric(sma_200, "price")
    metrics["sma_50"] = latest_sma_50
    metrics["sma_200"] = latest_sma_200
    required.extend([latest_sma_50, latest_sma_200])
    if any(item.get("status") != "available" for item in required):
        regime = {"status": "insufficient_history", "value": None}
    else:
        s50 = float(latest_sma_50["value"])
        s200 = float(latest_sma_200["value"])
        s50_slope = float(metrics["sma_50_slope_20"]["value"])
        s200_slope = float(metrics["sma_200_slope_20"]["value"])
        if latest_close > s50 > s200 and s50_slope > 0 and s200_slope >= 0:
            value = "uptrend"
        elif latest_close > s50 and s50_slope > 0:
            value = "recovery"
        elif latest_close < s50 and s50_slope < 0:
            value = "deteriorating"
        else:
            value = "range"
        regime = {"status": "available", "value": value}

    return {
        "status": "available",
        "as_of": pd.to_datetime(result.iloc[-1]["date"], utc=True).isoformat(),
        "price_basis": "raw_close",
        "percentile_window_sessions": percentile_window,
        "metrics": metrics,
        "trend_regime": regime,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON path with ohlcv array or - for stdin")
    parser.add_argument("--output", required=True, help="Output JSON path or - for stdout")
    parser.add_argument("--indicators", default="sma_50,sma_200,ema_10,macd,rsi_14,bollinger,atr_14,vwma_20")
    parser.add_argument("--cutoff", help="Override the bundle analysis cutoff")
    parser.add_argument("--secondary-close", type=float)
    parser.add_argument("--percentile-window", type=int)
    args = parser.parse_args()
    payload = json.load(sys.stdin) if args.input == "-" else json.loads(
        Path(args.input).read_text(encoding="utf-8")
    )
    rows = payload.get("ohlcv", payload)
    selected = [item.strip() for item in args.indicators.split(",") if item.strip()]
    percentile_window = args.percentile_window or (
        payload.get("technical_percentile_window", 252) if isinstance(payload, dict) else 252
    )
    result = calculate(pd.DataFrame(rows), selected)
    indicator_columns = [c for c in result.columns if c not in {"open", "high", "low", "close", "volume"}]
    records = result[indicator_columns].replace({np.nan: None}).to_dict(orient="records")
    technical = {
        "status": "available" if records else "unavailable",
        "selected": selected,
        "formula_version": "1.0",
        "adjustment_basis": "raw_close",
        "observation_count": len(result),
        "series": records,
        "snapshot": build_snapshot(result, result, percentile_window),
    }
    if not isinstance(payload, dict) or "ohlcv" not in payload:
        output = technical
    else:
        output = dict(payload)
        output.setdefault("blocks", {})["technical"] = technical
        output["records"] = [
            record for record in output.get("records", [])
            if record.get("source") != "local_technical"
        ]
        availability = {
            time_key(row.get("date")): row.get("available_at") or row.get("date")
            for row in payload.get("ohlcv", [])
        }
        subject = payload.get("canonical_ticker") or payload.get("requested_ticker")
        for row in records:
            observed = time_key(row.get("date"))
            for field, value in row.items():
                if field == "date" or value is None:
                    continue
                seed = json.dumps([subject, observed, field, value], sort_keys=True, default=str).encode()
                evidence_id = "tech-" + hashlib.sha256(seed).hexdigest()[:16]
                record = {
                    "evidence_id": evidence_id,
                    "source": "local_technical",
                    "source_url": None,
                    "fetched_at": payload.get("fetched_at"),
                    "observed_at": observed,
                    "available_at": availability.get(time_key(row.get("date"))),
                    "status": "available",
                    "subject_id": subject,
                    "field": field,
                    "value": value,
                    "unit_or_currency": "index" if field == "rsi_14" else "price",
                    "adjustment_basis": "raw_close",
                }
                record["content_hash"] = hashlib.sha256(
                    json.dumps(record, ensure_ascii=False, sort_keys=True, default=str).encode()
                ).hexdigest()
                output["records"].append(record)
        snapshot = technical["snapshot"]
        if snapshot.get("as_of"):
            summary = {
                "evidence_id": "tech-" + hashlib.sha256(
                    json.dumps([subject, "technical_snapshot", snapshot], sort_keys=True, default=str).encode()
                ).hexdigest()[:16],
                "source": "local_technical",
                "source_url": None,
                "fetched_at": payload.get("fetched_at"),
                "observed_at": snapshot["as_of"],
                "available_at": availability.get(time_key(snapshot["as_of"])),
                "status": "available",
                "subject_id": subject,
                "field": "technical_snapshot",
                "value": snapshot,
                "unit_or_currency": None,
                "adjustment_basis": "raw_close",
            }
            summary["content_hash"] = hashlib.sha256(
                json.dumps(summary, ensure_ascii=False, sort_keys=True, default=str).encode()
            ).hexdigest()
            output["records"].append(summary)
        cutoff = args.cutoff or payload.get("analysis_cutoff")
        snapshot = reconcile(output, cutoff, args.secondary_close) if cutoff else None
        if snapshot is not None:
            output.setdefault("blocks", {})["market_snapshot"] = snapshot
        output.pop("bundle_hash", None)
        output["bundle_hash"] = hashlib.sha256(
            json.dumps(output, ensure_ascii=False, sort_keys=True, default=str).encode()
        ).hexdigest()
    rendered = json.dumps(output, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output == "-":
        sys.stdout.write(rendered)
    else:
        Path(args.output).write_text(rendered, encoding="utf-8")
    if isinstance(payload, dict) and "ohlcv" in payload:
        snapshot = output.get("blocks", {}).get("market_snapshot")
        if snapshot and snapshot.get("status") == "unavailable":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
