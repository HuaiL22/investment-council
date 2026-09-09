#!/usr/bin/env python3
"""Audit a mapped security universe without making investment judgments."""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi
import pandas as pd
import yfinance as yf

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import technical_analysis  # noqa: E402


SCHEMA_VERSION = "1.1"
LEGACY_SCHEMA_VERSIONS = {"1.0"}
ROUTE_TYPES = {"direct", "indirect"}
SEC_MAPPING_URL = "https://www.sec.gov/files/company_tickers_exchange.json?output=1"
SUPPORTED_LIQUIDITY_METRIC = "median_turnover"
SUPPORTED_WINDOWS = {20, 60}
TICKER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-^=]{0,31}$")
NETWORK_TIMEOUT_SECONDS = 20
MAX_RETRY_AFTER_SECONDS = 2.0


class ContractError(ValueError):
    """Raised when the audit input contract is invalid."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a timezone-aware RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ContractError(f"{field} must be a timezone-aware RFC 3339 timestamp") from None
    if parsed.tzinfo is None:
        raise ContractError(f"{field} must be timezone-aware")
    return parsed


def clean_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value.strip()


def normalize_name(value: str) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
    suffixes = {"inc", "incorporated", "corp", "corporation", "company", "co", "ltd", "limited", "plc"}
    return " ".join(word for word in words if word not in suffixes)


def normalize_identifier(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    return text.lstrip("0") or "0"


def validate_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{field} must be a non-empty array")
    cleaned = [clean_text(item, field) for item in value]
    if len({item.casefold() for item in cleaned}) != len(cleaned):
        raise ContractError(f"{field} must not contain duplicates")
    return cleaned


def validate_payload(payload: Any, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContractError("input must be a JSON object")
    input_schema_version = payload.get("schema_version")
    if input_schema_version not in LEGACY_SCHEMA_VERSIONS | {SCHEMA_VERSION}:
        accepted = ", ".join(sorted(LEGACY_SCHEMA_VERSIONS | {SCHEMA_VERSION}))
        raise ContractError(f"schema_version must be one of: {accepted}")
    legacy_input = input_schema_version in LEGACY_SCHEMA_VERSIONS
    cutoff = parse_time(payload.get("analysis_cutoff"), "analysis_cutoff")
    current = now or utc_now()
    if cutoff.astimezone(timezone.utc) > current.astimezone(timezone.utc) + timedelta(minutes=5):
        raise ContractError("analysis_cutoff cannot be in the future")

    boundary = payload.get("market_boundary")
    if not isinstance(boundary, dict):
        raise ContractError("market_boundary must be an object")
    boundary = {
        "markets": validate_string_list(boundary.get("markets"), "market_boundary.markets"),
        "venues": validate_string_list(boundary.get("venues"), "market_boundary.venues"),
        "security_types": validate_string_list(
            boundary.get("security_types"), "market_boundary.security_types"
        ),
    }

    benchmark = payload.get("benchmark")
    if benchmark is not None:
        if not isinstance(benchmark, dict):
            raise ContractError("benchmark must be an object or null")
        benchmark = {"ticker": clean_text(benchmark.get("ticker"), "benchmark.ticker").upper()}
        if not TICKER_PATTERN.fullmatch(benchmark["ticker"]):
            raise ContractError("benchmark.ticker contains unsupported characters")

    rule = payload.get("liquidity_rule")
    if rule is not None:
        if not isinstance(rule, dict):
            raise ContractError("liquidity_rule must be an object or null")
        if rule.get("metric") != SUPPORTED_LIQUIDITY_METRIC:
            raise ContractError(f"liquidity_rule.metric must be {SUPPORTED_LIQUIDITY_METRIC}")
        if rule.get("window_sessions") not in SUPPORTED_WINDOWS:
            raise ContractError("liquidity_rule.window_sessions must be 20 or 60")
        if rule.get("operator") != "gte":
            raise ContractError("liquidity_rule.operator must be gte")
        threshold = rule.get("threshold")
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 0:
            raise ContractError("liquidity_rule.threshold must be a non-negative number")
        rule = {
            "metric": SUPPORTED_LIQUIDITY_METRIC,
            "window_sessions": int(rule["window_sessions"]),
            "operator": "gte",
            "threshold": float(threshold),
            "currency": clean_text(rule.get("currency"), "liquidity_rule.currency").upper(),
        }

    raw_securities = payload.get("securities")
    if not isinstance(raw_securities, list) or not raw_securities:
        raise ContractError("securities must be a non-empty array")
    securities = []
    route_ids: set[str] = set()
    for index, raw in enumerate(raw_securities):
        if not isinstance(raw, dict):
            raise ContractError(f"securities[{index}] must be an object")
        if legacy_input:
            candidate_id = clean_text(
                raw.get("candidate_id"), f"securities[{index}].candidate_id"
            )
            route_id = candidate_id
            route_type = "direct"
            issuer_entity_id = candidate_id
        else:
            candidate_id = None
            route_id = clean_text(raw.get("route_id"), f"securities[{index}].route_id")
            route_type = clean_text(
                raw.get("route_type"), f"securities[{index}].route_type"
            ).casefold()
            if route_type not in ROUTE_TYPES:
                raise ContractError(
                    f"securities[{index}].route_type must be direct or indirect"
                )
            raw_entity_id = raw.get("issuer_entity_id")
            if route_type == "direct":
                issuer_entity_id = clean_text(
                    raw_entity_id, f"securities[{index}].issuer_entity_id"
                )
            elif raw_entity_id is None or raw_entity_id == "":
                issuer_entity_id = None
            else:
                issuer_entity_id = clean_text(
                    raw_entity_id, f"securities[{index}].issuer_entity_id"
                )
        if route_id in route_ids:
            label = "candidate_id" if legacy_input else "route_id"
            raise ContractError(f"duplicate {label}: {route_id}")
        route_ids.add(route_id)
        ticker = clean_text(raw.get("ticker"), f"securities[{index}].ticker").upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            raise ContractError(f"securities[{index}].ticker contains unsupported characters")
        security = {
            "route_id": route_id,
            "route_type": route_type,
            "issuer_entity_id": issuer_entity_id,
            "legacy_candidate_id": candidate_id,
            "ticker": ticker,
            "issuer_name": clean_text(raw.get("issuer_name"), f"securities[{index}].issuer_name"),
            "expected_venue": clean_text(
                raw.get("expected_venue"), f"securities[{index}].expected_venue"
            ),
            "expected_security_type": clean_text(
                raw.get("expected_security_type"), f"securities[{index}].expected_security_type"
            ),
            "expected_official_identifier": normalize_identifier(
                raw.get("expected_official_identifier")
            ),
            "quote_currency": str(raw.get("quote_currency") or "").strip().upper() or None,
            "proposed_category": str(raw.get("proposed_category") or "").strip() or None,
        }
        securities.append(security)

    return {
        "schema_version": SCHEMA_VERSION,
        "input_schema_version": input_schema_version,
        "analysis_cutoff": cutoff,
        "market_boundary": boundary,
        "benchmark": benchmark,
        "liquidity_rule": rule,
        "securities": securities,
    }


def certificate_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def transient_network_error(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    if isinstance(exc, URLError):
        return isinstance(exc.reason, (ssl.SSLError, socket.timeout, TimeoutError))
    return isinstance(exc, (ssl.SSLError, socket.timeout, TimeoutError))


def retry_delay(exc: Exception) -> float:
    if isinstance(exc, HTTPError) and exc.headers:
        value = exc.headers.get("Retry-After")
        try:
            return min(MAX_RETRY_AFTER_SECONDS, max(0.0, float(value)))
        except (TypeError, ValueError):
            pass
    return 0.25


def fetch_sec_mapping(
    *,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    payload = None
    attempts = 0
    context = certificate_context()
    for attempt in range(2):
        attempts = attempt + 1
        request = Request(
            SEC_MAPPING_URL,
            headers={
                "User-Agent": "InvestmentCouncil/1.0 https://github.com/HuaiL22/investment-council"
            },
        )
        try:
            with opener(
                request,
                timeout=NETWORK_TIMEOUT_SECONDS,
                context=context,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except Exception as exc:
            if attempt == 0 and transient_network_error(exc):
                sleeper(retry_delay(exc))
                continue
            raise
    if payload is None:
        raise RuntimeError("SEC mapping request returned no payload")
    fetched_at = utc_now().isoformat()
    fields = payload.get("fields")
    rows = payload.get("data")
    if not isinstance(fields, list) or not isinstance(rows, list):
        raise ValueError("unexpected SEC mapping shape")
    records = [dict(zip(fields, row)) for row in rows]
    return {
        "source": "SEC company_tickers_exchange",
        "source_url": SEC_MAPPING_URL,
        "fetched_at": fetched_at,
        "source_as_of": payload.get("as_of"),
        "retrieval_attempts": attempts,
        "records": records,
    }


def frame_from_history(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    output = frame.copy()
    if isinstance(output.columns, pd.MultiIndex):
        output.columns = output.columns.get_level_values(0)
    output = output.reset_index()
    first = output.columns[0]
    output = output.rename(columns={first: "date"})
    output.columns = [str(column).lower().replace(" ", "_") for column in output.columns]
    if "adj_close" not in output:
        output["adj_close"] = output.get("close")
    return output


def fetch_market_data(
    ticker_symbol: str,
    cutoff: datetime,
    *,
    ticker_factory: Callable[[str], Any] = yf.Ticker,
    download_loader: Callable[..., pd.DataFrame] = yf.download,
) -> dict[str, Any]:
    fetched_at = utc_now().isoformat()
    start = (cutoff - timedelta(days=550)).date().isoformat()
    end = (cutoff + timedelta(days=1)).date().isoformat()
    ticker = None
    frame = pd.DataFrame()
    errors = []
    retrieval_attempts = 1
    fallback_used = False
    try:
        ticker = ticker_factory(ticker_symbol)
        frame = frame_from_history(
            ticker.history(start=start, end=end, auto_adjust=False, actions=True)
        )
        if frame.empty:
            errors.append("Ticker.history returned no rows")
    except Exception as exc:
        errors.append(f"Ticker.history {type(exc).__name__}: {exc}")

    if frame.empty:
        fallback_used = True
        retrieval_attempts = 2
        try:
            frame = frame_from_history(download_loader(
                ticker_symbol,
                start=start,
                end=end,
                auto_adjust=False,
                actions=True,
                progress=False,
                threads=False,
            ))
            if frame.empty:
                errors.append("yf.download returned no rows")
        except Exception as exc:
            errors.append(f"yf.download {type(exc).__name__}: {exc}")

    if frame.empty:
        raise RuntimeError("; ".join(errors) or "Yahoo Finance returned no rows")
    currency = None
    if ticker is not None:
        try:
            fast_info = ticker.fast_info
            currency = fast_info.get("currency") if hasattr(fast_info, "get") else None
        except Exception:
            currency = None
    return {
        "source": (
            "Yahoo Finance via yfinance download fallback"
            if fallback_used
            else "Yahoo Finance via yfinance Ticker.history"
        ),
        "source_url": f"https://finance.yahoo.com/quote/{ticker_symbol}/history",
        "fetched_at": fetched_at,
        "quote_currency": str(currency).upper() if currency else None,
        "retrieval_attempts": retrieval_attempts,
        "fallback_used": fallback_used,
        "prior_errors": errors if fallback_used else [],
        "frame": frame,
    }


def completed_history(frame: pd.DataFrame, cutoff: datetime) -> tuple[pd.DataFrame, int]:
    if frame is None or frame.empty:
        return pd.DataFrame(), 0
    required = {"date", "open", "high", "low", "close", "volume"}
    if not required <= set(frame.columns):
        return pd.DataFrame(), len(frame)
    rows = []
    quarantined = 0
    for raw in frame.to_dict(orient="records"):
        try:
            date = pd.Timestamp(raw["date"])
            if date.tzinfo is None:
                date = date.tz_localize("UTC")
            available_value = raw.get("available_at")
            if available_value:
                available = pd.Timestamp(available_value)
                if available.tzinfo is None:
                    available = available.tz_localize("UTC")
            else:
                available = (date + pd.Timedelta(days=1)).normalize()
            if available.to_pydatetime() > cutoff:
                quarantined += 1
                continue
            row = dict(raw)
            row["date"] = date
            row["available_at"] = available
            row["adj_close"] = row.get("adj_close", row.get("close"))
            rows.append(row)
        except (TypeError, ValueError):
            quarantined += 1
    if not rows:
        return pd.DataFrame(), quarantined
    output = pd.DataFrame(rows)
    numeric = ["open", "high", "low", "close", "adj_close", "volume"]
    output[numeric] = output[numeric].apply(pd.to_numeric, errors="coerce")
    output = output.dropna(subset=["date", "close", "volume"])
    output = output.sort_values("date").drop_duplicates("date")
    return output, quarantined


def sec_index(mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for record in mapping.get("records", []):
        ticker = str(record.get("ticker") or "").upper()
        if ticker:
            result[ticker] = record
    return result


def identity_result(
    security: dict[str, Any],
    boundary: dict[str, Any],
    cutoff: datetime,
    mapping: dict[str, Any] | None,
    mapping_error: str | None,
) -> dict[str, Any]:
    markets = {value.casefold() for value in boundary["markets"]}
    if "us" not in markets and "usa" not in markets and "united states" not in markets:
        return {
            "status": "unsupported",
            "reason": "version 1 official mapping supports US-listed securities only",
            "canonical": None,
            "source": None,
            "boundary_status": "unsupported",
            "security_type_status": "unsupported",
        }
    if mapping is None:
        return {
            "status": "unavailable",
            "reason": mapping_error or "official mapping unavailable",
            "canonical": None,
            "source": None,
            "boundary_status": "unavailable",
            "security_type_status": "unavailable",
        }
    record = sec_index(mapping).get(security["ticker"])
    source = {
        "name": mapping.get("source"),
        "url": mapping.get("source_url"),
        "fetched_at": mapping.get("fetched_at"),
        "source_as_of": mapping.get("source_as_of"),
    }
    if record is None:
        return {
            "status": "unavailable",
            "reason": "ticker absent from official current mapping",
            "canonical": None,
            "source": source,
            "boundary_status": "unavailable",
            "security_type_status": "unsupported",
        }

    canonical = {
        "ticker": str(record.get("ticker") or "").upper(),
        "issuer_name": record.get("name"),
        "venue": record.get("exchange"),
        "official_identifier": normalize_identifier(record.get("cik")),
    }
    conflicts = []
    expected_identifier = security.get("expected_official_identifier")
    if expected_identifier and expected_identifier != canonical["official_identifier"]:
        conflicts.append("official_identifier")
    if security["expected_venue"].casefold() != str(canonical["venue"] or "").casefold():
        conflicts.append("venue")
    warnings = []
    if normalize_name(security["issuer_name"]) != normalize_name(str(canonical["issuer_name"] or "")):
        warnings.append("issuer display name differs from official mapping; review manually")

    fetched = parse_time(mapping.get("fetched_at"), "mapping.fetched_at")
    historical = cutoff.date() < fetched.astimezone(cutoff.tzinfo).date()
    status = "conflicting" if conflicts else "current_only" if historical else "verified_at_cutoff"
    venues = {value.casefold() for value in boundary["venues"]}
    types = {value.casefold() for value in boundary["security_types"]}
    venue_ok = str(canonical["venue"] or "").casefold() in venues
    type_ok = security["expected_security_type"].casefold() in types
    boundary_status = "pass" if venue_ok and type_ok else "fail"
    if not venue_ok:
        warnings.append("official venue falls outside market boundary")
    if not type_ok:
        warnings.append("expected security type falls outside market boundary")
    return {
        "status": status,
        "reason": None if not conflicts else "expected fields conflict: " + ", ".join(conflicts),
        "canonical": canonical,
        "source": source,
        "boundary_status": boundary_status,
        "security_type_status": "unsupported",
        "warnings": warnings,
    }


def metric(value: Any, status: str, *, unit: str | None = None, **extra: Any) -> dict[str, Any]:
    output = {"status": status, "value": None if value is None or pd.isna(value) else value}
    if unit:
        output["unit"] = unit
    output.update(extra)
    return output


def window_metric(series: pd.Series, window: int, reducer: Callable[[pd.Series], float]) -> dict[str, Any]:
    available = len(series)
    if available == 0:
        return metric(None, "unavailable", window_sessions=window, observed_sessions=0)
    value = reducer(series.tail(window))
    status = "available" if available >= window else "insufficient_history"
    return metric(float(value), status, window_sessions=window, observed_sessions=min(available, window))


def return_metric(frame: pd.DataFrame, window: int) -> dict[str, Any]:
    series = frame["adj_close"].dropna()
    if len(series) < window + 1:
        status = "unavailable" if series.empty else "insufficient_history"
        return metric(None, status, unit="percent", window_sessions=window)
    value = (float(series.iloc[-1]) / float(series.iloc[-window - 1]) - 1) * 100
    return metric(value, "available", unit="percent", window_sessions=window)


def relative_return_metric(frame: pd.DataFrame, benchmark: pd.DataFrame | None, window: int) -> dict[str, Any]:
    if benchmark is None or benchmark.empty:
        return metric(None, "unavailable", unit="percentage_points", window_sessions=window)
    left = frame[["date", "adj_close"]].dropna().copy()
    right = benchmark[["date", "adj_close"]].dropna().copy()
    left["session"] = pd.to_datetime(left["date"], utc=True).dt.normalize()
    right["session"] = pd.to_datetime(right["date"], utc=True).dt.normalize()
    joined = left.set_index("session")[["adj_close"]].join(
        right.set_index("session")[["adj_close"]], how="inner", lsuffix="_security", rsuffix="_benchmark"
    ).dropna()
    if len(joined) < window + 1:
        status = "unavailable" if joined.empty else "insufficient_history"
        return metric(None, status, unit="percentage_points", window_sessions=window)
    security_return = joined["adj_close_security"].iloc[-1] / joined["adj_close_security"].iloc[-window - 1] - 1
    benchmark_return = joined["adj_close_benchmark"].iloc[-1] / joined["adj_close_benchmark"].iloc[-window - 1] - 1
    return metric(float((security_return - benchmark_return) * 100), "available", unit="percentage_points", window_sessions=window)


def technical_overlay(frame: pd.DataFrame, benchmark: pd.DataFrame | None) -> dict[str, Any]:
    if frame.empty:
        overlay = {}
        for name in ("return_20", "return_60"):
            overlay[name] = metric(None, "unavailable", unit="percent")
        for name in ("relative_return_20", "relative_return_60"):
            overlay[name] = metric(None, "unavailable", unit="percentage_points")
        for name in (
            "close_vs_sma_50", "close_vs_sma_200", "rsi_14", "macd_hist",
            "macd_hist_change", "atr_14_pct", "volume_5_vs_prior_20",
            "price_percentile_252", "rsi_percentile_252", "atr_percentile_252",
            "sma_50_slope_20", "sma_200_slope_20", "trend_regime",
        ):
            overlay[name] = metric(None, "unavailable")
        return overlay

    overlay = {
        "return_20": return_metric(frame, 20),
        "return_60": return_metric(frame, 60),
        "relative_return_20": relative_return_metric(frame, benchmark, 20),
        "relative_return_60": relative_return_metric(frame, benchmark, 60),
    }

    selected = ["sma_50", "sma_200", "macd", "rsi_14", "atr_14"]
    calculated = technical_analysis.calculate(
        frame[["date", "open", "high", "low", "close", "volume"]], selected
    )
    snapshot = technical_analysis.build_snapshot(frame, calculated, 252)
    latest = calculated.iloc[-1]
    previous = calculated.iloc[-2] if len(calculated) > 1 else None

    def latest_metric(column: str, unit: str | None = None) -> dict[str, Any]:
        value = latest.get(column)
        if value is None or pd.isna(value):
            return metric(None, "insufficient_history", unit=unit)
        return metric(float(value), "available", unit=unit)

    close = float(latest["close"])
    for window in (50, 200):
        column = f"sma_{window}"
        value = latest.get(column)
        status = "available" if value is not None and not pd.isna(value) else "insufficient_history"
        difference = (close / float(value) - 1) * 100 if status == "available" else None
        overlay[f"close_vs_sma_{window}"] = metric(difference, status, unit="percent")
    overlay["rsi_14"] = latest_metric("rsi_14", "index")
    overlay["macd_hist"] = latest_metric("macd_hist", "price")
    if previous is None or pd.isna(latest.get("macd_hist")) or pd.isna(previous.get("macd_hist")):
        overlay["macd_hist_change"] = metric(None, "insufficient_history", unit="price")
    else:
        overlay["macd_hist_change"] = metric(
            float(latest["macd_hist"] - previous["macd_hist"]), "available", unit="price"
        )
    atr = latest.get("atr_14")
    overlay["atr_14_pct"] = metric(
        None if atr is None or pd.isna(atr) or close == 0 else float(atr / close * 100),
        "insufficient_history" if atr is None or pd.isna(atr) or close == 0 else "available",
        unit="percent",
    )
    snapshot_metrics = snapshot.get("metrics", {})
    for source_key, target_key in (
        ("price_percentile", "price_percentile_252"),
        ("rsi_percentile", "rsi_percentile_252"),
        ("atr_percentile", "atr_percentile_252"),
        ("sma_50_slope_20", "sma_50_slope_20"),
        ("sma_200_slope_20", "sma_200_slope_20"),
    ):
        overlay[target_key] = snapshot_metrics.get(source_key, metric(None, "unavailable"))
    overlay["trend_regime"] = snapshot.get(
        "trend_regime", {"status": "unavailable", "value": None}
    )
    volumes = frame["volume"].dropna()
    if len(volumes) < 25:
        overlay["volume_5_vs_prior_20"] = metric(None, "insufficient_history", unit="ratio")
    else:
        baseline = float(volumes.iloc[-25:-5].median())
        recent = float(volumes.iloc[-5:].median())
        overlay["volume_5_vs_prior_20"] = metric(
            None if baseline == 0 else recent / baseline,
            "unavailable" if baseline == 0 else "available",
            unit="ratio",
        )
    return overlay


def liquidity_result(
    frame: pd.DataFrame,
    quote_currency: str | None,
    rule: dict[str, Any] | None,
    cutoff: datetime,
) -> dict[str, Any]:
    count = len(frame)
    observation_status = "unavailable" if count == 0 else "observed" if count >= 60 else "insufficient_history"
    turnover = frame["close"] * frame["volume"] if count else pd.Series(dtype=float)
    metrics: dict[str, Any] = {}
    for window in (20, 60):
        turnover_metric = window_metric(turnover, window, lambda values: float(values.median()))
        turnover_metric["unit"] = quote_currency
        metrics[f"median_turnover_{window}"] = turnover_metric
        metrics[f"traded_sessions_{window}"] = window_metric(
            frame["volume"] if count else pd.Series(dtype=float),
            window,
            lambda values: int((values > 0).sum()),
        )
        metrics[f"zero_volume_sessions_{window}"] = window_metric(
            frame["volume"] if count else pd.Series(dtype=float),
            window,
            lambda values: int((values == 0).sum()),
        )
    if count:
        latest_date = pd.Timestamp(frame.iloc[-1]["date"])
        staleness = max(0, (cutoff.date() - latest_date.date()).days)
        latest = {
            "date": latest_date.isoformat(),
            "available_at": pd.Timestamp(frame.iloc[-1]["available_at"]).isoformat(),
            "close": float(frame.iloc[-1]["close"]),
            "volume": float(frame.iloc[-1]["volume"]),
        }
    else:
        staleness = None
        latest = None

    if rule is None:
        rule_result = {"status": "not_applicable", "rule": None, "observed_value": None}
    else:
        chosen = metrics[f"median_turnover_{rule['window_sessions']}"]
        if chosen["status"] != "available" or not quote_currency or quote_currency != rule["currency"]:
            reason = "insufficient market history" if chosen["status"] != "available" else "quote currency does not match rule currency"
            rule_result = {"status": "unavailable", "rule": rule, "observed_value": chosen.get("value"), "reason": reason}
        else:
            passed = float(chosen["value"]) >= float(rule["threshold"])
            rule_result = {
                "status": "pass" if passed else "fail",
                "rule": rule,
                "observed_value": chosen["value"],
            }
    return {
        "observation_status": observation_status,
        "quote_currency": quote_currency,
        "history_sessions": count,
        "history_limited": 0 < count < 60,
        "calendar_days_since_last_bar": staleness,
        "latest_completed_bar": latest,
        "metrics": metrics,
        "rule_result": rule_result,
    }


def duplicate_warnings(securities: list[dict[str, Any]]) -> tuple[list[str], dict[str, list[str]]]:
    ticker_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    identifier_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    issuer_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entity_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for security in securities:
        ticker_groups[security["ticker"]].append(security)
        identifier = security.get("expected_official_identifier")
        if identifier:
            identifier_groups[identifier].append(security)
        issuer_groups[normalize_name(security["issuer_name"])].append(security)
        entity_id = security.get("issuer_entity_id")
        if entity_id:
            entity_groups[entity_id].append(security)

    global_warnings: list[str] = []
    by_route: dict[str, list[str]] = defaultdict(list)

    def add_warning(entries: list[dict[str, Any]], message: str) -> None:
        global_warnings.append(message)
        for entry in entries:
            by_route[entry["route_id"]].append(message)

    for ticker, entries in sorted(ticker_groups.items()):
        if len(entries) < 2:
            continue
        route_ids = sorted(entry["route_id"] for entry in entries)
        direct_entity_ids = {
            entry["issuer_entity_id"]
            for entry in entries
            if entry["route_type"] == "direct" and entry.get("issuer_entity_id")
        }
        if len(direct_entity_ids) > 1:
            reason = "direct ticker assigned to different issuer entities"
        else:
            reason = "ticker mapped by more than one route"
        add_warning(entries, f"duplicate ticker {ticker}: {', '.join(route_ids)}; {reason}")

    for identifier, entries in sorted(identifier_groups.items()):
        if len(entries) < 2:
            continue
        direct_entries = [entry for entry in entries if entry["route_type"] == "direct"]
        direct_entity_ids = {entry["issuer_entity_id"] for entry in direct_entries}
        indirect_entries = [entry for entry in entries if entry["route_type"] == "indirect"]
        if len(direct_entity_ids) <= 1 and not indirect_entries:
            continue
        route_ids = sorted(entry["route_id"] for entry in entries)
        add_warning(
            entries,
            f"duplicate official_identifier {identifier}: {', '.join(route_ids)}; "
            "identifier assigned across distinct issuer or fund routes",
        )

    for issuer, entries in sorted(issuer_groups.items()):
        if len(entries) < 2:
            continue
        entity_ids = {entry.get("issuer_entity_id") for entry in entries}
        if len(entity_ids) <= 1:
            continue
        route_ids = sorted(entry["route_id"] for entry in entries)
        add_warning(
            entries,
            f"issuer name {issuer} maps to different entity IDs: {', '.join(route_ids)}",
        )

    for entity_id, entries in sorted(entity_groups.items()):
        categories = {
            entry["proposed_category"]
            for entry in entries
            if entry.get("proposed_category")
        }
        if len(categories) <= 1:
            continue
        route_ids = sorted(entry["route_id"] for entry in entries)
        add_warning(
            entries,
            f"issuer entity {entity_id} has incompatible proposed categories: "
            f"{', '.join(sorted(categories))}; routes {', '.join(route_ids)}",
        )
    return global_warnings, by_route


def audit(
    payload: Any,
    *,
    mapping_loader: Callable[[], dict[str, Any]] = fetch_sec_mapping,
    market_loader: Callable[[str, datetime], dict[str, Any]] = fetch_market_data,
    now: datetime | None = None,
) -> dict[str, Any]:
    validated = validate_payload(payload, now=now)
    cutoff = validated["analysis_cutoff"]
    fetched_at = (now or utc_now()).isoformat()
    try:
        mapping = mapping_loader()
        mapping_error = None
    except Exception as exc:
        mapping = None
        mapping_error = f"{type(exc).__name__}: {exc}"

    benchmark_result = {"status": "not_requested", "ticker": None, "error": None}
    benchmark_frame = None
    benchmark = validated["benchmark"]
    if benchmark:
        try:
            raw_benchmark = market_loader(benchmark["ticker"], cutoff)
            benchmark_frame, benchmark_quarantined = completed_history(raw_benchmark.get("frame"), cutoff)
            benchmark_status = "available" if not benchmark_frame.empty else "unavailable"
            benchmark_result = {
                "status": benchmark_status,
                "ticker": benchmark["ticker"],
                "error": None if benchmark_status == "available" else "no completed bars",
                "quarantined_rows": benchmark_quarantined,
            }
        except Exception as exc:
            benchmark_result = {
                "status": "unavailable",
                "ticker": benchmark["ticker"],
                "error": f"{type(exc).__name__}: {exc}",
            }

    global_warnings, route_warnings = duplicate_warnings(validated["securities"])
    if mapping_error:
        global_warnings.append("official mapping unavailable: " + mapping_error)
    results = []
    usable_components = 0
    failed_components = 0
    for security in sorted(
        validated["securities"],
        key=lambda item: (item.get("issuer_entity_id") or "", item["route_id"], item["ticker"]),
    ):
        identity = identity_result(
            security, validated["market_boundary"], cutoff, mapping, mapping_error
        )
        warnings = list(route_warnings.get(security["route_id"], []))
        warnings.extend(identity.get("warnings", []))
        if identity["status"] in {"verified_at_cutoff", "current_only", "conflicting"}:
            usable_components += 1
        else:
            failed_components += 1
        if identity["status"] != "verified_at_cutoff" or identity["boundary_status"] != "pass":
            failed_components += 1
        market_source = None
        market_error = None
        quarantined = 0
        frame = pd.DataFrame()
        input_currency = security.get("quote_currency")
        quote_currency = input_currency
        currency_conflict = None
        try:
            raw_market = market_loader(security["ticker"], cutoff)
            frame, quarantined = completed_history(raw_market.get("frame"), cutoff)
            market_source = {
                "name": raw_market.get("source"),
                "url": raw_market.get("source_url"),
                "fetched_at": raw_market.get("fetched_at"),
                "retrieval_attempts": raw_market.get("retrieval_attempts", 1),
                "fallback_used": bool(raw_market.get("fallback_used", False)),
                "prior_errors": raw_market.get("prior_errors", []),
            }
            provider_currency = str(raw_market.get("quote_currency") or "").upper() or None
            if input_currency and provider_currency and input_currency != provider_currency:
                currency_conflict = (
                    f"input quote currency {input_currency} conflicts with provider {provider_currency}"
                )
                quote_currency = None
            else:
                quote_currency = input_currency or provider_currency
        except Exception as exc:
            market_error = f"{type(exc).__name__}: {exc}"
        if frame.empty:
            failed_components += 1
        else:
            usable_components += 1
        liquidity = liquidity_result(
            frame, str(quote_currency).upper() if quote_currency else None,
            validated["liquidity_rule"], cutoff,
        )
        overlay = technical_overlay(frame, benchmark_frame)
        recent_actions = False
        if not frame.empty:
            for action_column in ("stock_splits", "dividends"):
                if action_column in frame and frame[action_column].tail(60).fillna(0).ne(0).any():
                    recent_actions = True
        if recent_actions:
            warnings.append("recent corporate action may make raw-price technical fields misleading")
        if market_error:
            warnings.append("market data unavailable: " + market_error)
        if currency_conflict:
            warnings.append(currency_conflict)
            failed_components += 1
        if liquidity["rule_result"]["status"] in {"fail", "unavailable"}:
            failed_components += 1
        result = {
            "route_id": security["route_id"],
            "route_type": security["route_type"],
            "issuer_entity_id": security.get("issuer_entity_id"),
            "proposed": {
                "ticker": security["ticker"],
                "issuer_name": security["issuer_name"],
                "venue": security["expected_venue"],
                "security_type": security["expected_security_type"],
                "official_identifier": security.get("expected_official_identifier"),
                "category": security.get("proposed_category"),
            },
            "identity": identity,
            "market_data": {
                "observation_status": liquidity["observation_status"],
                "source": market_source,
                "error": market_error,
                "quarantined_rows": quarantined,
            },
            "liquidity": liquidity,
            "overlay": overlay,
            "conflicts": route_warnings.get(security["route_id"], []),
            "warnings": sorted(set(warnings)),
        }
        if security.get("legacy_candidate_id") is not None:
            result["candidate_id"] = security["legacy_candidate_id"]
        results.append(result)

    if usable_components == 0:
        overall_status = "unavailable"
    elif failed_components or benchmark_result["status"] == "unavailable":
        overall_status = "partial"
    else:
        overall_status = "complete"
    return {
        "schema_version": SCHEMA_VERSION,
        "input_schema_version": validated["input_schema_version"],
        "analysis_cutoff": cutoff.isoformat(),
        "fetched_at": fetched_at,
        "overall_status": overall_status,
        "benchmark": benchmark_result,
        "securities": results,
        "warnings": sorted(set(global_warnings)),
    }


def read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, payload: Any) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    if path == "-":
        sys.stdout.write(rendered)
    else:
        Path(path).write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="-", help="Audit input JSON or - for stdin")
    parser.add_argument("--output", default="-", help="Audit output JSON or - for stdout")
    args = parser.parse_args()
    try:
        result = audit(read_json(args.input))
    except (ContractError, json.JSONDecodeError) as exc:
        sys.stderr.write(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "status": "invalid_input",
            "error": str(exc),
        }, ensure_ascii=False) + "\n")
        return 2
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
