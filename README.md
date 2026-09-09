# Investment Council

An evidence-grounded Codex skill for investment research, trading analysis, theme discovery, stock screening, and multi-company comparison.

It combines progressive candidate screening with complete multi-role investment councils. Market data, compact VIX/rates/FX context, technical indicators and historical percentiles, frozen evidence, run state, and report assembly are handled deterministically; Codex performs the research judgment, debate, risk analysis, and final writing.

## Install

This single-skill repository keeps `SKILL.md` at its root. Clone the complete repository into the Codex skills directory so every script and reference is installed:

```bash
git clone https://github.com/HuaiL22/investment-council.git ~/.codex/skills/investment-council
```

The repository is public, so cloning does not require GitHub authentication. To update an existing installation, run:

```bash
git -C ~/.codex/skills/investment-council pull --ff-only
```

The skill becomes available after Codex detects the installation; start a new task if it does not appear immediately.

## Requirements

- Python 3.10–3.13
- `numpy`, `pandas`, and `yfinance`
- Web access for current public-source research

Install the Python dependencies when needed:

```bash
python -m pip install -r ~/.codex/skills/investment-council/requirements.txt
```

The skill checks its environment before a run and does not install packages without permission.

## Use

Invoke it explicitly:

```text
$investment-council 分析苹果当前的投资与交易价值
$investment-council 筛选 AI 数据中心供电产业链，并给出经过完整委员会讨论的候选
```

For an unqualified “U.S.-listed” or “美股” request, the default security boundary is common shares and direct ADR/ADS listed on Nasdaq, NYSE, or NYSE American. OTC securities and funds are excluded unless the request explicitly includes them. Theme runs default to a 3–12 month research horizon unless the user supplies another horizon.

It supports:

- Single-stock, ETF, index, and crypto analysis
- Entity-first theme discovery that completes a requested-market route waterfall from primary and cross-listings through ADR/ADS and corporate actions, then uses conditional ETF references only when no direct route exists
- Independent omission review and substantive path-coverage checks before screening
- Early candidate identity, liquidity, and lightweight market-data auditing
- A shared macro snapshot with VIX, U.S. 2-year and 10-year Treasury yields, 2s10s, DXY, optional issuer-relevant FX, 20/60-session changes, and 252-session percentiles
- Per-instrument RSI, moving-average, MACD, ATR, price/RSI/ATR percentile, slope, relative-strength, and trend-regime analysis
- Two-stage screening that locks either a full-universe or resolved-subset discovery baseline before company decisions, preserves atomic-path membership and unresolved research leads, follows non-terminal corporate actions to the cutoff, forbids invented liquidity gates, and requires expectations, valuation, catalysts, downside, and like-for-like nearest-alternative comparisons before advancement
- User-supplied company comparisons
- Evidence-backed Bull/Bear debate, risk review, and portfolio conclusions
- Current or historical analysis with a fixed evidence cutoff

Chat requests return one report without leaving a run directory. When a saved or resumable run is requested, the default compact profile stores one frozen evidence bundle, one stage bundle, minimal state, and one final report. Separate role files are available only through an explicit audit run.

Outputs are research material, not personalized financial advice or a promise of returns.
