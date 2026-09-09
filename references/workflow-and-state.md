# Workflow and state

The skill supports instrument runs and screening runs while using natural-language Markdown throughout.

## Manifest

Every manifest records run type, research mode, analysis cutoff, output language, requested and actual execution mode, benchmark, macro-context policy, macro and technical percentile windows, source statuses, skill version, and `artifact_profile` (`compact` by default; `audit` only when explicitly needed).

- Instrument runs also record requested and canonical ticker, identity, exchange, timezone, asset type, debate rounds, portfolio context, and optional parent screening run ID and evidence hash.
- Screening runs record theme or comparison label, market, horizon, liquidity requirement, and child candidates. When a United States market scope omits venue details, `state_store.py init` records Nasdaq, NYSE, and NYSE American common shares and direct ADR/ADS as the eligible boundary, with OTC securities and funds excluded unless explicitly overridden. When a theme horizon is absent, initialization records the disclosed 3–12 month default.

Macro context is enabled by default with a 252-session percentile window. The default series are VIX, the U.S. 2-year and 10-year Treasury yields, and DXY; derive 2s10s only when both yield observations share the same date. `macro_series` may replace the source series with validated `key`, `ticker`, `label`, `kind`, and `unit` entries. Use `kind: yield` for basis-point changes and `kind: fx` for relevant currency pairs. The technical percentile window also defaults to 252 sessions. These settings participate in the resume signature.

Treat the requested historical cutoff as now. Preserve a requested ticker even when a provider returns a normalized symbol.

## Instrument stage order

1. market, sentiment, news, fundamentals
2. Bull then Bear for each investment-debate round
3. Research Manager
4. Trader
5. Aggressive, Conservative, then Neutral for each risk round
6. Portfolio Manager
7. register final decision
8. complete

Analysts may run concurrently. Debate turns remain sequential. Partial source coverage never removes a role; the role explains the limitation. A totally unusable instrument bundle stops before all roles and produces no council rating.

## Screening stage order

1. scope
2. system map
3. candidate ledger
4. shortlist
5. comparison after every finalist child is complete or failed
6. complete

For a theme run, register the candidate-pool baseline immediately after initialization and before evidence freeze. Use a full-universe baseline when coverage is complete or a resolved-subset baseline when bounded unresolved research leads remain. `state_store.py baseline` stores its hash and full entity/path inventory inside `state.json`, so it adds no durable artifact. After shortlist, register immutable `candidates.json` and `finalists.json`, then start independent child councils. Candidate registration must exactly match the baseline's verified candidate IDs, tickers, markets, and atomic-path memberships; unresolved research leads remain outside the candidate and finalist sets and limit the final conclusion's scope. Finalist workers own separate directories and never write shared decision memory concurrently. An isolated worker owns exactly one finalist, reads that child's frozen `evidence.json` directly, and returns Markdown to the controller. Do not ask one worker to draft multiple councils, reason only from conversation summaries, or edit the run tree.

## Role artifacts

Every role returns natural-language Markdown with headings, tables, and evidence citations. Do not require JSON envelopes or hidden claim ledgers. Stream role output to the controller; do not create one temporary file per role.

In the default compact profile, the controller stores each role exactly once inside `stages.json`, records its content hash in `state.json`, and later assembles `complete_report.md` directly from that store. In explicit audit profile, store one `artifacts/STAGE.md` per role instead. Never persist both representations, and never generate a second canonical role directory unless `--render-stage-files` is explicitly requested for debugging.

Control metadata is allowed to be JSON:

- `candidates.json` stores final screening states.
- `finalists.json` stores membership and relevant subject IDs.
- `state.json` stores the registered candidate-pool baseline and hash for theme-run conservation.
- `state.json` stores an instrument's validated final decision and evidence references.
- manifest, evidence, and state files support deterministic resume and verification.

These files do not constrain natural-language reasoning.

Registration inputs use small deterministic contracts:

- Every candidate row includes `candidate_id`, requested ticker, market, atomic paths, status, `transition_reason`, and `next_required_evidence`. Eliminated and pending rows also include `reentry_condition`.
- Every instrument decision includes schema version, rating, Trader action, exposure intent, confidence, macro effect, technical effect, sizing basis, at least two usable frozen `evidence_ids`, a decision summary, and invalidation. A child decision must cite candidate-specific evidence.
- `suggested_weight_percent` and `sizing_basis: portfolio_context` are valid only when the manifest contains portfolio context explicitly marked `provided_by_user: true`. Otherwise use `risk_units` or `none`.

Stream transient manifest seeds, supplemental inputs, raw collection output, technical-analysis candidates, registration inputs, and discovery audit payloads whenever possible. Never place them inside the run directory. Verification rejects unexpected files and directories under the selected artifact profile. A compact instrument run therefore has five durable files; a compact screening parent has seven plus one five-file child directory per finalist.

## Evidence freeze

Complete collection and calculations before analysis. Freeze evidence.json with its SHA-256 hash. A resumed run must reuse the same manifest and evidence hash.

Never recollect evidence inside an existing run. If state or evidence is corrupt, preserve the run and start a new one with disclosure.

A child finalist inherits shared macro and other candidate-relevant records from the frozen parent bundle, adds its own evidence, and freezes exactly once before any analyst runs. Do not recollect the shared macro snapshot in each child.

Freezing is a hard boundary: no Markdown stage may be committed beforehand. A repeated freeze, candidate registration, finalist registration, or council start with identical input is idempotent and cannot regress a terminal lifecycle.

## Lifecycle

Instrument:

`initialized -> evidence_frozen -> council_running -> decision_ready -> registered decision -> complete|failed`

Screening:

`initialized -> evidence_frozen -> screening_running -> shortlist_frozen -> councils_running -> comparison_ready -> complete|failed`

Use `state_store.py fail` after a role or controller failure remains unresolved after one retry. Failed runs are terminal and never enter decision memory.

After Portfolio Manager, register the decision with `state_store.py decision`. The command requires at least two usable frozen evidence IDs and, for a finalist, candidate-specific evidence inherited from or added to the child bundle. `assemble_report.py` then validates all pre-completion stages and injects the registered decision summary. After assembly succeeds, commit `complete_report.md` as the complete stage and run verification.

## Execution modes

- auto: prefer isolated roles, retry once, then fall back sequentially and disclose.
- multi-agent: require isolation and stop if unavailable.
- sequential-full: execute the entire role sequence in one Codex context.

Execution mode controls how reasoning runs; artifact profile controls what is persisted. They are independent. Chat-only requests create no persistent run regardless of execution mode.

Isolation is a property of reasoning contexts, not headings or files. If one worker drafts several role sections, those stages are sequential-full even when they are stored separately. A theme may parallelize one sequential-full worker per finalist; report parent finalist parallelism and child role execution separately, and never call those child roles isolated.

A chat run may use the operating system temporary directory even when the user did not request durable output. Remove the compact temporary run after returning its verified report. Follow the requested execution mode and its documented fallback; do not downgrade a complete theme request to candidate discovery.

Always report the actual mode.
