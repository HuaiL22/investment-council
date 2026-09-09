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


def base_role(stage: str) -> str:
    return re.sub(r"_\d+$", "", stage)


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
    if not args.allow_partial:
        missing = [stage for stage in expected_stages(manifest) if stage not in state.get("artifacts", {})]
        if missing:
            raise ValueError("cannot assemble final report; missing stages: " + ", ".join(missing))
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
                chunks.append(f"## {stage.replace('_', ' ').title()}\n\n{report}")
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
            "# Complete Investment Council Screening Report",
            "",
            f"Mode: **{manifest.get('research_mode')}**",
            f"Theme or comparison: **{manifest.get('theme') or manifest.get('comparison_label')}**",
            f"Market: **{manifest.get('market')}**",
            f"Analysis cutoff: **{manifest.get('analysis_cutoff')}**",
            f"Execution mode: **{manifest.get('execution_mode_used')}**",
            "",
        ]
    else:
        header = [
            "# Complete Investment Council Report",
            "",
            f"Requested ticker: **{manifest.get('requested_ticker')}**",
            f"Canonical ticker: **{manifest.get('canonical_ticker')}**",
            f"Analysis cutoff: **{manifest.get('analysis_cutoff')}**",
            f"Execution mode: **{manifest.get('execution_mode_used')}**",
            f"Hypothetical: **{manifest.get('hypothetical', True)}**",
            "",
        ]
    body = header[:]
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
