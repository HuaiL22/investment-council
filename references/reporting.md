# Reporting and memory

Use consistent headings without forcing analyst prose into JSON.

## Role templates

Analyst:

- Summary
- Evidence and analysis
- Macro environment and technical regime when assigned to Market
- Management claims versus delivery when relevant
- Thesis timeline changes
- Catalysts
- Risks and limitations
- Evidence table when useful

Debate turn:

- Position
- Response to the opposing case
- Strongest supporting evidence
- What could prove this view wrong

Research Manager:

- Rating
- Decision rationale
- Recommended posture
- Invalidation conditions
- Data limitations

Trader:

- Proposed action
- Entry or execution approach
- Risk controls
- Position sizing guidance
- Conditions for no trade

Portfolio Manager:

- Final rating, exposure intent, and explicit confidence level
- Executive summary and thesis
- Value-chain position when relevant
- Management claims versus delivery
- Thesis timeline and invalidation
- Risk assessment and recommendation
- Macro effect on risk budget and technical effect on execution timing
- Supported target and horizon
- Confidence and data limitations
- Scenario method: probability-weighted with probabilities totaling 100% and rationale, or explicitly unweighted stress tests; never treat the base midpoint as expected value by default

## Screening templates

Decision-first opening:

- Lead with the strongest supported causal conclusion: the system change, the economic layers most likely to capture it inside the horizon, and the principal invalidation. Do not begin with audit mechanics or a long universe table.
- For discovery-only or coverage-incomplete work, keep securities unranked. Layer importance may be discussed as system context, but do not turn incomplete company evidence into a security priority list.
- For a valid completed first-round coarse screen, show layer priorities first and then a clearly labeled **provisional research order** or compact tiers for `researching` candidates when valuation, expectations, financing, concentration, delivery, and comparator checks support an order. State that it allocates the next unit of research effort and is neither a recommendation nor a final security-attractiveness ranking. Use explicit no preference when the evidence cannot distinguish candidates.
- Follow the concise decision block with the auditable candidate ledger, disposition reasons, evidence limitations, and search audit. Preserve rigor without making the reader reconstruct the conclusion from the working papers.
- For a completed council, keep the macro regime, technical regime, and their effect on the final exposure intent visible near the decision. Do not bury them in an analyst appendix or imply that they independently determined the fundamental rating.

Scope:

- market, theme or comparison set, cutoff, horizon
- request mode and actual execution mode, including whether candidate-pool construction, first-round coarse screening, finalist councils, persistence, and deterministic validation actually ran
- benchmark, instrument types, and liquidity-rule provenance: quote the user-supplied rule or report `not_applicable`; never imply a model-created threshold
- exclusions and data limitations
- discovery coverage gate, remaining material gaps, and whether first-round coarse screening was permitted to start
- analysis cutoff plus any non-terminal listing or corporate-action event followed forward to its latest cutoff-valid state
- requested-market route disposition for material foreign or changed entities: primary, secondary/cross-listing, ADR/ADS or equivalent depositary claim, corporate-action successor, and conditional ETF/fund fallback; distinguish direct issuer securities from indirect fund exposure

System map:

- system change
- value-chain layers
- layer research priority and horizon fit
- constraint direction, earnings-transmission lag, expectations, and downside
- evidence and missing checks
- a visible layer-priority decision covering every represented layer and naming the candidates carried into company screening

Candidate ledger, for every candidate:

- identity and chain position
- entry reason, state, and transition reason
- layer priority, horizon fit, transmission, and materiality
- evidence and strength, including latest results
- management claims versus delivery
- expectations gap, valuation or scenario asymmetry, and catalyst clock
- valuation method, cutoff date, result or labeled proxy; never merely "defer valuation to the next round"
- liquidity and exitability
- missing proof
- risks, invalidation, comparator-eligibility result, nearest alternative or explicitly labeled opportunity-cost comparison, relative preference, and re-entry condition
- investment, trading, both, or neither when supported

Shortlist:

- layer priorities reported separately from company dispositions
- exact-set and count reconciliation across discovery inventory, displayed map, candidate ledger, all disposition states, and finalists
- registered discovery-baseline hash and confirmation that first-round coarse screening preserved all candidate IDs and atomic-path memberships
- deterministic baseline-validation result; if baseline registration or reconciliation was not executed successfully, the report must say first-round coarse screening was not completed
- every baseline candidate visible in the candidate map and ledger, or explicitly named in one overflow appendix; presentation compression cannot remove a candidate
- provisional research order or tiers for continuing candidates only when the comparative evidence supports it, otherwise explicit no preference
- continuing or advanced candidates, gate results, light expectations and valuation evidence, and one explicit head-to-head conclusion against the nearest eligible alternative
- pending candidates, exact decision-critical missing proof, source, and next check
- whether the conclusion covers the full universe or only a verified subset; for a resolved-subset run, name every unresolved research lead or pending candidate that could alter the result and state that any preference is conditional rather than exhaustive
- eliminated candidates, decisive reasons, nearest superior alternatives, and re-entry conditions
- no generic company watch, observe, defer, or temporary parking bucket
- whole-class exclusions and the differentiated demand-side or downstream transmission test used before exclusion
- Screening Reviewer challenges and resolutions
- finalist registration summary

Each candidate needs an individual decisive transition reason and re-entry condition. Companies may be grouped for compact presentation only when those company-specific records remain visible; one shared generic reason cannot stand in for multiple materially different businesses, stages, or risk profiles. A name that appears in a disposition but not the candidate map, or vice versa, is a blocking report error rather than a cosmetic omission.

Search audit:

- report universe discovery, security-route discovery, corporate actions, business verification, and market audit as separate jobs;
- for each job state source classes or sites, query or traversal lens, call count, failures or empty results, fallback used, and unresolved high-impact items;
- do not use a list of issuer pages as evidence that global supplier discovery or route-family checking occurred;
- disclose the actual execution mode and any step that was skipped, simulated, or incomplete.

Comparison:

- preferred candidate or explicit no preference
- every completed council ranked without a quota
- rating, exposure intent, and trading or investment suitability
- scarce-layer position and management delivery
- strongest evidence and dissent
- liquidity, action conditions, and invalidation
- failed or incomplete councils excluded from ranking

For every completed council, keep the final rating, exposure intent, and confidence adjacent in the decision block. Explain any apparent mismatch, such as an Overweight research rating paired with `hold` or `avoid` because post-event price discovery, macro risk, portfolio context, or technical execution evidence is incomplete.

Write fluent prose under these headings. Omit genuinely inapplicable sections but never hide missing data.

## Output profiles

Chat is the default user experience. Use a system temporary directory when the complete council requires freezing and verification, return the verified natural-language report, and remove that temporary directory afterward. Create no durable run directory unless the user asks to save, resume, or audit the run.

Persistent runs default to `artifact_profile: compact`:

- `manifest.json`: immutable run identity and configuration
- `state.json`: lifecycle, hashes, and stage registry
- `evidence.json`: the single frozen evidence bundle
- `stages.json`: natural-language stage outputs stored once for resume and verification
- `complete_report.md`: the only user-facing report
- screening parents additionally retain `candidates.json` and `finalists.json`
- each finalist child uses the same five-file compact instrument layout

Do not save manifest seeds, raw evidence, calculated evidence candidates, registration inputs, discovery audits, or temporary role Markdown inside the run directory. Produce them in the system temporary directory and remove them after the corresponding deterministic command succeeds.

Use `artifact_profile: audit` only when the user explicitly requests inspectable role-by-role artifacts or when diagnosing the skill. Audit mode replaces `stages.json` with `artifacts/STAGE.md`. It does not also render a second `1_analysts/`, `2_research/`, `3_trading/`, `4_risk/`, or `5_portfolio/` tree. `assemble_report.py --render-stage-files` is an explicit debugging export, never a default step.

Do not duplicate the final report as a `complete` stage artifact. Register the existing `complete_report.md` in place.

## Storage

Default runs: `./investment-council-runs/SAFE_TICKER/DATE-TIMESTAMP/`.

Default memory: `~/.investment-council/memory/decisions.json`.

Allow overrides, sanitize ticker-derived paths, and write state atomically.

## Decision memory

Only after a complete verified Portfolio Manager run, pass the allowed rating, exposure intent, and short thesis to `memory_log.py`. Reports remain natural language; command arguments support outcome tracking.

Failed and partial councils never enter memory. Child workers do not write shared memory concurrently; the screening controller appends completed decisions serially.

Align the instrument and benchmark on common completed sessions. Enter at adjusted-close index 0 and evaluate the full horizon at index 5. With only 2–5 common closes, record a partial outcome and update it later.

Store asset return, benchmark return, raw alpha, direction-adjusted decision return, and decision alpha. These are counterfactual decision-quality metrics, not realized P&L.

Resolve one run ID at a time with a Codex-authored reflection. Inject at most five recent resolved same-ticker lessons and three cross-ticker lessons; never inject pending outcomes.

On later runs, compare the prior thesis and management claims with new evidence. State what changed and whether each claim was delivered, partly delivered, contradicted, not yet testable, or superseded.
