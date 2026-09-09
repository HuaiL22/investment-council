# Screening workflow

Read this reference for theme discovery, candidate-pool construction, first-round coarse screening, or multi-company comparison.

The workflow separates three questions:

1. Which economic paths and issuers belong in the research universe?
2. Which verified securities deserve the next unit of research effort at the current price and horizon?
3. After complete councils, which security—if any—has the best evidence-adjusted prospective asymmetry?

Do not answer a later question with evidence gathered only for an earlier one.

## Scope and completion frontier

Record the requested outcome, market boundary, cutoff, horizon, benchmark, instrument types, liquidity rule, exclusions, and execution mode before searching.

For a broad theme, define a finite **completion frontier** in economic terms. Include material system-level enablers, general-purpose platforms, and independently purchased commercialization paths that can affect security economics within the horizon. Treat downstream adopters and representative vertical applications as context unless the user requests them or they create an independent, material purchasing market.

The frontier is a closure rule, not a familiar-company list. It must explain why another adjacent company would not add a new economic path. Once locked, do not expand or contract it to obtain a convenient candidate count.

A complete theme request continues through screening, finalist research, councils, and comparison. A discovery-only request stops after the audited map. A coarse-screen-only request stops after comparative dispositions and exact-set reconciliation.

## Candidate-pool construction

### Build atomic economic paths

Start with the system change and trace how it affects buyer needs, purchased products or services, suppliers, substitutes, capacity, pricing, and company economics.

Each atomic path should represent one buyer need and one meaningful purchasing choice. A path may contain different technologies or business models when buyers treat them as substitutes for that need. Split a path when the buyer, budget, contract, product, or non-substitutability changes the economic market.

Implementation differences, supplier sets, capacity, revenue models, and transmission speed are prompts to test atomicity; they do not automatically create separate paths. When a compound path is split, conserve every material parent member in one or more child paths and audit the parent-to-child mapping.

For every material path, record:

- buyer need and economic function
- principal suppliers and substitutes
- demand or constraint transmission
- expected lag to revenue, margin, cash flow, or asset value
- material risks and invalidation
- relation to sibling or adjacent paths

### Discover entities globally

Do not begin with the requested exchange list. Reconstruct the economic supplier set first, then map market access.

Use both discovery directions:

- **Function to supplier**: who provides the product, capacity, asset, or platform?
- **Supplier to alternatives**: whom do buyers, competitors, filings, technical records, projects, or industry sources identify as alternatives?

Classify surfaced entities as path members, sibling-path members, or adjacent context. Preserve cutoff-valid new entrants and corporate actions. Use industry, customer, project, technical, exchange-new-listing, and current-news sources for recall; issuer investor relations alone cannot demonstrate supplier-set completeness.

Bound discovery with explicit per-run search limits and a maximum path queue recorded in scope. If the limit is reached while a material frontier remains unresolved, retain the map, mark coverage incomplete, and continue on the verified subset when possible. An empty broad search or failed preferred adapter never proves that an entity or route does not exist.

### Resolve securities and access

After entity discovery, map each entity to cutoff-valid tradable routes inside the requested market:

1. eligible primary listing
2. eligible secondary or cross-listing
3. eligible ADR, ADS, GDR, depositary receipt, or equivalent direct issuer claim
4. current listing, spin-off, rename, merger, successor, and ticker chain
5. only when direct access is absent and funds are permitted, a bounded ETF or fund fallback

Depositary receipts are direct issuer securities. Funds are indirect exposure and enter the formal candidate pool only when the requested scope permits them.

Never infer access from domicile, headquarters, incorporation, reporting currency, or primary-listing country. Finding an outside-boundary primary listing is a route-search trigger, not a negative conclusion.

Negative or unresolved route conclusions require targeted cutoff-valid checks of every applicable route family using issuer, exchange, regulator, or depositary sources. A failed or ambiguous lookup remains unresolved; it is not evidence of absence. One current authoritative source can establish a positive route when no independent second source is available. For route-changing corporate actions, seek two independent authoritative source classes when practical.

Treat proposed, filed, registered, pending, or not-yet-effective events as non-terminal. Search forward through the cutoff for effectiveness, pricing, trading commencement, closing, withdrawal, or termination. The latest cutoff-valid terminal event determines the route and owner. Display a current ticker only when supported; otherwise use an unresolved identifier and label legacy tickers as historical.

When a verified corporate action changes the route, replace the legacy security in the ledger and rerun identity and market checks on the current one.

### Drain high-impact and sparse-path checks

Maintain a compact high-impact access queue containing:

- principal global suppliers or substitutes
- recent or cutoff-relevant listings and corporate actions
- entities whose access result could change a material path's coverage
- unresolved routes that could alter the formal candidate or core coverage

Process these before lower-impact adjacency. A broad search or shared batch error does not clear an item; record the exact targeted fallback and result.

Use provisional and final eligible route counts as recall triggers:

- **0**: rebuild the path and access search
- **1**: challenge apparent monopoly and missing foreign or new routes
- **2**: run a lighter alternatives check
- **3+**: no count-driven repair is required

This is not a quota. Never manufacture a third candidate.

### Classify entities without screening them early

Every material entity with a verified eligible direct route enters the formal candidate pool before screening. Company fame, size, evidence convenience, expected later elimination, or a stronger same-path alternative cannot demote it to context.

Reserve context for:

- securities outside the requested boundary
- indirect-only routes when indirect exposure is excluded
- private or unavailable routes
- entities outside the locked completion frontier

Use a named research-lead state for material unresolved entities that could enter the pool. Keep route reason, attempted checks, missing proof, and affected path visible.

Every formal candidate needs a dated candidate-specific economic-transmission anchor. Record the status of its latest-results check; a full valuation and decision dossier belongs to coarse screening, not pool-completion gating.

Core and extended groupings may compress presentation but do not change membership. If used, derive core as the smallest subset that preserves every distinct exposure and transmission mechanism under an iterative remove-one test. Alternatives remain extended.

### Run an independent omission review

After the first map, review it from a fresh perspective. Challenge:

- compound or overlapping paths
- paths with zero, one, or two eligible routes
- customer-to-supplier and supplier-to-customer inversions
- newly listed or recently changed securities
- foreign entities incorrectly excluded by country inference
- small suppliers, ODM/EMS providers, connectors, storage, integrators, and demand-side platforms
- overreliance on famous issuers or English-language evidence
- whole-class exclusions based on presumed thematic purity

Add valid omissions to the same inventory. Do not create an informal side list that escapes later reconciliation.

### Audit identity and market observations

Feed the complete mapped inventory to the bundled audit:

~~~bash
python scripts/audit_universe.py --input - --output -
~~~

The audit validates requested and canonical symbols, issuer identity, exchange, route type, cutoff validity, corporate-action warnings, market-history availability, and optional liquidity observations. It does not decide investment merit.

Merge scripted and manual results per route and per field:

- preserve successful observations when another route or source fails
- allow authoritative manual evidence to replace an unavailable field
- never erase a genuine conflict
- never propagate a shared endpoint failure to every route
- treat short or unavailable price history as a market-data status, not a company disposition

Reconcile the union of system-map entities, omission additions, route changes, split-path members, and formal candidates. Every material entity must end as a candidate, research lead, or explicit context/exclusion. Unexplained disappearance blocks a completeness claim.

## Coverage decision

Use **complete coverage** (`coverage_status: coverage_complete`, `screening_scope: full_universe`) when all material paths inside the locked frontier have substantive reasoning, high-impact route checks are drained, formal candidates are identified, and the conservation audit passes.

Use **incomplete coverage with a resolved subset** (`coverage_status: coverage_incomplete`, `screening_scope: resolved_subset`) when bounded unresolved research leads remain but a coherent verified candidate set can be screened. Register both the unresolved leads and the verified baseline. Continue the requested workflow on that subset and label all later preferences conditional.

Do not claim complete coverage merely because the table looks balanced or every row has a ticker. Do not stop a complete request solely because one source, batch endpoint, candidate, or long-tail route failed.

## First-round coarse screening

### Register the baseline

Initialize the screening run and register the immutable discovery baseline before screening evidence is frozen:

~~~bash
python scripts/state_store.py init --manifest - --run-dir SCREENING_RUN
python scripts/state_store.py baseline --run-dir SCREENING_RUN --input -
~~~

The baseline records every verified candidate ID and atomic-path membership plus unresolved research leads and coverage scope. Later candidate registration must reconcile exactly with it. If deterministic registration or reconciliation fails, do not report the coarse screen as completed.

### Prioritize economic layers

Before deciding company states, compare the represented layers on:

- system change and buyer urgency
- transmission to revenue, margin, cash flow, or asset value
- capacity, substitution, and pricing power
- horizon fit and catalyst timing
- expectations already reflected
- downside and failure modes

Publish a visible layer view such as priority, watch, or deprioritized. These labels belong to layers only; they are not company states. Scarcity and bottleneck control may create durable economics but are not mandatory advancement gates. Test differentiated demand-side, diversified, integrator, and downstream transmission before excluding an entire class.

### Compare companies within and across paths

Collect evidence progressively as specified in [evidence](evidence.md): a baseline pass for every candidate, a contender pass for plausible continuers, and a decision pack for potential finalists.

For every company that may continue, establish:

- **Transmission and materiality**: why the system change can affect this issuer inside the horizon
- **Delivery**: whether orders, capacity, products, margins, working capital, cash flow, or customer evidence support management's claims
- **Expectations gap**: what the current price and public expectations appear to assume
- **Valuation and asymmetry**: an appropriate multiple, normalized cash-flow view, asset method, or scenario range
- **Catalyst clock**: a plausible thesis-resolution event inside the horizon
- **Downside**: financing, dilution, concentration, substitution, governance, legal, regulatory, geopolitical, and execution risks
- **Relative opportunity**: one explicit comparison with the nearest eligible alternative

A comparator is genuinely nearest only when economic transmission, maturity, financing profile, catalyst horizon, and security rights are sufficiently similar. Otherwise label it a cross-layer or opportunity-cost comparison.

Use valuation methods suited to the security and business model. Normalize currency, depositary ratios, and economic rights. Do not capitalize peak cyclical earnings, use ordinary P/E for REITs, or value pre-revenue and capital-intensive businesses as mature software. A single aggregator multiple, target price, or recent return cannot decide disposition.

Observe liquidity and exitability. Apply pass/fail only when the user supplied a numerical rule. With no rule, record it as not applicable and do not use liquidity to advance or eliminate a candidate.

Price trend, macro, and technical evidence may inform context and later execution; they do not replace the company-level opportunity case.

### Assign one candidate state

Use the state model enforced by `state_store.py`:

- `researching`: deserves more work but has not passed complete finalist gates
- `pending_verification`: one or a few named, obtainable, decision-critical facts could change the decision
- `eliminated`: does not receive more resources in this run
- `advanced`: has passed finalist registration requirements and will receive a complete council

Do not create company-level watch, observe, defer, or similar parking states.

Pending is exceptional. Name the exact fact, expected source or event, why it matters, and when it can be checked. Short trading history, a recent official listing, preliminary results, an upcoming filing, or an unavailable quote does not by itself create pending. Use existing registration, exchange, current-report, issuer, and depositary evidence first.

Run one consolidated gap-closure pass for material pending candidates. Then advance, eliminate, or retain pending only if the still-missing fact could plausibly alter the finalist set. A large pending population indicates inadequate baseline work and lowers confidence.

Every candidate receives an individual decisive transition reason and next-required evidence. Eliminated and pending candidates also receive a concrete re-entry condition. Missing evidence is not a negative business fact. Elimination is appropriate for a supported conclusion such as immaterial or too-slow transmission, unattractive downside-adjusted valuation, catalyst outside the horizon, weak economics or quality, or clear inferiority to alternatives.

### Review and reconcile

The screening reviewer challenges material continuations and eliminations for:

- evidence-availability and famous-name bias
- strong operations without a prospective expectations gap
- mistaken equivalence between obscurity and weak economics
- weak or incomparable valuation methods
- hidden financing, concentration, or correlation risk
- untested whole-class exclusions
- pending or eliminated candidates that could replace a finalist

Resolve material challenges before registration.

Before rendering, reconcile exact entity sets and counts across the baseline, displayed map, candidate ledger, dispositions, and finalists. Every baseline candidate appears once; unresolved leads remain outside the candidate and finalist sets but stay visible.

Register candidates and finalists, then begin councils:

~~~bash
python scripts/state_store.py candidates --run-dir SCREENING_RUN --input -
python scripts/state_store.py finalists --run-dir SCREENING_RUN --input -
python scripts/state_store.py start-councils --run-dir SCREENING_RUN
~~~

For a coarse-screen-only request, continuing names remain `researching`. Do not label them final picks.

## Complete finalist councils

For every registered finalist:

1. Create an independent child instrument run linked to the parent run and evidence hash. One isolated worker owns one finalist.
2. Inherit shared macro and candidate-relevant frozen records.
3. Add current candidate-specific market and public evidence.
4. Calculate technical evidence and freeze the child once.
5. Run every analyst, debate, research, trading, risk, and portfolio role from the child's frozen evidence rather than a conversation-only summary.
6. Register the final decision, then assemble and verify the report.

Do not refetch inherited shared macro data in every child. A failed or partial child is disclosed and excluded from ranking.

Bind the child to the exact parent run, finalist candidate ID, canonical security, market, and relevant subject IDs. The parent accepts only terminal children whose manifests, state hashes, evidence, stage order, and committed artifacts verify.

## Final comparison

Compare completed Portfolio Manager decisions; do not average role opinions or manufacture unanimity.

For each surviving company explain:

- economic path and transmission
- final rating, exposure intent, and confidence
- suitability for trading, investing, both, or neither
- management claim versus delivered evidence
- strongest support and strongest dissent
- valuation and downside asymmetry
- macro and technical effect on execution
- liquidity and exit conditions
- thesis invalidation

Rank without a fixed quota only when evidence supports an order. If none qualifies, say so and identify what could change the result.

For a resolved-subset run, rank only completed verified finalists. Lead with the scope limitation, name unresolved leads and pending candidates capable of changing the order, and label any preference conditional on the verified universe.

Every full conclusion includes a thesis timeline: when the thesis became plausible, what strengthened or weakened it, what management said, what was subsequently delivered, and what future fact would invalidate it.

## Search and execution audit

Report these research jobs separately:

- universe discovery
- security-route discovery
- corporate actions
- company exposure and current-results verification
- market and liquidity observations
- macro and technical collection
- finalist evidence and councils

For each material job state the source classes, search or traversal approach, meaningful failures, fallback, and unresolved high-impact items. Disclose the actual execution mode and anything skipped or incomplete. Search volume is an audit aid, not proof of completeness.
