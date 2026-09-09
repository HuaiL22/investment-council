#!/usr/bin/env python3
"""Atomic run manifest, artifact, and checkpoint storage."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
CORE_ORDER = ["market", "sentiment", "news", "fundamentals"]
SCREENING_ORDER = ["scope", "system_map", "candidate_ledger", "shortlist", "comparison", "complete"]
CANDIDATE_STATES = {
    "discovered", "researching", "pending_verification", "advanced", "eliminated",
}
DISCOVERY_CLASSIFICATIONS = {"candidate", "research_lead", "context"}
ACCESS_STATUSES = {
    "direct_available", "indirect_only", "outside_boundary",
    "no_known_tradable_vehicle", "direct_unresolved",
}
COVERAGE_STATUSES = {"coverage_complete", "coverage_incomplete"}
SCREENING_SCOPES = {"full_universe", "resolved_subset"}
IMPACT_LEVELS = {"high", "lower"}
DIRECT_ROUTE_FAMILIES = ("primary", "secondary", "depositary", "corporate_action")
DIRECT_ROUTE_CHECK_STATUSES = {
    "eligible", "outside_boundary", "not_found", "not_applicable", "unresolved",
}
FUND_FALLBACK_STATUSES = {"eligible", "not_found", "not_applicable", "unresolved"}
FUND_POLICIES = {"excluded_by_user", "fallback_allowed", "formal_universe_requested"}
TERMINAL_LIFECYCLES = {"complete", "failed"}
USABLE_RECORD_STATUSES = {"available", "partial", "conflict"}
RECORD_STATUSES = {
    "available", "partial", "conflict", "stale", "unavailable",
    "historical_unavailable", "quarantined", "inapplicable",
}
EVIDENCE_STRENGTHS = {"strong", "medium", "weak", "unverified"}
EVIDENCE_KINDS = {
    "observed_fact", "management_claim", "analytical_input", "unverified_lead",
}
EVIDENCE_SCOPES = {"shared", "candidate"}
ARTIFACT_PROFILES = {"compact", "audit"}
STAGE_STORE_FILENAME = "stages.json"
RATINGS = {"Buy", "Overweight", "Hold", "Underweight", "Sell"}
EXPOSURE_INTENTS = {
    "open_long", "add_long", "hold", "reduce_long", "close_long",
    "open_short", "add_short", "reduce_short", "close_short", "avoid",
}
TRADER_ACTIONS = {"Buy", "Hold", "Sell"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
CONTEXT_EFFECTS = {
    "supportive", "neutral", "adverse", "mixed", "unavailable",
    "insufficient_history",
}
SIZING_BASES = {"none", "risk_units", "portfolio_context"}
REQUIRED_PACKAGES = ("numpy", "pandas", "yfinance", "certifi")
FORBIDDEN_SCRIPT_PATTERNS = (
    re.compile(r"(^|\n)\s*(from|import)\s+(openai|anthropic|langchain)", re.I),
    re.compile(r"\b((subprocess|system|popen|run)\b.*\bcodex|codex\b.*\b(subprocess|system|popen|run))\b", re.I),
    re.compile(r"\b(chat\.completions|responses\.create|messages\.create)\b", re.I),
)
PERCENTAGE_VALUE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?\s*%")
PERCENTAGE_ONLY = re.compile(r"^\s*(?:[-*]\s*)?\d+(?:\.\d+)?\s*%\s*$")
PERCENTAGE_SIZING_LABEL_TEXT = (
    r"(?:(?:portfolio|position|suggested|target|hypothetical)\s+"
    r"(?:weight|allocation|size|risk\s+budget)|"
    r"(?:weight|allocation|risk\s+budget)|"
    r"(?:建议|目标|假设|组合)?(?:仓位|权重|配置比例|风险预算)|配置)"
)
PERCENTAGE_SIZING_LABEL = re.compile(PERCENTAGE_SIZING_LABEL_TEXT, re.I)
PERCENTAGE_SIZING_LABEL_ONLY = re.compile(
    rf"^\s*{PERCENTAGE_SIZING_LABEL_TEXT}\s*[:：]?\s*$", re.I,
)
PERCENTAGE_SIZING_INLINE = re.compile(
    rf"{PERCENTAGE_SIZING_LABEL_TEXT}"
    rf"\s*(?:(?:[:：=]|is|of|at|为|是)\s*)?"
    rf"(?:(?:should\s+)?(?:not\s+exceed|be)\s*)?"
    rf"(?:(?:no\s+more\s+than|up\s+to|about|approximately|around|约|不超过)\s*)?"
    rf"{PERCENTAGE_VALUE.pattern}",
    re.I,
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def collection_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{field} must be a timezone-aware timestamp") from None
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_source(source: str | Path) -> Any:
    """Read JSON from a path or stdin when source is '-'."""
    if str(source) == "-":
        return json.load(sys.stdin)
    return load(Path(source))


def load_bytes_source(source: str | Path) -> bytes:
    """Read bytes from a path or stdin when source is '-'."""
    if str(source) != "-":
        return Path(source).read_bytes()
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    value = stream.read()
    return value.encode("utf-8") if isinstance(value, str) else value


def package_status(names: tuple[str, ...]) -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in names}


def scan_scripts(root: Path) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path in sorted(root.glob("*.py")):
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_SCRIPT_PATTERNS:
            if pattern.search(text):
                violations.append({"file": path.name, "pattern": pattern.pattern})
    return violations


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


def atomic_write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def artifact_bytes(run_dir: Path, entry: dict[str, Any]) -> bytes:
    """Read one committed Markdown stage from either supported storage profile."""
    path_value = entry.get("path")
    if not isinstance(path_value, str):
        raise ValueError("artifact path is missing")
    path = (run_dir / path_value).resolve()
    try:
        path.relative_to(run_dir.resolve())
    except ValueError:
        raise ValueError("artifact path escapes run directory") from None
    if entry.get("storage") == "bundle":
        key = entry.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("bundled artifact key is missing")
        bundle = load(path)
        if bundle.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("stage bundle schema version mismatch")
        stages = bundle.get("stages")
        if not isinstance(stages, dict) or not isinstance(stages.get(key), str):
            raise ValueError(f"bundled artifact is missing stage: {key}")
        return stages[key].encode("utf-8")
    if not path.exists():
        raise ValueError("artifact file is missing")
    return path.read_bytes()


def safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._=-]+", "_", value.strip())
    cleaned = cleaned.strip("._")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("unsafe empty path component")
    return cleaned[:96]


def contains_percentage_sizing(markdown: bytes) -> bool:
    """Detect percentage position sizing while avoiding ordinary financial percentages."""
    text = markdown.decode("utf-8", errors="replace")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if PERCENTAGE_SIZING_INLINE.search(line):
            return True
        if "|" in line:
            headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
            sizing_columns = [
                column for column, header in enumerate(headers)
                if PERCENTAGE_SIZING_LABEL_ONLY.fullmatch(header)
            ]
            if not sizing_columns:
                continue
            for following in lines[index + 1:index + 20]:
                if not following.strip() or "|" not in following:
                    break
                cells = [cell.strip() for cell in following.strip().strip("|").split("|")]
                for column in sizing_columns:
                    if column < len(cells) and PERCENTAGE_VALUE.search(cells[column]):
                        return True
        else:
            heading = re.sub(r"^\s{0,3}#{1,6}\s*", "", line).strip()
            if not PERCENTAGE_SIZING_LABEL_ONLY.fullmatch(heading):
                continue
            for following in lines[index + 1:index + 5]:
                if not following.strip():
                    continue
                if PERCENTAGE_ONLY.match(following) or (
                    re.match(r"^\s*[-*+]\s+", following)
                    and PERCENTAGE_VALUE.search(following)
                ):
                    return True
                break
    return False


def resume_signature(manifest: dict[str, Any]) -> str:
    keys = [
        "run_type", "research_mode", "theme", "comparison_label", "market",
        "time_horizon", "liquidity_requirement", "eligible_venues",
        "eligible_security_types", "include_otc", "include_funds",
        "parent_screening_run_id",
        "parent_evidence_hash", "candidate_id", "relevant_subject_ids",
        "requested_ticker", "canonical_ticker", "analysis_cutoff", "timezone",
        "asset_type", "analysts", "investment_debate_rounds", "risk_debate_rounds",
        "benchmark_ticker", "execution_mode_requested", "execution_mode_used",
        "macro_context_enabled", "macro_series", "macro_percentile_window",
        "technical_percentile_window",
        "portfolio_context", "output_language",
        "prompt_reference_version", "prompt_reference_hash", "skill_version",
        "schema_version", "evidence_hash", "artifact_profile",
    ]
    return digest({key: manifest.get(key) for key in keys})


def stage_order(manifest: dict[str, Any]) -> list[str]:
    if manifest.get("run_type", "instrument") == "screening":
        return list(SCREENING_ORDER)
    stages = list(CORE_ORDER)
    for idx in range(1, int(manifest.get("investment_debate_rounds", 1)) + 1):
        stages.extend([f"bull_{idx}", f"bear_{idx}"])
    stages.extend(["research_manager", "trader"])
    for idx in range(1, int(manifest.get("risk_debate_rounds", 1)) + 1):
        stages.extend([f"aggressive_{idx}", f"conservative_{idx}", f"neutral_{idx}"])
    stages.extend(["portfolio_manager", "complete"])
    return stages


def expected_stage(stage: str, state: dict[str, Any], manifest: dict[str, Any]) -> bool:
    completed = state.get("completed_stages", [])
    if stage in completed:
        return True
    order = stage_order(manifest)
    return len(completed) < len(order) and stage == order[len(completed)]


def validate_evidence_bundle(
    evidence: Any,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(evidence, dict):
        raise ValueError("evidence bundle must be an object")
    if evidence.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("evidence schema_version must be 1.0")
    run_type = manifest.get("run_type", "instrument")
    if evidence.get("bundle_kind") != run_type:
        raise ValueError("evidence bundle_kind does not match manifest")
    if evidence.get("run_id") != manifest.get("run_id"):
        raise ValueError("evidence run_id does not match manifest")
    cutoff = parse_time(manifest.get("analysis_cutoff"), "manifest analysis_cutoff")
    evidence_cutoff = parse_time(evidence.get("analysis_cutoff"), "evidence analysis_cutoff")
    if evidence_cutoff.astimezone(timezone.utc) != cutoff.astimezone(timezone.utc):
        raise ValueError("evidence analysis_cutoff does not match manifest")
    expected_bundle_hash = collection_digest({
        key: value for key, value in evidence.items() if key != "bundle_hash"
    })
    if evidence.get("bundle_hash") != expected_bundle_hash:
        raise ValueError("evidence bundle_hash mismatch")
    records = evidence.get("records")
    if not isinstance(records, list):
        raise ValueError("evidence records must be an array")
    ohlcv = evidence.get("ohlcv")
    if not isinstance(ohlcv, list):
        raise ValueError("evidence ohlcv must be an array")
    for index, row in enumerate(ohlcv):
        if not isinstance(row, dict):
            raise ValueError(f"evidence ohlcv row {index} must be an object")
        available = parse_time(
            row.get("available_at"),
            f"evidence ohlcv row {index} available_at",
        )
        if available.astimezone(timezone.utc) > cutoff.astimezone(timezone.utc):
            raise ValueError(f"evidence ohlcv row {index} exceeds analysis_cutoff")
    parse_time(evidence.get("fetched_at"), "evidence fetched_at")
    if run_type == "instrument":
        requested = str(manifest.get("requested_ticker") or "").upper()
        canonical = str(manifest.get("canonical_ticker") or requested).upper()
        if str(evidence.get("requested_ticker") or "").upper() != requested:
            raise ValueError("evidence requested_ticker does not match manifest")
        if str(evidence.get("canonical_ticker") or "").upper() != canonical:
            raise ValueError("evidence canonical_ticker does not match manifest")
    seen_evidence_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"evidence record {index} must be an object")
        for field in ("evidence_id", "source", "subject_id", "field"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f"evidence record {index} has invalid {field}")
        if record["evidence_id"] in seen_evidence_ids:
            raise ValueError(f"duplicate evidence_id: {record['evidence_id']}")
        seen_evidence_ids.add(record["evidence_id"])
        if "value" not in record:
            raise ValueError(f"evidence record {index} is missing value")
        if record.get("status") not in RECORD_STATUSES:
            raise ValueError(f"evidence record {index} has invalid status")
        available = parse_time(record.get("available_at"), f"evidence record {index} available_at")
        parse_time(record.get("fetched_at"), f"evidence record {index} fetched_at")
        if available.astimezone(timezone.utc) > cutoff.astimezone(timezone.utc):
            raise ValueError(f"evidence record {index} exceeds analysis_cutoff")
        if record.get("observed_at") is not None:
            parse_time(record["observed_at"], f"evidence record {index} observed_at")
        if run_type == "screening":
            source_url = record.get("source_url")
            if not isinstance(source_url, str) or not re.match(r"^https?://", source_url):
                raise ValueError(f"evidence record {index} has invalid source_url")
            if record.get("evidence_strength") not in EVIDENCE_STRENGTHS:
                raise ValueError(f"evidence record {index} has invalid evidence_strength")
            if record.get("evidence_kind") not in EVIDENCE_KINDS:
                raise ValueError(f"evidence record {index} has invalid evidence_kind")
            scope = record.get("scope")
            candidate_ids = record.get("candidate_ids")
            if scope not in EVIDENCE_SCOPES:
                raise ValueError(f"evidence record {index} has invalid scope")
            if not isinstance(candidate_ids, list) or not all(
                isinstance(item, str) and item.strip() for item in candidate_ids
            ):
                raise ValueError(f"evidence record {index} has invalid candidate_ids")
            if scope == "shared" and candidate_ids:
                raise ValueError(f"evidence record {index} shared scope has candidate_ids")
            if scope == "candidate" and not candidate_ids:
                raise ValueError(f"evidence record {index} candidate scope lacks candidate_ids")
        expected_content_hash = collection_digest({
            key: value for key, value in record.items() if key != "content_hash"
        })
        if record.get("content_hash") != expected_content_hash:
            raise ValueError(f"evidence record {index} content_hash mismatch")
    usable = [
        record for record in records
        if record.get("status") in USABLE_RECORD_STATUSES
    ]
    if run_type == "instrument" and not usable:
        raise ValueError("instrument evidence contains no usable records")
    return usable


def validate_candidates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get("candidates"), list):
        raise ValueError("candidates input must be an object with a candidates array")
    candidates = value["candidates"]
    seen_ids: set[str] = set()
    seen_tickers: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("candidate entries must be objects")
        candidate_id = candidate.get("candidate_id")
        ticker = candidate.get("requested_ticker")
        market = candidate.get("market")
        state = candidate.get("status")
        transition_reason = candidate.get("transition_reason")
        next_required_evidence = candidate.get("next_required_evidence")
        atomic_path_ids = candidate.get("atomic_path_ids")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("candidate_id must be a non-empty string")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("requested_ticker must be a non-empty string")
        if not isinstance(market, str) or not market.strip():
            raise ValueError("candidate market must be a non-empty string")
        if state not in CANDIDATE_STATES:
            raise ValueError(f"invalid candidate status: {state}")
        if not isinstance(transition_reason, str) or not transition_reason.strip():
            raise ValueError(f"candidate lacks transition_reason: {candidate_id}")
        if not isinstance(next_required_evidence, str) or not next_required_evidence.strip():
            raise ValueError(f"candidate lacks next_required_evidence: {candidate_id}")
        if (
            not isinstance(atomic_path_ids, list)
            or not atomic_path_ids
            or not all(isinstance(item, str) and item.strip() for item in atomic_path_ids)
            or len(set(atomic_path_ids)) != len(atomic_path_ids)
        ):
            raise ValueError(f"candidate has invalid atomic_path_ids: {candidate_id}")
        if state in {"eliminated", "pending_verification"}:
            reentry_condition = candidate.get("reentry_condition")
            if not isinstance(reentry_condition, str) or not reentry_condition.strip():
                raise ValueError(f"candidate lacks reentry_condition: {candidate_id}")
        if candidate_id in seen_ids:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        normalized_ticker = ticker.upper()
        if normalized_ticker in seen_tickers:
            raise ValueError(f"duplicate requested_ticker: {ticker}")
        seen_ids.add(candidate_id)
        seen_tickers.add(normalized_ticker)
    return candidates


def validate_final_decision(
    value: Any,
    manifest: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("final decision must be an object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("final decision schema_version must be 1.0")
    if value.get("rating") not in RATINGS:
        raise ValueError("final decision has invalid rating")
    if value.get("exposure_intent") not in EXPOSURE_INTENTS:
        raise ValueError("final decision has invalid exposure_intent")
    if value.get("action") not in TRADER_ACTIONS:
        raise ValueError("final decision has invalid action")
    if value.get("confidence") not in CONFIDENCE_LEVELS:
        raise ValueError("final decision has invalid confidence")
    if value.get("macro_effect") not in CONTEXT_EFFECTS:
        raise ValueError("final decision has invalid macro_effect")
    if value.get("technical_effect") not in CONTEXT_EFFECTS:
        raise ValueError("final decision has invalid technical_effect")
    if value.get("sizing_basis") not in SIZING_BASES:
        raise ValueError("final decision has invalid sizing_basis")
    for field in ("decision_summary", "invalidation"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f"final decision requires {field}")

    usable = validate_evidence_bundle(evidence, manifest)
    usable_by_id = {record["evidence_id"]: record for record in usable}
    evidence_ids = value.get("evidence_ids")
    if not isinstance(evidence_ids, list) or len(set(evidence_ids)) < 2 or not all(
        isinstance(item, str) and item.strip() for item in evidence_ids
    ):
        raise ValueError("final decision requires at least two distinct evidence_ids")
    missing = sorted(set(evidence_ids) - set(usable_by_id))
    if missing:
        raise ValueError("final decision references unavailable evidence: " + ", ".join(missing))
    selected_records = [usable_by_id[item] for item in evidence_ids]
    if value.get("macro_effect") != "unavailable" and not any(
        record.get("field") == "macro_snapshot" for record in selected_records
    ):
        raise ValueError("available macro effect requires a cited macro_snapshot")
    if value.get("technical_effect") != "unavailable" and not any(
        record.get("field") == "technical_snapshot" for record in selected_records
    ):
        raise ValueError("available technical effect requires a cited technical_snapshot")

    if manifest.get("parent_screening_run_id"):
        candidate_id = manifest.get("candidate_id")
        subjects = {
            str(manifest.get("requested_ticker") or "").upper(),
            str(manifest.get("canonical_ticker") or "").upper(),
            *{
                str(item).upper()
                for item in manifest.get("relevant_subject_ids", [])
            },
        }
        if not any(
            record.get("scope") == "candidate"
            and (
                candidate_id in record.get("candidate_ids", [])
                or str(record.get("subject_id") or "").upper() in subjects
            )
            for record in selected_records
        ):
            raise ValueError("final decision lacks candidate-specific frozen evidence")

    portfolio_context = manifest.get("portfolio_context")
    user_portfolio_context = (
        isinstance(portfolio_context, dict)
        and portfolio_context.get("provided_by_user") is True
    )
    if value.get("sizing_basis") == "portfolio_context" and not user_portfolio_context:
        raise ValueError("portfolio_context sizing requires user-provided portfolio context")
    if value.get("suggested_weight_percent") is not None:
        weight = value["suggested_weight_percent"]
        if not user_portfolio_context:
            raise ValueError("percentage weights require user-provided portfolio context")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 <= weight <= 100:
            raise ValueError("suggested_weight_percent must be between 0 and 100")
    return value


def validate_discovery_baseline(value: Any, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValueError("theme discovery baseline must be an object")
    coverage_status = value.get("coverage_status")
    if coverage_status not in COVERAGE_STATUSES:
        raise ValueError("theme discovery baseline requires a valid coverage_status")
    screening_scope = value.get("screening_scope", "full_universe")
    if screening_scope not in SCREENING_SCOPES:
        raise ValueError("theme discovery baseline requires a valid screening_scope")
    if coverage_status == "coverage_complete" and screening_scope != "full_universe":
        raise ValueError("coverage_complete requires full_universe screening_scope")
    if coverage_status == "coverage_incomplete" and screening_scope != "resolved_subset":
        raise ValueError("coverage_incomplete requires resolved_subset screening_scope")
    cutoff = parse_time(value.get("analysis_cutoff"), "discovery baseline analysis_cutoff")
    manifest_cutoff = parse_time(manifest.get("analysis_cutoff"), "manifest analysis_cutoff")
    if cutoff != manifest_cutoff:
        raise ValueError("discovery baseline cutoff does not match manifest")
    fund_policy = value.get("fund_policy")
    if fund_policy not in FUND_POLICIES:
        raise ValueError("discovery baseline requires a valid fund_policy")
    entities = value.get("entities")
    if not isinstance(entities, list) or not entities:
        raise ValueError("discovery baseline requires a non-empty entities array")
    seen_entities: set[str] = set()
    seen_candidates: set[str] = set()
    unresolved_entities = 0
    for entity in entities:
        if not isinstance(entity, dict):
            raise ValueError("discovery baseline entities must be objects")
        entity_id = entity.get("entity_id")
        classification = entity.get("classification")
        path_ids = entity.get("atomic_path_ids")
        disposition = entity.get("disposition_reason")
        route_resolution = entity.get("route_resolution")
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("discovery baseline entity_id must be a non-empty string")
        if entity_id in seen_entities:
            raise ValueError(f"duplicate discovery entity_id: {entity_id}")
        if classification not in DISCOVERY_CLASSIFICATIONS:
            raise ValueError(f"invalid discovery classification: {classification}")
        if not isinstance(path_ids, list) or not path_ids or not all(
            isinstance(item, str) and item.strip() for item in path_ids
        ):
            raise ValueError(f"discovery entity lacks atomic_path_ids: {entity_id}")
        if not isinstance(disposition, str) or not disposition.strip():
            raise ValueError(f"discovery entity lacks disposition_reason: {entity_id}")
        if not isinstance(route_resolution, dict):
            raise ValueError(f"discovery entity lacks route_resolution: {entity_id}")
        access_status = route_resolution.get("access_status")
        if access_status not in ACCESS_STATUSES:
            raise ValueError(f"invalid discovery access_status: {entity_id}")
        checked_through = parse_time(
            route_resolution.get("checked_through"),
            f"discovery route checked_through for {entity_id}",
        )
        if checked_through != cutoff:
            raise ValueError(f"discovery route checks do not reach cutoff: {entity_id}")
        direct_checks = route_resolution.get("direct_route_families")
        if not isinstance(direct_checks, dict) or set(direct_checks) != set(DIRECT_ROUTE_FAMILIES):
            raise ValueError(f"discovery route families are incomplete: {entity_id}")
        for family, check in direct_checks.items():
            if not isinstance(check, dict) or check.get("status") not in DIRECT_ROUTE_CHECK_STATUSES:
                raise ValueError(f"invalid {family} route check: {entity_id}")
            if not isinstance(check.get("reason"), str) or not check["reason"].strip():
                raise ValueError(f"{family} route check lacks reason: {entity_id}")
            source_refs = check.get("source_refs")
            if check["status"] != "not_applicable" and (
                not isinstance(source_refs, list)
                or not source_refs
                or not all(isinstance(item, str) and item.strip() for item in source_refs)
            ):
                raise ValueError(f"{family} route check lacks source_refs: {entity_id}")
        direct_statuses = {check["status"] for check in direct_checks.values()}
        has_unresolved_direct = "unresolved" in direct_statuses
        if coverage_status == "coverage_complete" and has_unresolved_direct:
            raise ValueError(f"coverage_complete cannot contain unresolved direct routes: {entity_id}")
        has_direct = "eligible" in direct_statuses
        fund_fallback = route_resolution.get("fund_fallback")
        if not isinstance(fund_fallback, dict) or fund_fallback.get("status") not in FUND_FALLBACK_STATUSES:
            raise ValueError(f"invalid fund fallback: {entity_id}")
        if not isinstance(fund_fallback.get("reason"), str) or not fund_fallback["reason"].strip():
            raise ValueError(f"fund fallback lacks reason: {entity_id}")
        fund_status = fund_fallback["status"]
        fund_sources = fund_fallback.get("source_refs")
        if fund_status != "not_applicable" and (
            not isinstance(fund_sources, list)
            or not fund_sources
            or not all(isinstance(item, str) and item.strip() for item in fund_sources)
        ):
            raise ValueError(f"fund fallback lacks source_refs: {entity_id}")
        if coverage_status == "coverage_complete" and fund_status == "unresolved":
            raise ValueError(f"coverage_complete cannot contain unresolved fund fallback: {entity_id}")
        has_unresolved_route = has_unresolved_direct or fund_status == "unresolved"
        if has_unresolved_route:
            unresolved_entities += 1
            if classification != "research_lead":
                raise ValueError(f"unresolved route must remain a research_lead: {entity_id}")
            if entity.get("impact_level") not in IMPACT_LEVELS:
                raise ValueError(f"unresolved research lead lacks impact_level: {entity_id}")
            for field in ("unresolved_fact", "next_check"):
                if not isinstance(entity.get(field), str) or not entity[field].strip():
                    raise ValueError(f"unresolved research lead lacks {field}: {entity_id}")
            attempted_refs = entity.get("attempted_source_refs")
            if (
                not isinstance(attempted_refs, list)
                or not attempted_refs
                or not all(isinstance(item, str) and item.strip() for item in attempted_refs)
            ):
                raise ValueError(f"unresolved research lead lacks attempted_source_refs: {entity_id}")
        if fund_policy == "excluded_by_user" and fund_status != "not_applicable":
            raise ValueError(f"fund fallback conflicts with user exclusion: {entity_id}")
        if not has_direct and fund_policy != "excluded_by_user" and fund_status == "not_applicable":
            raise ValueError(f"missing conditional fund fallback: {entity_id}")
        if access_status == "direct_available" and not has_direct:
            raise ValueError(f"direct_available lacks an eligible direct route: {entity_id}")
        if access_status != "direct_available" and has_direct:
            raise ValueError(f"eligible direct route conflicts with access_status: {entity_id}")
        if access_status == "indirect_only" and fund_status != "eligible":
            raise ValueError(f"indirect_only lacks an eligible fund route: {entity_id}")
        if access_status != "indirect_only" and fund_status == "eligible":
            raise ValueError(f"eligible fund route conflicts with access_status: {entity_id}")
        if access_status == "outside_boundary" and "outside_boundary" not in direct_statuses:
            raise ValueError(f"outside_boundary lacks a known outside route: {entity_id}")
        if access_status == "direct_unresolved" and not has_unresolved_route:
            raise ValueError(f"direct_unresolved lacks an unresolved route check: {entity_id}")
        if access_status == "direct_unresolved" and has_direct:
            raise ValueError(f"direct_unresolved conflicts with an eligible direct route: {entity_id}")
        if access_status != "direct_unresolved" and has_unresolved_route:
            raise ValueError(f"unresolved route conflicts with access_status: {entity_id}")
        if classification == "candidate":
            candidate_id = entity.get("candidate_id")
            ticker = entity.get("requested_ticker")
            market = entity.get("market")
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                raise ValueError(f"discovery candidate lacks candidate_id: {entity_id}")
            if candidate_id in seen_candidates:
                raise ValueError(f"duplicate discovery candidate_id: {candidate_id}")
            if not isinstance(ticker, str) or not ticker.strip():
                raise ValueError(f"discovery candidate lacks requested_ticker: {candidate_id}")
            if not isinstance(market, str) or not market.strip():
                raise ValueError(f"discovery candidate lacks market: {candidate_id}")
            if access_status != "direct_available" and not (
                fund_policy == "formal_universe_requested" and access_status == "indirect_only"
            ):
                raise ValueError(f"discovery candidate lacks an eligible requested-market route: {candidate_id}")
            seen_candidates.add(candidate_id)
        seen_entities.add(entity_id)
    if not seen_candidates:
        raise ValueError("discovery baseline requires at least one verified candidate")
    if coverage_status == "coverage_incomplete" and not unresolved_entities:
        raise ValueError("resolved_subset baseline requires at least one unresolved research lead")
    return entities


def reconcile_candidates_with_baseline(
    candidates: list[dict[str, Any]],
    baseline_entities: list[dict[str, Any]],
) -> None:
    baseline = {
        entity["candidate_id"]: entity
        for entity in baseline_entities
        if entity.get("classification") == "candidate"
    }
    registered = {candidate["candidate_id"]: candidate for candidate in candidates}
    missing = sorted(set(baseline) - set(registered))
    unexpected = sorted(set(registered) - set(baseline))
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError("candidate set does not match discovery baseline (" + "; ".join(details) + ")")
    for candidate_id, candidate in registered.items():
        source = baseline[candidate_id]
        if str(candidate["requested_ticker"]).upper() != str(source["requested_ticker"]).upper():
            raise ValueError(f"candidate ticker changed from discovery baseline: {candidate_id}")
        if candidate["market"] != source["market"]:
            raise ValueError(f"candidate market changed from discovery baseline: {candidate_id}")
        path_ids = candidate.get("atomic_path_ids")
        if not isinstance(path_ids, list) or set(path_ids) != set(source["atomic_path_ids"]):
            raise ValueError(f"candidate atomic paths changed from discovery baseline: {candidate_id}")


def validate_finalists(value: Any, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get("finalists"), list):
        raise ValueError("finalists input must be an object with a finalists array")
    candidate_map = {item["candidate_id"]: item for item in candidates}
    finalists = value["finalists"]
    seen_ids: set[str] = set()
    seen_tickers: set[str] = set()
    seen_child_paths: set[str] = set()
    for finalist in finalists:
        if not isinstance(finalist, dict):
            raise ValueError("finalist entries must be objects")
        candidate_id = finalist.get("candidate_id")
        ticker = finalist.get("requested_ticker")
        subjects = finalist.get("relevant_subject_ids")
        if candidate_id not in candidate_map:
            raise ValueError(f"unknown finalist candidate_id: {candidate_id}")
        if candidate_map[candidate_id]["status"] != "advanced":
            raise ValueError(f"finalist is not advanced: {candidate_id}")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("finalist requested_ticker must be a non-empty string")
        candidate = candidate_map[candidate_id]
        if ticker.upper() != str(candidate["requested_ticker"]).upper():
            raise ValueError(f"finalist ticker does not match candidate: {candidate_id}")
        if finalist.get("market") != candidate.get("market"):
            raise ValueError(f"finalist market does not match candidate: {candidate_id}")
        candidate_canonical = candidate.get("canonical_ticker")
        if candidate_canonical and str(finalist.get("canonical_ticker") or "").upper() != str(candidate_canonical).upper():
            raise ValueError(f"finalist canonical_ticker does not match candidate: {candidate_id}")
        if not isinstance(subjects, list) or not all(
            isinstance(item, str) and item.strip() for item in subjects
        ):
            raise ValueError("relevant_subject_ids must be an array of non-empty strings")
        normalized_subjects = {item.upper() for item in subjects}
        finalist_canonical = str(finalist.get("canonical_ticker") or ticker).upper()
        if ticker.upper() not in normalized_subjects or finalist_canonical not in normalized_subjects:
            raise ValueError("relevant_subject_ids must include requested and canonical tickers")
        if candidate_id in seen_ids:
            raise ValueError(f"duplicate finalist candidate_id: {candidate_id}")
        normalized_ticker = ticker.upper()
        if normalized_ticker in seen_tickers:
            raise ValueError(f"duplicate finalist ticker: {ticker}")
        child_path = safe_component(str(finalist.get("canonical_ticker") or ticker))
        if child_path in seen_child_paths:
            raise ValueError(f"duplicate finalist child path: {child_path}")
        seen_ids.add(candidate_id)
        seen_tickers.add(normalized_ticker)
        seen_child_paths.add(child_path)
    advanced_ids = {
        candidate["candidate_id"]
        for candidate in candidates
        if candidate.get("status") == "advanced"
    }
    if seen_ids != advanced_ids:
        details = []
        missing = sorted(advanced_ids - seen_ids)
        unexpected = sorted(seen_ids - advanced_ids)
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError(
            "finalist set must exactly match advanced candidates (" + "; ".join(details) + ")"
        )
    return finalists


def run_tree_errors(run_dir: Path, manifest: dict[str, Any]) -> list[str]:
    """Reject duplicate or ad hoc run artifacts outside the selected profile."""
    profile = manifest.get("artifact_profile", "compact")
    run_type = manifest.get("run_type", "instrument")
    allowed_files = {
        "manifest.json", "state.json", "evidence.json", "complete_report.md",
    }
    allowed_nested_files: set[str] = set()
    if profile == "compact":
        allowed_files.add(STAGE_STORE_FILENAME)
    else:
        state_path = run_dir / "state.json"
        state = load(state_path) if state_path.exists() else {}
        for entry in state.get("artifacts", {}).values():
            if isinstance(entry, dict) and entry.get("storage") == "file":
                path = entry.get("path")
                if isinstance(path, str) and "/" in path:
                    allowed_nested_files.add(path)
        if run_type == "instrument":
            allowed_nested_files.update({
                "1_analysts/market.md", "1_analysts/sentiment.md",
                "1_analysts/news.md", "1_analysts/fundamentals.md",
                "2_research/bull.md", "2_research/bear.md",
                "2_research/manager.md", "3_trading/trader.md",
                "4_risk/aggressive.md", "4_risk/conservative.md",
                "4_risk/neutral.md", "5_portfolio/decision.md",
            })
        else:
            allowed_nested_files.update({
                "0_screening/scope.md", "0_screening/system_map.md",
                "0_screening/candidate_ledger.md", "0_screening/shortlist.md",
            })
            allowed_files.add("comparison.md")
    if run_type == "screening":
        allowed_files.update({"candidates.json", "finalists.json"})

    errors: list[str] = []
    for entry in run_dir.iterdir():
        if entry.name == ".DS_Store":
            continue
        if entry.is_symlink():
            errors.append(f"unexpected run symlink: {entry.name}")
            continue
        if entry.is_file() and entry.name not in allowed_files:
            errors.append(f"unexpected run file for {profile} profile: {entry.name}")
        elif entry.is_dir():
            allowed_directory = entry.name == "candidates" and run_type == "screening"
            allowed_directory = allowed_directory or any(
                path.startswith(entry.name + "/") for path in allowed_nested_files
            )
            if not allowed_directory:
                errors.append(f"unexpected run directory for {profile} profile: {entry.name}")

    if profile == "audit":
        for entry in run_dir.rglob("*"):
            relative = entry.relative_to(run_dir).as_posix()
            if relative == "candidates" or relative.startswith("candidates/"):
                continue
            if entry.is_symlink():
                errors.append(f"unexpected run symlink: {relative}")
            elif entry.is_file() and "/" in relative and relative not in allowed_nested_files:
                errors.append(f"unexpected nested run file for audit profile: {relative}")
            elif entry.is_dir() and not any(
                path == relative or path.startswith(relative + "/")
                for path in allowed_nested_files
            ):
                errors.append(f"unexpected nested run directory for audit profile: {relative}")

    if run_type == "screening" and (run_dir / "candidates").exists():
        finalists_path = run_dir / "finalists.json"
        expected_children: set[str] = set()
        if finalists_path.exists():
            for finalist in load(finalists_path).get("finalists", []):
                ticker = finalist.get("canonical_ticker") or finalist.get("requested_ticker")
                if ticker:
                    expected_children.add(safe_component(str(ticker)))
        for entry in (run_dir / "candidates").iterdir():
            if entry.is_symlink() or not entry.is_dir() or entry.name not in expected_children:
                errors.append(f"unexpected finalist child path: candidates/{entry.name}")
    return errors


def require_clean_run_tree(run_dir: Path, manifest: dict[str, Any]) -> None:
    errors = run_tree_errors(run_dir, manifest)
    if errors:
        raise ValueError("run tree violates artifact profile: " + "; ".join(errors))


def verify_errors(run_dir: Path) -> list[str]:
    manifest_path = run_dir / "manifest.json"
    state_path = run_dir / "state.json"
    if not manifest_path.exists() or not state_path.exists():
        return ["manifest.json or state.json is missing"]
    manifest = load(manifest_path)
    state = load(state_path)
    errors: list[str] = run_tree_errors(run_dir, manifest)
    if state.get("run_id") != manifest.get("run_id"):
        errors.append("state run_id mismatch")
    if state.get("manifest_hash") != digest(manifest):
        errors.append("manifest hash mismatch")
    evidence_path = run_dir / "evidence.json"
    evidence_required = bool(
        manifest.get("evidence_hash")
        or state.get("evidence_hash")
        or state.get("completed_stages")
        or state.get("lifecycle") == "complete"
    )
    if evidence_required and not evidence_path.exists():
        errors.append("required evidence.json is missing")
    elif evidence_path.exists():
        evidence = load(evidence_path)
        evidence_hash = digest(evidence)
        if manifest.get("evidence_hash") != evidence_hash:
            errors.append("evidence hash mismatch")
        if state.get("evidence_hash") != evidence_hash:
            errors.append("state evidence hash mismatch")
        try:
            validate_evidence_bundle(evidence, manifest)
        except ValueError as exc:
            errors.append(f"invalid evidence bundle: {exc}")
    order = stage_order(manifest)
    completed = state.get("completed_stages", [])
    if not isinstance(completed, list) or completed != order[:len(completed)]:
        errors.append("completed stages are not an ordered prefix")
    artifacts = state.get("artifacts", {})
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be an object")
        artifacts = {}
    if set(artifacts) != set(completed):
        errors.append("artifact registry does not match completed stages")
    for stage, entry in artifacts.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            errors.append(f"invalid artifact entry: {stage}")
            continue
        try:
            content = artifact_bytes(run_dir, entry)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid artifact storage for {stage}: {exc}")
            continue
        if digest_bytes(content) != entry["sha256"]:
            errors.append(f"artifact mismatch: {stage}")
    if manifest.get("run_type") == "screening" and manifest.get("research_mode") == "theme":
        baseline_value = state.get("discovery_baseline")
        baseline_hash = state.get("discovery_baseline_hash")
        if baseline_value is None or baseline_hash is None:
            if state.get("lifecycle") in {
                "evidence_frozen", "screening_running", "shortlist_frozen",
                "councils_running", "comparison_ready", "complete",
            }:
                errors.append("theme screening discovery baseline is missing")
        elif baseline_hash != digest(baseline_value):
            errors.append("discovery baseline hash mismatch")
        else:
            try:
                validate_discovery_baseline(baseline_value, manifest)
            except ValueError as exc:
                errors.append(f"invalid discovery baseline: {exc}")
    candidates_path = run_dir / "candidates.json"
    if state.get("candidates_hash") and not candidates_path.exists():
        errors.append("registered candidates.json is missing")
    elif candidates_path.exists() and state.get("candidates_hash") != digest(load(candidates_path)):
        errors.append("candidates hash mismatch")
    finalists_path = run_dir / "finalists.json"
    if state.get("finalists_hash") and not finalists_path.exists():
        errors.append("registered finalists.json is missing")
    elif finalists_path.exists() and state.get("finalists_hash") != digest(load(finalists_path)):
        errors.append("finalists hash mismatch")
    if manifest.get("run_type") == "screening" and state.get("lifecycle") in {
        "shortlist_frozen", "councils_running", "comparison_ready", "complete",
    }:
        if not candidates_path.exists() or not finalists_path.exists():
            errors.append("screening control files are missing")
        else:
            try:
                candidates = validate_candidates(load(candidates_path))
                validate_finalists(load(finalists_path), candidates)
            except ValueError as exc:
                errors.append(f"invalid screening controls: {exc}")
    if manifest.get("run_type") == "screening" and state.get("lifecycle") in {
        "comparison_ready", "complete",
    }:
        ready, pending = child_runs_terminal(run_dir)
        if not ready:
            errors.append("child runs are not terminal and valid: " + ", ".join(pending))
    if manifest.get("run_type", "instrument") == "instrument":
        decision = state.get("final_decision")
        decision_hash = state.get("final_decision_hash")
        decision_required = state.get("lifecycle") in {
            "decision_ready", "decision_registered", "complete",
        }
        if decision_required and (decision is None or decision_hash is None):
            errors.append("registered final decision is missing")
        elif decision is not None:
            if decision_hash != digest(decision):
                errors.append("final decision hash mismatch")
            elif evidence_path.exists():
                try:
                    validate_final_decision(decision, manifest, load(evidence_path))
                except ValueError as exc:
                    errors.append(f"invalid final decision: {exc}")
    if state.get("lifecycle") == "complete" and completed != order:
        errors.append("complete lifecycle missing or unordered stages")
    if state.get("lifecycle") == "failed" and not state.get("failure"):
        errors.append("failed lifecycle without failure metadata")
    return errors


def child_runs_terminal(run_dir: Path) -> tuple[bool, list[str]]:
    finalists_path = run_dir / "finalists.json"
    if not finalists_path.exists():
        return False, ["finalists are not registered"]
    parent_manifest = load(run_dir / "manifest.json")
    finalists = load(finalists_path).get("finalists", [])
    pending = []
    for finalist in finalists:
        ticker = finalist.get("canonical_ticker") or finalist["requested_ticker"]
        child_dir = run_dir / "candidates" / safe_component(ticker)
        child_state_path = child_dir / "state.json"
        child_manifest_path = child_dir / "manifest.json"
        if not child_state_path.exists() or not child_manifest_path.exists():
            pending.append(str(ticker))
            continue
        child_state = load(child_state_path)
        child_manifest = load(child_manifest_path)
        linked = (
            child_manifest.get("run_type") == "instrument"
            and child_manifest.get("parent_screening_run_id") == parent_manifest.get("run_id")
            and child_manifest.get("parent_evidence_hash") == parent_manifest.get("evidence_hash")
            and child_manifest.get("candidate_id") == finalist.get("candidate_id")
            and str(child_manifest.get("requested_ticker") or "").upper()
                == str(finalist.get("requested_ticker") or "").upper()
            and str(child_manifest.get("canonical_ticker") or "").upper()
                == str(ticker).upper()
            and child_manifest.get("market") == finalist.get("market")
        )
        if not linked:
            pending.append(str(ticker))
            continue
        lifecycle = child_state.get("lifecycle")
        if lifecycle not in TERMINAL_LIFECYCLES:
            pending.append(str(ticker))
        elif lifecycle == "failed" and not child_state.get("failure"):
            pending.append(str(ticker))
        elif verify_errors(child_dir):
            pending.append(str(ticker))
    return not pending, pending


def update_lifecycle_after_commit(
    run_dir: Path,
    state: dict[str, Any],
    manifest: dict[str, Any],
    stage: str,
) -> None:
    run_type = manifest.get("run_type", "instrument")
    if run_type == "screening":
        if stage in {"scope", "system_map", "candidate_ledger", "shortlist"}:
            state["lifecycle"] = "screening_running"
        elif stage == "comparison":
            ready, pending = child_runs_terminal(run_dir)
            if not ready:
                raise ValueError("cannot commit comparison; child runs not terminal: " + ", ".join(pending))
            state["lifecycle"] = "comparison_ready"
        elif stage == "complete":
            state["lifecycle"] = "complete"
    else:
        if stage in {"market", "sentiment", "news", "fundamentals"} or re.match(
            r"^(bull|bear|aggressive|conservative|neutral)_\d+$", stage
        ) or stage in {"research_manager", "trader"}:
            state["lifecycle"] = "council_running"
        elif stage == "portfolio_manager":
            state["lifecycle"] = "decision_ready"
        elif stage == "complete":
            state["lifecycle"] = "complete"


def command_init(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    seed = load_json_source(args.manifest)
    common_required = {
        "requested_analysis_date", "analysis_cutoff",
        "execution_mode_requested", "execution_mode_used", "benchmark_ticker",
    }
    run_type = seed.get("run_type", "instrument")
    if run_type not in {"instrument", "screening"}:
        raise ValueError("run_type must be instrument or screening")
    if (
        run_type == "screening"
        and seed.get("research_mode") == "theme"
        and not seed.get("time_horizon")
    ):
        seed["time_horizon"] = "3-12 months"
    required = set(common_required)
    if run_type == "instrument":
        required.add("requested_ticker")
        if seed.get("parent_screening_run_id"):
            required.update({
                "parent_evidence_hash", "candidate_id", "relevant_subject_ids",
            })
    else:
        required.update({
            "research_mode", "market", "time_horizon", "liquidity_requirement",
        })
        if seed.get("research_mode") not in {"theme", "comparison"}:
            raise ValueError("screening research_mode must be theme or comparison")
        if not seed.get("theme") and not seed.get("comparison_label"):
            required.add("theme_or_comparison_label")
    missing = sorted(key for key in required if not seed.get(key))
    if "theme_or_comparison_label" in missing:
        missing.remove("theme_or_comparison_label")
        missing.append("theme or comparison_label")
    if missing:
        raise ValueError("manifest missing required fields: " + ", ".join(missing))
    if seed.get("parent_screening_run_id"):
        subjects = seed.get("relevant_subject_ids")
        if not isinstance(subjects, list) or not subjects or not all(
            isinstance(item, str) and item.strip() for item in subjects
        ):
            raise ValueError("relevant_subject_ids must be a non-empty string array")
    if "portfolio_context" in seed:
        portfolio_context = seed["portfolio_context"]
        if not isinstance(portfolio_context, dict):
            raise ValueError("portfolio_context must be an object when provided")
        if portfolio_context.get("provided_by_user") is not True:
            raise ValueError("portfolio_context must explicitly record provided_by_user: true")
    cutoff = datetime.fromisoformat(str(seed["analysis_cutoff"]).replace("Z", "+00:00"))
    if cutoff.tzinfo is None:
        raise ValueError("analysis_cutoff must be timezone-aware")
    if cutoff.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise ValueError("analysis_cutoff cannot be in the future")
    manifest = dict(seed)
    manifest["run_type"] = run_type
    manifest.setdefault("research_mode", "instrument")
    market_token = str(manifest.get("market", "")).strip().lower()
    if run_type == "screening" and market_token in {
        "us", "u.s.", "us-listed", "u.s.-listed", "united states", "美股",
    }:
        manifest.setdefault("eligible_venues", ["Nasdaq", "NYSE", "NYSE American"])
        manifest.setdefault("eligible_security_types", ["common_stock", "ADR", "ADS"])
        manifest.setdefault("include_otc", False)
        manifest.setdefault("include_funds", False)
    manifest.setdefault("artifact_profile", "compact")
    manifest.setdefault("output_language", "en")
    if not isinstance(manifest["output_language"], str) or not manifest["output_language"].strip():
        raise ValueError("output_language must be a non-empty string")
    manifest.setdefault("macro_context_enabled", True)
    manifest.setdefault("macro_percentile_window", 252)
    manifest.setdefault("technical_percentile_window", 252)
    for field in ("macro_percentile_window", "technical_percentile_window"):
        if isinstance(manifest[field], bool) or not isinstance(manifest[field], int) or manifest[field] < 20:
            raise ValueError(f"{field} must be an integer of at least 20 sessions")
    if "macro_series" in manifest and not isinstance(manifest["macro_series"], list):
        raise ValueError("macro_series must be an array when provided")
    if manifest["artifact_profile"] not in ARTIFACT_PROFILES:
        raise ValueError("artifact_profile must be compact or audit")
    if run_type == "instrument":
        manifest.setdefault("canonical_ticker", seed["requested_ticker"])
        manifest.setdefault("analysts", CORE_ORDER)
        if manifest["analysts"] != CORE_ORDER:
            raise ValueError("complete-port baseline requires all analysts in fixed order")
        manifest.setdefault("investment_debate_rounds", 1)
        manifest.setdefault("risk_debate_rounds", 1)
    manifest.setdefault("schema_version", SCHEMA_VERSION)
    manifest.setdefault("skill_version", "0.4.0")
    manifest.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    manifest["run_id"] = manifest.get("run_id") or digest({
        "subject": manifest.get("requested_ticker") or manifest.get("theme") or manifest.get("comparison_label"),
        "cutoff": manifest.get("analysis_cutoff"),
        "created_at": manifest["created_at"],
    })[:20]
    manifest["resume_signature"] = resume_signature(manifest)
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "manifest_hash": digest(manifest),
        "evidence_hash": manifest.get("evidence_hash"),
        "completed_stages": [],
        "artifacts": {},
        "lifecycle": "initialized",
        "failure": None,
        "discovery_baseline_hash": None,
        "discovery_baseline": None,
        "candidates_hash": None,
        "finalists_hash": None,
        "final_decision_hash": None,
        "final_decision": None,
        "updated_at": manifest["created_at"],
    }
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"run directory is not empty: {run_dir}")
    atomic_write(run_dir / "manifest.json", manifest)
    atomic_write(run_dir / "state.json", state)
    print(json.dumps({"run_dir": str(run_dir), "run_id": manifest["run_id"]}))
    return 0


def command_baseline(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = load(run_dir / "manifest.json")
    require_clean_run_tree(run_dir, manifest)
    state_path = run_dir / "state.json"
    state = load(state_path)
    if manifest.get("run_type") != "screening" or manifest.get("research_mode") != "theme":
        raise ValueError("discovery baseline requires a theme screening run")
    if state.get("lifecycle") != "initialized" or state.get("completed_stages"):
        raise ValueError("register discovery baseline before freezing evidence or committing stages")
    value = load_json_source(args.input)
    entities = validate_discovery_baseline(value, manifest)
    value_hash = digest(value)
    if state.get("discovery_baseline_hash"):
        if state["discovery_baseline_hash"] != value_hash:
            raise ValueError("discovery baseline is already registered with different content")
        print(json.dumps({"discovery_baseline_hash": value_hash, "entity_count": len(entities)}))
        return 0
    state["discovery_baseline_hash"] = value_hash
    state["discovery_baseline"] = value
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(state_path, state)
    counts = {
        classification: sum(entity["classification"] == classification for entity in entities)
        for classification in sorted(DISCOVERY_CLASSIFICATIONS)
    }
    print(json.dumps({
        "discovery_baseline_hash": value_hash,
        "entity_count": len(entities),
        "coverage_status": value["coverage_status"],
        "screening_scope": value.get("screening_scope", "full_universe"),
        "classification_counts": counts,
    }))
    return 0


def command_commit(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = load(run_dir / "manifest.json")
    require_clean_run_tree(run_dir, manifest)
    state = load(run_dir / "state.json")
    if state.get("lifecycle") == "failed":
        raise ValueError("cannot commit to a failed run")
    if not state.get("evidence_hash") or not (run_dir / "evidence.json").exists():
        raise ValueError("freeze evidence before committing artifacts")
    if args.artifact == "-":
        artifact = load_bytes_source("-")
        source = None
    else:
        source = Path(args.artifact)
        if source.suffix.lower() != ".md":
            raise ValueError("role artifacts must be Markdown files")
        artifact = source.read_bytes()
    if not artifact.strip():
        raise ValueError("role artifact is empty")
    portfolio_context = manifest.get("portfolio_context")
    user_portfolio_context = (
        isinstance(portfolio_context, dict)
        and portfolio_context.get("provided_by_user") is True
    )
    if (
        not user_portfolio_context
        and args.stage in {"trader", "portfolio_manager", "comparison", "complete"}
        and contains_percentage_sizing(artifact)
    ):
        raise ValueError("percentage portfolio sizing requires user-provided portfolio context")
    existing = state.get("artifacts", {}).get(args.stage)
    if existing:
        try:
            existing_artifact = artifact_bytes(run_dir, existing)
        except (OSError, ValueError, json.JSONDecodeError):
            existing_artifact = b""
        if existing_artifact and digest_bytes(existing_artifact) == digest_bytes(artifact):
            print(json.dumps(existing))
            return 0
        raise ValueError(f"stage already committed with different content: {args.stage}")
    if not expected_stage(args.stage, state, manifest):
        raise ValueError(f"stage out of order: {args.stage}")
    if (
        args.stage == "complete"
        and manifest.get("run_type", "instrument") == "instrument"
        and not state.get("final_decision_hash")
    ):
        raise ValueError("register the final decision before completing an instrument run")
    update_lifecycle_after_commit(run_dir, state, manifest, args.stage)
    profile = manifest.get("artifact_profile", "compact")
    if args.stage == "complete":
        destination = run_dir / "complete_report.md"
        if source is None or source.resolve() != destination.resolve():
            atomic_write_bytes(destination, artifact)
        entry = {
            "storage": "file",
            "path": str(destination.relative_to(run_dir)),
            "sha256": digest_bytes(artifact),
            "format": "markdown",
        }
    elif profile == "compact":
        destination = run_dir / STAGE_STORE_FILENAME
        if destination.exists():
            bundle = load(destination)
            if bundle.get("schema_version") != SCHEMA_VERSION or not isinstance(bundle.get("stages"), dict):
                raise ValueError("invalid compact stage bundle")
        else:
            bundle = {"schema_version": SCHEMA_VERSION, "stages": {}}
        bundle["stages"][args.stage] = artifact.decode("utf-8")
        atomic_write(destination, bundle)
        entry = {
            "storage": "bundle",
            "path": STAGE_STORE_FILENAME,
            "key": args.stage,
            "sha256": digest_bytes(artifact),
            "format": "markdown",
        }
    else:
        destination = run_dir / "artifacts" / f"{safe_component(args.stage)}.md"
        atomic_write_bytes(destination, artifact)
        entry = {
            "storage": "file",
            "path": str(destination.relative_to(run_dir)),
            "sha256": digest_bytes(artifact),
            "format": "markdown",
        }
    if args.stage not in state["completed_stages"]:
        state["completed_stages"].append(args.stage)
    state["artifacts"][args.stage] = entry
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(run_dir / "state.json", state)
    print(json.dumps(state["artifacts"][args.stage]))
    return 0


def command_freeze(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest_path = run_dir / "manifest.json"
    state_path = run_dir / "state.json"
    manifest = load(manifest_path)
    require_clean_run_tree(run_dir, manifest)
    state = load(state_path)
    if state.get("lifecycle") == "failed":
        raise ValueError("cannot freeze a failed run")
    if state.get("completed_stages"):
        raise ValueError("cannot replace evidence after role artifacts are committed")
    if (
        manifest.get("run_type") == "screening"
        and manifest.get("research_mode") == "theme"
        and not state.get("discovery_baseline_hash")
    ):
        raise ValueError("register the discovery baseline before freezing evidence")
    evidence = load_json_source(args.evidence)
    validate_evidence_bundle(evidence, manifest)
    frozen_path = run_dir / "evidence.json"
    frozen_hash = digest(evidence)
    if frozen_path.exists():
        if digest(load(frozen_path)) != frozen_hash:
            raise ValueError("run already contains different frozen evidence")
        if (
            manifest.get("evidence_hash") == frozen_hash
            and state.get("evidence_hash") == frozen_hash
        ):
            print(json.dumps({
                "evidence_hash": frozen_hash,
                "resume_signature": manifest["resume_signature"],
            }))
            return 0
    atomic_write(frozen_path, evidence)
    manifest["evidence_hash"] = frozen_hash
    manifest["evidence_frozen_at"] = datetime.now(timezone.utc).isoformat()
    manifest["resume_signature"] = resume_signature(manifest)
    atomic_write(manifest_path, manifest)
    state["manifest_hash"] = digest(manifest)
    state["evidence_hash"] = frozen_hash
    state["lifecycle"] = "evidence_frozen"
    state["updated_at"] = manifest["evidence_frozen_at"]
    atomic_write(state_path, state)
    print(json.dumps({"evidence_hash": frozen_hash, "resume_signature": manifest["resume_signature"]}))
    return 0


def command_candidates(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = load(run_dir / "manifest.json")
    require_clean_run_tree(run_dir, manifest)
    state_path = run_dir / "state.json"
    state = load(state_path)
    if manifest.get("run_type") != "screening":
        raise ValueError("candidate registration requires a screening run")
    if "shortlist" not in state.get("completed_stages", []):
        raise ValueError("commit shortlist before registering candidates")
    value = load_json_source(args.input)
    candidates = validate_candidates(value)
    if manifest.get("research_mode") == "theme":
        baseline_value = state.get("discovery_baseline")
        if not isinstance(baseline_value, dict):
            raise ValueError("register the discovery baseline before candidates")
        baseline_entities = validate_discovery_baseline(baseline_value, manifest)
        if state.get("discovery_baseline_hash") != digest(baseline_value):
            raise ValueError("discovery baseline hash mismatch")
        reconcile_candidates_with_baseline(candidates, baseline_entities)
    destination = run_dir / "candidates.json"
    value_hash = digest(value)
    if destination.exists():
        if digest(load(destination)) != value_hash:
            raise ValueError("candidates are already registered with different content")
        print(json.dumps({"candidates_hash": value_hash, "count": len(candidates)}))
        return 0
    if state.get("lifecycle") in TERMINAL_LIFECYCLES:
        raise ValueError("cannot register candidates on a terminal run")
    advanced = [
        candidate for candidate in candidates
        if candidate.get("status") == "advanced"
    ]
    if advanced:
        usable = validate_evidence_bundle(load(run_dir / "evidence.json"), manifest)
        if not usable:
            raise ValueError("cannot advance candidates without usable frozen evidence")
        for candidate in advanced:
            candidate_id = candidate["candidate_id"]
            subjects = {
                str(candidate["requested_ticker"]).upper(),
                str(candidate.get("canonical_ticker") or candidate["requested_ticker"]).upper(),
            }
            if not any(
                record.get("evidence_strength") in {"strong", "medium"}
                and record.get("evidence_kind") != "unverified_lead"
                and (
                    candidate_id in record.get("candidate_ids", [])
                    or str(record.get("subject_id") or "").upper() in subjects
                )
                for record in usable
            ):
                raise ValueError(
                    f"advanced candidate lacks qualifying frozen evidence: {candidate_id}"
                )
    atomic_write(destination, value)
    state["candidates_hash"] = value_hash
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(state_path, state)
    print(json.dumps({"candidates_hash": value_hash, "count": len(value["candidates"])}))
    return 0


def command_finalists(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = load(run_dir / "manifest.json")
    require_clean_run_tree(run_dir, manifest)
    state_path = run_dir / "state.json"
    state = load(state_path)
    if manifest.get("run_type") != "screening":
        raise ValueError("finalist registration requires a screening run")
    candidates_path = run_dir / "candidates.json"
    if not candidates_path.exists():
        raise ValueError("register candidates before finalists")
    candidates_value = load(candidates_path)
    candidates = validate_candidates(candidates_value)
    value = load_json_source(args.input)
    finalists = validate_finalists(value, candidates)
    usable = validate_evidence_bundle(load(run_dir / "evidence.json"), manifest)
    for finalist in finalists:
        subjects = {item.upper() for item in finalist["relevant_subject_ids"]}
        candidate_id = finalist["candidate_id"]
        if not any(
            record.get("evidence_strength") in {"strong", "medium"}
            and record.get("evidence_kind") != "unverified_lead"
            and (
                candidate_id in record.get("candidate_ids", [])
                or str(record.get("subject_id") or "").upper() in subjects
            )
            for record in usable
        ):
            raise ValueError(
                f"finalist lacks candidate-relevant frozen evidence: {candidate_id}"
            )
    destination = run_dir / "finalists.json"
    value_hash = digest(value)
    if destination.exists():
        if digest(load(destination)) != value_hash:
            raise ValueError("finalists are already registered with different content")
        print(json.dumps({"finalists_hash": value_hash, "count": len(finalists)}))
        return 0
    if state.get("lifecycle") in TERMINAL_LIFECYCLES:
        raise ValueError("cannot register finalists on a terminal run")
    atomic_write(destination, value)
    state["finalists_hash"] = value_hash
    state["lifecycle"] = "shortlist_frozen"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(state_path, state)
    print(json.dumps({"finalists_hash": value_hash, "count": len(finalists)}))
    return 0


def command_start_councils(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = load(run_dir / "manifest.json")
    require_clean_run_tree(run_dir, manifest)
    state_path = run_dir / "state.json"
    state = load(state_path)
    if manifest.get("run_type") != "screening":
        raise ValueError("start-councils requires a screening run")
    if state.get("lifecycle") == "councils_running":
        print(json.dumps({"lifecycle": state["lifecycle"]}))
        return 0
    if state.get("lifecycle") != "shortlist_frozen":
        raise ValueError("register and freeze finalists before starting councils")
    if not (run_dir / "finalists.json").exists():
        raise ValueError("finalists.json is missing")
    state["lifecycle"] = "councils_running"
    state["councils_started_at"] = datetime.now(timezone.utc).isoformat()
    state["updated_at"] = state["councils_started_at"]
    atomic_write(state_path, state)
    print(json.dumps({"lifecycle": state["lifecycle"]}))
    return 0


def command_decision(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    manifest = load(run_dir / "manifest.json")
    require_clean_run_tree(run_dir, manifest)
    state_path = run_dir / "state.json"
    state = load(state_path)
    if manifest.get("run_type", "instrument") != "instrument":
        raise ValueError("final decision registration requires an instrument run")
    value = load_json_source(args.input)
    evidence_path = run_dir / "evidence.json"
    if not evidence_path.exists():
        raise ValueError("freeze evidence before registering a final decision")
    validate_final_decision(value, manifest, load(evidence_path))
    value_hash = digest(value)
    if state.get("final_decision_hash"):
        if state["final_decision_hash"] != value_hash:
            raise ValueError("final decision is already registered with different content")
        print(json.dumps({"final_decision_hash": value_hash}))
        return 0
    if state.get("lifecycle") != "decision_ready":
        raise ValueError("complete the Portfolio Manager stage before registering a final decision")
    state["final_decision_hash"] = value_hash
    state["final_decision"] = value
    state["lifecycle"] = "decision_registered"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write(state_path, state)
    print(json.dumps({
        "final_decision_hash": value_hash,
        "rating": value["rating"],
        "exposure_intent": value["exposure_intent"],
        "confidence": value["confidence"],
    }))
    return 0


def command_fail(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    state_path = run_dir / "state.json"
    state = load(state_path)
    if state.get("lifecycle") == "complete":
        raise ValueError("cannot fail a complete run")
    failure = {
        "failed_stage": args.stage,
        "reason": args.reason,
        "failed_at": datetime.now(timezone.utc).isoformat(),
    }
    if state.get("lifecycle") == "failed":
        if state.get("failure", {}).get("failed_stage") == args.stage and state.get("failure", {}).get("reason") == args.reason:
            print(json.dumps(state["failure"]))
            return 0
        raise ValueError("run is already failed with different metadata")
    state["lifecycle"] = "failed"
    state["failure"] = failure
    state["updated_at"] = failure["failed_at"]
    atomic_write(state_path, state)
    print(json.dumps(failure))
    return 0


def command_verify(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    errors = verify_errors(run_dir)
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


def command_doctor(args: argparse.Namespace) -> int:
    scripts_dir = Path(getattr(args, "scripts_dir", None) or Path(__file__).parent)
    required = package_status(REQUIRED_PACKAGES)
    result = {
        "python": platform.python_version(),
        "python_supported": (3, 10) <= sys.version_info[:2] <= (3, 13),
        "required": required,
        "missing_required": [name for name, available in required.items() if not available],
        "forbidden_script_calls": scan_scripts(scripts_dir),
    }
    result["ok"] = (
        result["python_supported"]
        and not result["missing_required"]
        and not result["forbidden_script_calls"]
    )
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("OK" if result["ok"] else "NOT READY")
        if result["missing_required"]:
            print("Missing required: " + ", ".join(result["missing_required"]))
            print("Install with: python -m pip install -r requirements.txt")
        if result["forbidden_script_calls"]:
            print("Forbidden external LLM or Codex invocation found in scripts")
    return 0 if result["ok"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--manifest", required=True, help="Manifest JSON path or - for stdin")
    init.add_argument("--run-dir", required=True)
    init.set_defaults(func=command_init)
    baseline = sub.add_parser("baseline")
    baseline.add_argument("--run-dir", required=True)
    baseline.add_argument("--input", required=True, help="Discovery baseline JSON path or - for stdin")
    baseline.set_defaults(func=command_baseline)
    commit = sub.add_parser("commit")
    commit.add_argument("--run-dir", required=True)
    commit.add_argument("--stage", required=True)
    commit.add_argument("--artifact", required=True, help="Markdown artifact path or - for stdin")
    commit.set_defaults(func=command_commit)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--run-dir", required=True)
    freeze.add_argument("--evidence", required=True, help="Evidence JSON path or - for stdin")
    freeze.set_defaults(func=command_freeze)
    candidates = sub.add_parser("candidates")
    candidates.add_argument("--run-dir", required=True)
    candidates.add_argument("--input", required=True, help="Candidates JSON path or - for stdin")
    candidates.set_defaults(func=command_candidates)
    finalists = sub.add_parser("finalists")
    finalists.add_argument("--run-dir", required=True)
    finalists.add_argument("--input", required=True, help="Finalists JSON path or - for stdin")
    finalists.set_defaults(func=command_finalists)
    start_councils = sub.add_parser("start-councils")
    start_councils.add_argument("--run-dir", required=True)
    start_councils.set_defaults(func=command_start_councils)
    decision = sub.add_parser("decision")
    decision.add_argument("--run-dir", required=True)
    decision.add_argument("--input", required=True, help="Final decision JSON path or - for stdin")
    decision.set_defaults(func=command_decision)
    fail = sub.add_parser("fail")
    fail.add_argument("--run-dir", required=True)
    fail.add_argument("--stage", required=True)
    fail.add_argument("--reason", required=True)
    fail.set_defaults(func=command_fail)
    verify = sub.add_parser("verify")
    verify.add_argument("--run-dir", required=True)
    verify.set_defaults(func=command_verify)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true", dest="as_json")
    doctor.add_argument("--scripts-dir")
    doctor.set_defaults(func=command_doctor)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
