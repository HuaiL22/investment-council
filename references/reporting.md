# Reporting and memory

Write fluent natural-language Markdown. Use headings and tables only when they improve decision clarity. Do not expose internal schemas, phase codes, or working-file mechanics unless a failure is material to the conclusion.

## Decision-first structure

Lead with the strongest supported result:

- for an instrument, place final rating, exposure intent, confidence, and current action together;
- for a coarse screen, state the layer conclusion and provisional research order;
- for a completed theme, state the conditional or full-universe ranking and whether any candidate qualifies;
- for discovery-only or incomplete company evidence, keep securities unranked.

Follow the decision with causal evidence, strongest dissent, valuation and downside, macro and technical effects on execution, invalidation, scope, and limitations. Do not make the reader reconstruct the conclusion from an audit log.

Distinguish:

- **layer priority**: where the economic transmission appears attractive;
- **provisional research order**: where the next unit of research effort should go;
- **final security ranking**: the result of completed verified councils.

A provisional order is not a recommendation. A resolved-subset preference is not an exhaustive winner.

## Instrument report

Include:

- identity, cutoff, horizon, benchmark, and relevant portfolio assumptions
- final rating, exposure intent, and explicit confidence
- current action in plain language
- thesis and value-chain position
- observed facts versus management claims and subsequent delivery
- valuation or scenario method and prospective asymmetry
- macro regime and its effect on the risk budget
- technical regime and its effect on timing
- strongest Bull case, strongest Bear case, and decisive synthesis
- financing, concentration, liquidity, and exit risks
- catalyst timeline and invalidation conditions
- supported execution framework, or a clear statement that exact levels are unavailable
- evidence and source limitations

Explain apparent mismatches, such as an Overweight research rating paired with hold or avoid because valuation, macro risk, portfolio context, or price discovery makes immediate action unattractive.

Without user portfolio data, use hypothetical risk units or conditional tranches. Do not output percentage portfolio weights or invent current position size, cost basis, concentration limits, or executable order quantities.

Numeric scenarios must be either:

- probability-weighted, with probabilities totaling 100%, rationale, and calculation; or
- explicitly unweighted stress tests.

Do not present a base midpoint as expected value or a target by default.

## Theme report

Use this order:

1. decision-first conclusion
2. scope and completion frontier
3. system map and layer priorities
4. candidate pool and coverage status
5. coarse-screen dispositions
6. finalist council comparison when completed
7. unresolved leads, limitations, and search audit

### Candidate pool

Show every formal candidate in the map or a clearly named overflow section. Presentation compression may group rows but cannot delete candidates.

State:

- market, cutoff, horizon, benchmark, instrument types, and liquidity-rule provenance
- coverage status and whether screening uses the full universe or a resolved subset
- material foreign, changed, indirect, private, and unresolved routes
- important corporate-action and current-ticker corrections
- the deterministic baseline and exact-set reconciliation result

### Candidate dispositions

For every formal candidate preserve a compact record of:

- path and state
- decisive transition reason
- current expectations and valuation method or labeled proxy
- nearest comparable alternative or labeled opportunity-cost comparison
- principal risk or missing proof
- for eliminated or pending candidates, a concrete re-entry condition

Use only registered candidate states. Layer-level watch labels do not create a company watch bucket. Group company rows only when each name's distinct reason and any applicable re-entry condition remain visible.

For pending verification, name the exact decision-critical fact, expected source or event, and why it could change the finalist set. For unresolved research leads, state which path or ranking they could change.

Counts and identities must reconcile across the baseline, candidate map, ledger, dispositions, and finalists. A missing or duplicated name is a blocking report error.

The report assembler adds the registered disposition row for every formal candidate and lists every unresolved research lead. Do not substitute a short “nearest alternatives” list for these complete registries.

### Finalist comparison

For every completed council show:

- rank or explicit no preference
- final rating, exposure intent, and confidence
- economic path and transmission
- management delivery
- valuation and downside asymmetry
- strongest evidence and strongest dissent
- macro and technical effect on action
- liquidity and exit conditions
- thesis invalidation

Exclude failed or partial councils from ranking and name them. Do not force a preferred candidate. The assembler derives rating, action, exposure intent, confidence, macro effect, and technical effect from each child's registered final decision; prose may explain these fields but may not replace or contradict them.

## Role outputs

Role artifacts should be compact and decision-relevant:

- Analysts: conclusion, evidence, implications, catalysts, risks, and limitations.
- Bull/Bear: position, direct response to the opposing case, strongest evidence, and falsifier.
- Research Manager: rating, decisive rationale, posture, limitations, and invalidation.
- Trader: action, execution conditions, risk controls, horizon, liquidity, and no-trade conditions.
- Risk roles: adjustment to size, timing, stop logic, horizon, or direction.
- Portfolio Manager: final rating, exposure intent, confidence, synthesis, execution, and invalidation.

Attach evidence IDs to material facts and exact numbers, not every opinion.

## Search and execution audit

Keep the audit concise but separable by job:

- universe discovery
- security-route discovery
- corporate actions
- company exposure and current results
- market, macro, and technical collection
- finalist research and councils

For each material job disclose source classes, meaningful failures or empty results, fallback, and unresolved high-impact items. Report the requested and actual execution modes, skipped work, coverage scope, and whether recommendations are hypothetical.

Search call counts are useful diagnostics but are not evidence of completeness.

## Output profiles

Chat is the default user experience. Use a system temporary directory for freeze and verification, return the verified report, and remove the run afterward. Create durable output only when the user asks to save, resume, or audit.

Persistent runs default to artifact_profile: compact:

- manifest.json: immutable configuration
- state.json: lifecycle, hashes, baseline, and stage registry
- evidence.json: frozen evidence
- stages.json: each natural-language stage stored once
- complete_report.md: the only user-facing report
- screening parents also retain candidates.json and finalists.json
- each finalist child uses the same five-file instrument layout

Transient inputs, raw collection output, audit payloads, and temporary role Markdown stay outside the run directory and are removed after use.

Use artifact_profile: audit only when the user requests inspectable role files or when diagnosing the skill. Audit mode replaces stages.json with artifacts/STAGE.md; it does not create a duplicate hierarchy. Do not duplicate the final report as another stage artifact.

## Decision memory

Only a complete verified Portfolio Manager decision may enter memory through memory_log.py. Failed and partial runs never enter it. Child workers do not write shared memory concurrently; the parent appends completed decisions serially.

Outcome tracking aligns the instrument and benchmark on common completed sessions and stores asset return, benchmark return, raw alpha, direction-adjusted decision return, and decision alpha. These are counterfactual decision-quality metrics, not realized profit and loss.

On later runs, compare the prior thesis and management claims with new evidence. State what changed and classify each material claim as delivered, partly delivered, contradicted, not yet testable, or superseded.
