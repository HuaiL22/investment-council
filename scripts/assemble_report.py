#!/usr/bin/env python3
"""Assemble natural-language role reports into the canonical report tree."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

INSTRUMENT_PATHS = {
    "market": "1_analysts/market.md",
    "sentiment": "1_analysts/sentiment.md",
    "news": "1_analysts/news.md",
    "fundamentals": "1_analysts/fundamentals.md",
    "bull": "2_research/bull.md",
    "bear": "2_research/bear.md",
    "research_manager": "2_research/manager.md",
    "trader": "3_trading/trader.md",
    "aggressive": "4_risk/aggressive.md",
    "conservative": "4_risk/conservative.md",
    "neutral": "4_risk/neutral.md",
    "portfolio_manager": "5_portfolio/decision.md",
}
SCREENING_PATHS = {
    "scope": "0_screening/scope.md",
    "system_map": "0_screening/system_map.md",
    "candidate_ledger": "0_screening/candidate_ledger.md",
    "shortlist": "0_screening/shortlist.md",
    "comparison": "comparison.md",
}
REPORT_LABELS = {
    "en": {
        "screening_title": "# Complete Investment Council Screening Report",
        "instrument_title": "# Complete Investment Council Report",
        "mode": "Mode", "subject": "Theme or comparison", "market": "Market",
        "cutoff": "Analysis cutoff", "execution": "Execution mode",
        "requested": "Requested ticker", "canonical": "Canonical ticker",
        "hypothetical": "Hypothetical", "decision": "## Registered final decision",
        "decision_columns": "| Rating | Action | Exposure intent | Confidence | Macro effect | Technical effect |",
        "invalidation": "Invalidation", "finalists": "## Verified finalist decisions",
        "finalist_columns": "| Security | Council status | Rating | Action | Exposure | Confidence | Macro | Technical |",
        "candidates": "## Complete candidate disposition registry",
        "candidate_columns": "| Security | Atomic path | State | Decisive reason | Next required evidence | Re-entry condition |",
        "leads": "## Unresolved research leads",
        "lead_columns": "| Entity | Atomic path | Potential impact | Missing fact | Next check |",
    },
    "zh": {
        "screening_title": "# 完整投资委员会主题研究报告",
        "instrument_title": "# 完整投资委员会个股研究报告",
        "mode": "研究模式", "subject": "主题或比较对象", "market": "市场",
        "cutoff": "分析截止时间", "execution": "实际执行模式",
        "requested": "请求代码", "canonical": "当前代码",
        "hypothetical": "是否为假设性研究", "decision": "## 已注册的最终决策",
        "decision_columns": "| 研究评级 | 当前动作 | 敞口意图 | 置信度 | 宏观影响 | 技术面影响 |",
        "invalidation": "失效条件", "finalists": "## 已验证的入围公司决策",
        "finalist_columns": "| 证券 | 评审状态 | 研究评级 | 当前动作 | 敞口意图 | 置信度 | 宏观 | 技术面 |",
        "candidates": "## 完整候选处置表",
        "candidate_columns": "| 证券 | 原子路径 | 状态 | 决定性原因 | 下一项所需证据 | 重新进入条件 |",
        "leads": "## 尚未解决的研究线索",
        "lead_columns": "| 实体 | 原子路径 | 潜在影响 | 缺失事实 | 下一步核验 |",
    },
}
ZH_STAGE_LABELS = {
    "market": "市场与技术面", "sentiment": "市场情绪", "news": "新闻与事件",
    "fundamentals": "基本面", "bull": "多方研究", "bear": "空方研究",
    "research_manager": "研究经理", "trader": "交易执行",
    "aggressive": "激进风险评审", "conservative": "保守风险评审",
    "neutral": "中性风险评审", "portfolio_manager": "组合经理",
}
ZH_VALUE_LABELS = {
    "Buy": "买入", "Overweight": "增持", "Hold": "持有",
    "Underweight": "减持", "Sell": "卖出",
    "open_long": "建立多头", "add_long": "增加多头", "hold": "持有",
    "reduce_long": "减少多头", "close_long": "退出多头",
    "open_short": "建立空头", "add_short": "增加空头",
    "reduce_short": "减少空头", "close_short": "平空", "avoid": "回避",
    "low": "低", "medium": "中", "high": "高",
    "supportive": "支持", "neutral": "中性", "adverse": "不利",
    "mixed": "混合", "unavailable": "不可用",
    "insufficient_history": "历史不足",
    "initialized": "已初始化", "evidence_frozen": "证据已冻结",
    "screening_running": "筛选中", "shortlist_frozen": "入围名单已冻结",
    "councils_running": "综合评审中", "council_running": "综合评审中",
    "comparison_ready": "待综合比较", "decision_ready": "待注册决策",
    "decision_registered": "决策已注册", "complete": "已完成",
    "failed": "失败", "missing": "缺失",
    "discovered": "已发现", "researching": "研究中",
    "pending_verification": "待核验", "advanced": "已晋级",
    "eliminated": "已剔除", "lower": "较低",
}


def base_role(stage: str) -> str:
    return re.sub(r"_\d+$", "", stage)


def safe_component(value: str) -> str:
    return (re.sub(r"[^A-Za-z0-9._=-]+", "_", str(value)).strip("._") or "item")[:96]


def report_language(manifest: dict) -> str:
    token = str(manifest.get("output_language") or manifest.get("language") or "").lower()
    return "zh" if token.startswith("zh") or "chinese" in token or "中文" in token else "en"


def stage_heading(stage: str, manifest: dict) -> str:
    if report_language(manifest) != "zh":
        return stage.replace("_", " ").title()
    role = base_role(stage)
    label = ZH_STAGE_LABELS.get(role, stage.replace("_", " "))
    match = re.search(r"_(\d+)$", stage)
    return f"{label} {match.group(1)}" if match else label


def expected_stages(manifest: dict) -> list[str]:
    if manifest.get("run_type", "instrument") == "screening":
        return list(SCREENING_PATHS)
    stages = ["market", "sentiment", "news", "fundamentals"]
    for index in range(1, int(manifest.get("investment_debate_rounds", 1)) + 1):
        stages.extend([f"bull_{index}", f"bear_{index}"])
    stages.extend(["research_manager", "trader"])
    for index in range(1, int(manifest.get("risk_debate_rounds", 1)) + 1):
        stages.extend([f"aggressive_{index}", f"conservative_{index}", f"neutral_{index}"])
    stages.append("portfolio_manager")
    return stages


def path_map(manifest: dict) -> dict[str, str]:
    if manifest.get("run_type", "instrument") == "screening":
        return SCREENING_PATHS
    return INSTRUMENT_PATHS


def read_artifact(run_dir: Path, entry: dict) -> str:
    path = run_dir / entry["path"]
    if entry.get("storage") == "bundle":
        bundle = json.loads(path.read_text(encoding="utf-8"))
        content = bundle.get("stages", {}).get(entry.get("key"))
        if not isinstance(content, str):
            raise ValueError(f"missing bundled stage: {entry.get('key')}")
        return content.strip()
    return path.read_text(encoding="utf-8").strip()


def markdown_cell(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "—"


def localized_cell(value, language: str) -> str:
    if language != "zh":
        return markdown_cell(value)
    if isinstance(value, list):
        value = [ZH_VALUE_LABELS.get(str(item), item) for item in value]
    else:
        value = ZH_VALUE_LABELS.get(str(value), value)
    return markdown_cell(value)


def instrument_decision_section(
    state: dict, labels: dict[str, str], language: str,
) -> str | None:
    decision = state.get("final_decision")
    if not isinstance(decision, dict):
        return None
    return "\n".join([
        labels["decision"],
        "",
        labels["decision_columns"],
        "|---|---|---|---|---|---|",
        "| " + " | ".join(localized_cell(decision.get(field), language) for field in (
            "rating", "action", "exposure_intent", "confidence",
            "macro_effect", "technical_effect",
        )) + " |",
        "",
        markdown_cell(decision.get("decision_summary")),
        "",
        f"{labels['invalidation']}: {markdown_cell(decision.get('invalidation'))}",
    ])


def screening_registry_sections(
    run_dir: Path, state: dict, labels: dict[str, str], language: str,
) -> list[str]:
    sections: list[str] = []
    finalists_path = run_dir / "finalists.json"
    if finalists_path.exists():
        lines = [
            labels["finalists"],
            "",
            labels["finalist_columns"],
            "|---|---|---|---|---|---|---|---|",
        ]
        for finalist in json.loads(finalists_path.read_text(encoding="utf-8")).get("finalists", []):
            ticker = finalist.get("canonical_ticker") or finalist.get("requested_ticker")
            child_dir = run_dir / "candidates" / safe_component(str(ticker))
            child_state_path = child_dir / "state.json"
            child_state = (
                json.loads(child_state_path.read_text(encoding="utf-8"))
                if child_state_path.exists() else {}
            )
            decision = child_state.get("final_decision") or {}
            lines.append("| " + " | ".join((
                markdown_cell(ticker),
                localized_cell(child_state.get("lifecycle", "missing"), language),
                localized_cell(decision.get("rating"), language),
                localized_cell(decision.get("action"), language),
                localized_cell(decision.get("exposure_intent"), language),
                localized_cell(decision.get("confidence"), language),
                localized_cell(decision.get("macro_effect"), language),
                localized_cell(decision.get("technical_effect"), language),
            )) + " |")
        sections.append("\n".join(lines))

    candidates_path = run_dir / "candidates.json"
    if candidates_path.exists():
        lines = [
            labels["candidates"],
            "",
            labels["candidate_columns"],
            "|---|---|---|---|---|---|",
        ]
        for candidate in json.loads(candidates_path.read_text(encoding="utf-8")).get("candidates", []):
            lines.append("| " + " | ".join((
                markdown_cell(candidate.get("canonical_ticker") or candidate.get("requested_ticker")),
                markdown_cell(candidate.get("atomic_path_ids")),
                localized_cell(candidate.get("status"), language),
                markdown_cell(candidate.get("transition_reason")),
                markdown_cell(candidate.get("next_required_evidence")),
                markdown_cell(candidate.get("reentry_condition")),
            )) + " |")
        sections.append("\n".join(lines))

    baseline = state.get("discovery_baseline")
    if isinstance(baseline, dict):
        leads = [
            entity for entity in baseline.get("entities", [])
            if entity.get("classification") == "research_lead"
        ]
        if leads:
            lines = [
                labels["leads"],
                "",
                labels["lead_columns"],
                "|---|---|---|---|---|",
            ]
            for entity in leads:
                lines.append("| " + " | ".join((
                    markdown_cell(entity.get("entity_name") or entity.get("entity_id")),
                    markdown_cell(entity.get("atomic_path_ids")),
                    localized_cell(entity.get("impact_level"), language),
                    markdown_cell(entity.get("unresolved_fact") or entity.get("disposition_reason")),
                    markdown_cell(entity.get("next_check")),
                )) + " |")
            sections.append("\n".join(lines))
    return sections


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument(
        "--render-stage-files",
        action="store_true",
        help="Explicitly render a secondary human-readable stage tree",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    language = report_language(manifest)
    labels = REPORT_LABELS[language]
    if not args.allow_partial:
        missing = [stage for stage in expected_stages(manifest) if stage not in state.get("artifacts", {})]
        if missing:
            raise ValueError("cannot assemble final report; missing stages: " + ", ".join(missing))
        if manifest.get("run_type", "instrument") == "instrument" and not state.get("final_decision"):
            raise ValueError("cannot assemble final report; registered final decision is missing")
    paths = path_map(manifest)
    order = list(paths)
    grouped: dict[str, list[tuple[str, str]]] = {role: [] for role in order}

    for stage in state.get("completed_stages", []):
        entry = state.get("artifacts", {}).get(stage)
        if not entry:
            continue
        role = base_role(stage)
        if role in grouped:
            grouped[role].append((stage, read_artifact(run_dir, entry)))

    rendered_paths: list[Path] = []
    rendered_sections: list[str] = []
    for role in order:
        reports = grouped[role]
        if not reports:
            continue
        chunks = []
        for stage, report in reports:
            if len(reports) > 1:
                chunks.append(f"## {stage_heading(stage, manifest)}\n\n{report}")
            else:
                chunks.append(report)
        rendered = "\n\n---\n\n".join(chunks).rstrip()
        rendered_sections.append(rendered)
        if args.render_stage_files:
            destination = run_dir / paths[role]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(rendered + "\n", encoding="utf-8")
            rendered_paths.append(destination)

    if manifest.get("run_type", "instrument") == "screening":
        header = [
            labels["screening_title"],
            "",
            f"{labels['mode']}: **{manifest.get('research_mode')}**",
            f"{labels['subject']}: **{manifest.get('theme') or manifest.get('comparison_label')}**",
            f"{labels['market']}: **{manifest.get('market')}**",
            f"{labels['cutoff']}: **{manifest.get('analysis_cutoff')}**",
            f"{labels['execution']}: **{manifest.get('execution_mode_used')}**",
            "",
        ]
    else:
        header = [
            labels["instrument_title"],
            "",
            f"{labels['requested']}: **{manifest.get('requested_ticker')}**",
            f"{labels['canonical']}: **{manifest.get('canonical_ticker')}**",
            f"{labels['cutoff']}: **{manifest.get('analysis_cutoff')}**",
            f"{labels['execution']}: **{manifest.get('execution_mode_used')}**",
            f"{labels['hypothetical']}: **{manifest.get('hypothetical', True)}**",
            "",
        ]
    body = header[:]
    if manifest.get("run_type", "instrument") == "screening":
        for section in screening_registry_sections(run_dir, state, labels, language):
            body.extend([section, "", "---", ""])
    else:
        decision_section = instrument_decision_section(state, labels, language)
        if decision_section:
            body.extend([decision_section, "", "---", ""])
    for section in rendered_sections:
        body.extend(["---", "", section, ""])
    complete = run_dir / "complete_report.md"
    complete.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({
        "reports": [str(path) for path in rendered_paths],
        "stage_count": sum(len(items) for items in grouped.values()),
        "complete_report": str(complete),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
