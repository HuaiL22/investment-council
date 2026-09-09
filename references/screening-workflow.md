# Candidate discovery and progressive screening

Read this reference for theme discovery, recommendation requests, and multi-company comparisons. Screening narrows a broad universe; it never replaces the complete council for a finalist.

## Request modes

- Instrument: analyze one stock, ETF, index, or crypto instrument with the complete council.
- Theme: discover a coverage-oriented universe, screen it, then run a complete council for every finalist.
- Comparison: keep the companies supplied by the user as a closed universe, apply the same gates, then run complete councils. Expand the set only when the user explicitly requests peers or alternatives.

A short theme query routes to the complete Theme workflow. Discovery-only, candidate-pool-only, system-map-only, or coarse-screen-only behavior must be explicitly requested. “Complete research,” “完整研究,” “final conclusion,” and equivalent language require a terminal attempt through candidate-pool construction, first-round coarse screening, finalist deep research, comprehensive council review, and the final research conclusion. Do not reinterpret a complete request as discovery-only after work begins.

Do not impose a finalist quota. Let the gates produce zero, one, or many finalists.

## Candidate-pool construction

Candidate discovery is recall-oriented and independent from prioritization. It maps the economic system and builds a complete-enough tradable universe without ranking, eliminating, recommending, or running council roles.

### Set scope

Record market, theme, cutoff, 3–12 month default horizon, benchmark, eligible instrument types, liquidity requirement, and user constraints.

State and lock how the theme closes before expanding it. For a broad cross-industry theme, cover enabling infrastructure, general-purpose platforms, and other direct system-wide transmission paths comprehensively. Treat downstream vertical applications as representative unless the user explicitly asks for exhaustive vertical coverage, narrows the theme to a vertical, or that vertical can change system-wide economics within the horizon. Do not turn “all chains” into every eventual adopter of the technology. Once locked, new adjacent adopters, feature users, micro-cap claimants, or representative verticals do not expand the completion frontier merely because they use the theme; record them as adjacent context or lower-impact leads with a reason. Reopen the frontier only when cutoff-valid evidence shows a distinct material buyer need or system-wide transmission path that could change the eligible universe or finalist set.

Use a materiality triage before detailed route work. A gap is high-impact only when resolving it could add or remove a material atomic path, change a provisional or final `0`/`1`/`2` access bucket, add a plausible core candidate, or change the finalist set. Everything else is lower-impact. Finish high-impact checks first. Lower-impact unresolved entities may retain an exact disposition, source failure, and next check without blocking `coverage_complete`; do not perform unbounded long-tail verification merely to turn every adjacent node into a terminal negative conclusion.

A closed comparison bypasses candidate-pool construction. If the user explicitly requests expansion, derive and state a defensible comparison axis from the user's goal, then treat it as a theme. If no defensible axis exists, keep the supplied set closed, return the expansion attempt as `coverage_incomplete`, identify the missing axis as the blocking gap, and stop discovery.

### Map the system

Translate the market story into:

`demand change -> system pressure -> required change -> value-chain layers -> hard-to-expand layer`

Generate the material layers from the theme's actual economic and technical structure. Do not start from a fixed industry taxonomy. Use demand, commercialization, supply, production, enabling inputs, infrastructure, standards, and regulation only as traversal lenses when they are relevant.

Understand layers before companies. Look for low supplier count, long qualification, hard expansion, specialized know-how, scarce inputs, capacity reservations, price acceptance, regulatory constraints, or infrastructure limits without ranking companies during discovery.

### Stage 1: build the preliminary inventory

1. **System expansion**: identify the underlying change, resulting pressure, required products, services, processes, or infrastructure, and possible transmission into revenue, pricing, margins, cash flow, or return on equity.
2. **Relationship expansion**: traverse material customers, suppliers, competitors, substitutes, partners, enabling inputs, standards, certification, regulation, and infrastructure around every material layer. Include listed and unlisted entities in the relationship map.
3. **Current-change scan**: inspect the latest relevant filings, results, calls, announcements, orders, tenders, certifications, capacity projects, permits, patents, standards, product changes, cross-company disclosures, listings, spin-offs, depositary receipts, and identifier changes available at or before the cutoff. Record a date or explicit unavailable status for current-change, listing, and liquidity conclusions. Candidate-pool construction requires a dated candidate-specific economic-transmission anchor and records the status of the latest-results check; first-round coarse screening completes the latest results or filing, current financial context, expectations, valuation, and comparator work for every company that could continue. One document need not serve all purposes.
4. **Path-purity and global-set pass**: split the updated layers into atomic material paths, classify surfaced entities as path members, sibling-path entities, or adjacent context, and reconstruct every path's cutoff-valid global supplier and substitute set in both directions below.
5. **Security mapping**: only after steps 1–4, map economic beneficiaries to direct and, conditionally, indirect tradable routes. Verify issuer, unique security identity, venue, type, business exposure, and observed liquidity rather than relying on memory. Reconcile the mapped inventory again after relationship expansion to catch new listings, depositary receipts, spin-offs, ticker changes, name changes, and category conflicts.

Before per-path ledgers exist, bound the preliminary system map to at most 12 query or traversal lenses, two substantive sources per lens, and two relationship hops from the theme's demand change across system expansion, relationship expansion, and the preliminary current-change scan. Record additions, unresolved frontiers, and the stop reason. Candidate-specific verification and targeted security-route fallbacks use their later budgets. If a high-impact material frontier remains when this budget ends, retain the current map and set `coverage_incomplete`. A discovery-only request returns that status; a terminal-outcome request later registers the unresolved frontier as research leads and continues on the verified subset. An exhausted lower-impact frontier outside the locked closure rule is recorded but does not block the complete workflow.

### Route sources by research job

Do not use one source type for the whole discovery process:

- **Universe discovery**: use current market-structure sources such as industry, customer, regulator, standards, exchange-new-listing, and financial-news sources to surface global entities, substitutes, new entrants, and corporate actions. An issuer page can add or verify that issuer but cannot prove the supplier set is complete.
- **Security-route discovery**: use official issuer, exchange, regulator, and depositary-program sources to map primary shares, cross-listings, depositary receipts, and new securities.
- **Corporate-action reconciliation**: use current issuer, exchange, and filing evidence to resolve spin-offs, separations, successors, renames, ticker changes, and current business ownership.
- **Business verification**: confirm the latest filing or results and the strongest dated evidence of economic exposure; use material customer or counterparty evidence when available.
- **Market audit**: use market-data sources only for identity conflicts, liquidity observations, and research context. Market data does not discover the global supplier set or prove business exposure.

Choose current sources appropriate to the subject instead of treating examples as a permanent whitelist. Preferred public examples include Nasdaq and NYSE listing or new-listing pages, SEC EDGAR or the relevant regulator, issuer IR, and the J.P. Morgan, Citi, and BNY Mellon depositary-receipt directories. Reuters, Bloomberg, and credible industry or market-share sources may surface current leads but are not final identity or exposure proof. These examples are replaceable fallbacks, not exclusive authorities. For each source job, record the source role, query or traversal lens, result, and fallback. An empty general, news, or AI search means only that the search route returned no usable result; it cannot prove absence.

### Prove path purity and reconstruct the global set

A path is atomic only when its products or services address the same buyer need and compete within the same purchasing choice or procurement category. Apply a counterfactual procurement test before counting: could the buyer reasonably choose one member instead of another to satisfy that need within an economically comparable budget range? Record the conclusion briefly. Split separate buyer needs, purchasing markets, or non-substitutable products into sibling paths. Enqueue every material child path for the complete path process and assign every parent-path membership to one or more child paths or explicit adjacent context. Conservation requires every parent membership to remain in the union of those dispositions; a child path may also add newly discovered entities. Splitting cannot delete a material child path or member. Technical implementation, switching cost, qualification, capacity constraints, supplier revenue models, and company-specific transmission are differentiators but do not alone determine membership. Adjacent paths cannot satisfy one another's counts.

Apply the same test to the proposed report labels immediately before rendering. If a row or its procurement-boundary explanation says that members satisfy different buyer needs, draw from different purchasing budgets, or cannot reasonably substitute for one another, the row contradicts its own atomicity claim: split it and rerun the affected child paths. A broad heading may group sibling paths for readability only when each child path and its membership remain explicit.

For each atomic material path, run both discovery directions before applying the user's market boundary:

1. **Function to supplier**: start from the required product, service, technical function, or capacity and identify the entities that ship, qualify, operate, or provide it by the cutoff.
2. **Supplier to alternatives**: start from the surfaced entities and identify their competitors, same-function substitutes, alternate technical implementations, integrated or horizontal suppliers, and material new entrants by the cutoff.

An issuer source can prove that issuer's exposure but cannot prove the supplier set is complete. Challenge the set with cutoff-valid cross-company, customer, regulator, standards, credible industry, or other market-structure evidence. For a historical cutoff, reconstruct the set as it existed then. Preserve entities whose omission could materially change supplier concentration, constrained capacity, or a principal technical substitute; security eligibility alone does not make a minor supplier material.

Classify each surfaced entity before counting it:

- **Path member**: supplies or operates a plausible alternative for the same buyer need and purchasing choice, even when implementation, switching cost, capacity constraint, or supplier revenue model differs.
- **Sibling-path entity**: serves a separate buyer need or procurement market, or buyers do not treat it as an alternative within the same choice; create or attach it to another atomic path and run the complete path process there.
- **Adjacent context**: affects the path but does not supply the required function and cannot enter its eligible count.

Technical implementation, supplier set, capacity constraint, revenue model, vertical integration, or horizontal supply differences trigger comparison but do not alone decide membership or force a split; apply the buyer-need and purchasing-choice test.

Use a separate finite pass ledger for each path: one Stage 1 broad pass in each direction, one Stage 2 focused omission or update pass, and one post-audit delta-repair pass limited to audited conflicts, bucket changes, and targeted route resolution. A broad direction uses at most four query or traversal lenses, at most two substantive sources per lens, and one relationship hop from its current frontier. The focused pass uses at most two gap-specific lenses and two substantive sources per lens. A delta repair touches only affected entities or routes and cannot start another broad expansion. Queue a surfaced sibling path for its own ledger rather than recursively expanding it in the current pass. Across one run, process at most 40 material atomic paths and at most two sibling-path generations from the initial system map. Reaching a cap with no remaining queue may still complete; if a material queued path would exceed either cap, record the queue and set `coverage_incomplete`. Record lenses, sources, anchors, additions, dispositions, unresolved gaps, exhausted budget, and stop reason. Any material unresolved addition at exhaustion forces `coverage_incomplete`, but a terminal-outcome request continues through the resolved-subset workflow rather than restarting or stopping the entire run.

Only after this proof may discovery map securities or count eligible candidates. Any later material addition, removal, or membership change invalidates the affected path's reconstruction, security map, count, and sparse result until both direction records and dispositions are updated within the same bound.

### Map economic entities before securities

Maintain two separate inventories:

- an economic-entity inventory containing material public, private, domestic, and foreign companies or other relationship nodes before applying the user's market boundary;
- a security-access map containing unique tradable instruments and their direct issuer link or indirect exposure links.

Give each economic entity a stable `entity_id` and each unique instrument a stable `route_id`. Search every material entity that could change an atomic path or eligible universe in this order:

1. primary ordinary shares or common stock;
2. secondary or cross-listed ordinary shares;
3. ADR, ADS, GDR, depositary receipt, or equivalent direct claims;
4. new listings, spin-offs, renamed issuers, and ticker changes available by the cutoff;
5. an ETF or other fund only when no direct route satisfies the user's boundary or the user explicitly requests funds.

Complete the route families; do not stop after finding an outside-boundary primary listing. Domicile, headquarters, incorporation, primary-listing country, reporting currency, company name, and an inherited "foreign" label are entity facts, not security-access conclusions. For a U.S. boundary, use the entity's exact legal and common names with the applicable official issuer, exchange, regulator, depositary-program, new-listing, and corporate-action sources to check U.S. secondary listings and ADR/ADS or equivalent claims. Include cutoff-relevant ticker and identifier changes. Country intuition or a foreign primary listing cannot support `outside_boundary`, `no_known_tradable_vehicle`, or an unattempted `direct_unresolved` result.

Interpret this as a mandatory fallback waterfall, not a menu. If the primary share fails the requested boundary, continue to secondary or cross-listings and ADR/ADS or equivalent direct claims before assigning any negative access label. If a remembered or supplied ticker has no quote, search issuer renames, spin-offs, mergers, successors, and ticker changes before creating `pending_verification`; a missing quote is a corporate-action trigger, not evidence that the company lacks a route. Only after direct-route families and cutoff-valid corporate actions are closed may the conditional fund fallback run. A fund is a path or entity exposure vehicle, not the issuer's security, and must never repair a missing direct-route check.

Use bulk mapping for the base inventory, then build and drain a high-impact access queue before running any lower-impact discovery query or adding a lower-impact extension. Before the full identity audit, compute each exact path's provisional count of known eligible direct issuer routes. Automatically enqueue every principal global path member and material substitute on paths with provisional counts `0`, `1`, or `2`; do not wait for a `verified` count, and do not let a failed bulk mapping suppress this trigger. Also enqueue cutoff-relevant new listings, spin-offs, renames or ticker changes, entities whose access could change a path's count bucket, and `direct_unresolved` entities whose resolution could change material path or core coverage. Record a compact queue ledger containing the entity, trigger, exact-name route queries or traversals, applicable route families, targeted official sources attempted, result, and exact remaining failure. Run the targeted route fallback for each queued entity against the applicable issuer, exchange, regulator, depositary-program, new-listing, and corporate-action sources. A positive route needs one cutoff-valid authoritative source. A negative result must complete every applicable route family; for a foreign entity in a U.S. boundary, check the eligible U.S. exchanges, SEC filings, and at least two current cross-depositary directories or an authoritative source identifying the actual program. A queue item is processed only when the positive route is recorded or every bounded targeted check has actually been attempted and its exact result is recorded. `direct_unresolved` is an allowed processed result only after a failed bounded fallback; before that, the queue item remains unprocessed. No batch error, broad theme search, empty general search, country inference, or inherited label processes a queue item or supports a negative result. Only after every queued item is processed may the remaining budget be spent on lower-impact extensions. Lower-impact unresolved entities may retain an explicit access summary and next check without targeted expansion. After a bulk failure, repair only the affected material queue rather than restarting broad discovery.

For every displayed candidate or research lead, record `owner_at_cutoff`, `current_owner_at_retrieval`, material corporate-action effective dates, the cutoff-valid issuer name, ticker or identifier, venue, security type, and predecessor or successor relationships. Apply this before using legacy business descriptions or counting the entity. Immediately before rendering the final report, repeat a final identity sweep over every displayed row: replace a predecessor ticker with the cutoff-valid successor ticker when verified, retain the predecessor only as historical context, and never present an unresolved or stale symbol as current. When the entity is material but its cutoff-valid ticker remains unresolved, display the entity name with `ticker_unresolved` rather than guessing or reusing a remembered symbol. Post-cutoff ownership, renames, listings, and evidence may explain the current state but cannot prove historical availability, ownership, or nonexistence.

Treat every proposed, filed, registered, expected, pending, conditional, or "not yet effective" listing or corporate action as a non-terminal event. Starting at that event date, search forward through the analysis cutoff for the next applicable official state: effective, priced, trading commenced, closed or completed, withdrawn, terminated, delisted, or superseded. Record the dated chain and use the latest cutoff-valid terminal event. Never let an earlier registration filing, announced intention, legacy ticker, or pending transaction override a later exchange, issuer, regulator, or depositary event available by the cutoff. The task environment's current date helps set a default cutoff; it does not perform this follow-through automatically.

Use multiple sources according to decision risk rather than as a universal quota. For a high-impact route-changing event, seek two independent authoritative source classes when available, normally the issuer and one exchange, regulator, or depositary source. A single current authoritative positive source may establish the route when a second authoritative class is genuinely unavailable and the limitation is disclosed. Negative access conclusions continue to require completion of every applicable route family. A routine uncontested number in a filed report does not need duplication merely to reach a source count; management claims that drive candidate inclusion need a later delivery check or an independent counterparty when reasonably available.

A direct route references one `issuer_entity_id`. Record every direct route's market, venue, type, ticker, identifier, currency, cutoff-valid official identity source, liquidity, and material route-specific differences such as depositary ratio, fees, settlement, voting, tax, and currency exposure. Multiple routes for one entity are alternatives, not additional companies and not extra path coverage.

Store each ETF or fund once as a unique indirect route. Link it to any number of entities or atomic paths through separate exposure records containing current holding weight when applicable, as-of date, concentration context, and official sponsor evidence. A fund holding does not make an issuer directly tradable or close an unresolved economic path.

ETF discovery is conditional and bounded. Unless the user requests a fund universe, perform one targeted fund search only for an entity with no eligible direct route, verify representative results through official sponsor holdings and exchange or regulator identity sources, and stop after finding a current material route or no verifiable material route. Do not enumerate every fund holding the entity. A thematic label without current holdings or path evidence is insufficient.

If the user excludes funds, set ETF fallback to `not_applicable`. Otherwise a reference-only fallback inherits the user's requested market and limits itself to exchange-traded funds; it does not create a formal fund universe. A formal ETF universe requires an explicit user request and its own fund boundary.

Derive one entity access summary from its routes and unresolved searches:

- `direct_available`: at least one verified direct route satisfies market, instrument, liquidity-observation, and explicit-rule conditions;
- `direct_unresolved`: a plausible direct route or required direct-route check remains unresolved;
- `indirect_only`: no eligible direct route, but an eligible fund has a current material exposure link;
- `outside_boundary`: verified routes exist, all required searches are complete, but none satisfies the boundary;
- `no_known_tradable_vehicle`: the bounded search completed without a verified route;
- `unresolved`: another material access uncertainty remains.

Treat `indirect_only`, `outside_boundary`, and `no_known_tradable_vehicle` as negative direct-access outcomes. Before assigning any of them, complete the applicable targeted official checks for primary shares, secondary or cross-listings, depositary receipts, and current corporate actions such as new listings, spin-offs, issuer renames, and ticker changes. For every applicable route family, record at least one cutoff-valid official issuer, exchange, regulator, or depositary source plus the search date and result. A source need not explicitly state that no route exists, but every applicable targeted official check must complete without a plausible unresolved route. A verified outside-boundary primary share alone does not prove that no eligible secondary or depositary route exists.

A failed bulk mapping, market-data request, general search, or targeted official lookup cannot support a negative direct-access outcome. If any required route family is blocked, failed, ambiguous, or incomplete after the mandatory targeted fallback, assign `direct_unresolved` or `unresolved`, retain the entity as a research lead, and state the exact failed official check. `direct_unresolved` is a truthful terminal label for a bounded failed fallback, not permission to skip that fallback or inherit a batch failure; do not infer a context-node category from source failure.

Presentation may group routes and repeated analysis, but it may not delete discovered entities or instruments. Preserve at minimum every entity's ID, name, and category; every route's ID, direct-or-indirect type, ticker or identifier, and disposition; and enough fund-exposure identity to show what the route represents. "Checked but omitted for brevity" is not a discovery disposition.

### Stage 2: independently challenge omissions

Review the preliminary inventory separately before declaring coverage complete. When an isolated reviewer is available, provide the scope, closure rule, atomic-path map, relationship inventory, evidence anchors, and proposed categories, but do not provide an expected company list or a prior claim that coverage is complete. Otherwise perform a clearly separated second pass in the same context and disclose that mode.

The reviewer searches for popular-name bias, uncovered demand or commercialization paths, second-order beneficiaries, substitution routes, newly tradable instruments, cross-market access, and paths mapped to only one company without evidence that the concentration is genuine. Apply all of these tests:

- **Atomic-path test**: rerun the buyer-need and purchasing-choice gate when a compound path contains different products, supplier sets, technical implementations, qualification or capacity constraints, revenue models, or company-specific transmission. These differences alone do not force a split. Split only when they establish a separate buyer need or purchasing market or non-substitutability within an economically comparable range. Classify every result before counting it.
- **Sparse-path challenge**: run only after path purity, both global reconstruction directions, provisional business checks, and provisional access checks. Count provisional verified eligible economic entities once per exact path regardless of routes or fund references; do not refer to core or extended before final classification. For a user-requested formal fund pool, count unique provisionally eligible fund routes with usable current material exposure edges to that exact path. Assign bucket `0`, `1`, `2`, or `3+`: bucket `0` requires a path-and-access rebuild, bucket `1` a concentration challenge, bucket `2` a lighter alternatives challenge, and bucket `3+` no sparse check. Recheck same-function competitors, substitutes, technical implementations, integrated or horizontal supply models, and newly accessible securities; classify every result before recounting. This is a recall trigger, not a quota: never add a weak name or force the path to reach three.
- **Relationship inversion**: begin with the required system function and separately traverse its customers, suppliers, equipment, materials, manufacturing, certification, infrastructure, and regulation. A familiar downstream company does not close upstream or enabling paths.
- **Commercialization check**: verify every material way the theme reaches customer spending or revenue inside the closure boundary. Do not silently omit a general-purpose application or distribution path merely because downstream vertical applications are non-exhaustive.
- **Cutoff-appropriate security reconciliation**: revisit material listed and unlisted relationship nodes for primary and secondary listings, depositary receipts, spin-offs, ticker changes, and newly accessible instruments available by the cutoff. Record an explicit access summary for every entity that could change a path or eligible universe. Current-only status cannot prove historical tradability. The audit script validates supplied routes; it cannot discover an issuer omitted from its input. Apply the conditional ETF rule without treating fund exposure as direct issuer identity. Apply the targeted-official-source contract above: any failed, blocked, ambiguous, or incomplete bulk or targeted lookup requires `direct_unresolved` or `unresolved`, not `indirect_only`, `outside_boundary`, or `no_known_tradable_vehicle`.
- **Final-core-set test**: after the verified eligible pool is complete, derive core iteratively. Move a candidate to extended whenever removing it leaves every atomic economic exposure, technical route, business model, constraint, and transmission mechanism represented by the remaining core set. Repeat until no further removal preserves coverage. When candidates are fully interchangeable, retain one justified representative in core and place the others in extended; retain several on one broad path only when each is necessary under this final-set remove-one test. Do not split labels merely to justify a larger core.

The reviewer returns proposed additions, atomic-path splits, category conflicts, and unresolved gaps. Every addition still needs candidate-specific business evidence and security checks. Every new child path repeats membership classification and both Stage 1 broad directions before using its own Stage 2 focused pass, then repeats current-change checks, security mapping, and the provisional path-local sparse check. Any addition, removal, or membership change on an existing path invalidates its previous reconstruction and sparse result until both direction records, dispositions, security map, and bucket are updated through that path's separate Stage 2 focused-pass budget. Reserve the later audit-delta pass for audited conflicts or bucket changes; do not use it for ordinary Stage 2 expansion. If the applicable budget cannot absorb a material change, force `coverage_incomplete`.

Use this bounded order:

`Stage 1 ordered discovery -> Stage 2 omission review and affected-path rebuilds -> provisional path-local sparse checks -> audit full inventory -> recompute audit-confirmed path buckets -> at most one audit-triggered delta review -> audit deltas -> recompute final buckets -> final entity-conservation audit -> latest-source checks -> final-core-set test -> final classification -> substantive coverage proof -> coverage decision`

After the full audit, recompute each path's eligible count and `0`/`1`/`2`/`3+` bucket from audit-confirmed results. A completed sparse check must match this bucket; an earlier check for another bucket is stale. Use the one bounded delta review for any newly sparse path, any change among buckets `0`, `1`, and `2`, or an audit failure, identity conflict, category conflict, or eligibility change that invalidates the path proof. Rerun the affected reconstruction, membership, access, and bucket-appropriate sparse checks, then audit every addition or change. Recompute final buckets once. Do not start another loop: if the final bucket differs from the completed delta check, or a material delta remains unresolved or unaudited, force `coverage_incomplete`. Do not expand merely to increase candidate count.

After the final bucket recomputation and before final classification, run the final entity-conservation audit against a union baseline, not merely the last candidate table. The baseline contains every material entity and route surfaced by system expansion, relationship expansion, the current-change scan, listings and depositary receipts, spin-offs, renames and ticker changes, the high-impact access queue, every split parent and child path, Stage 2, and audit deltas. Every baseline entity needs one entity-level final category; every material path membership must remain on its path, move to one or more explicit child or sibling paths, or become explicit adjacent context. Compare each split parent's membership set with the union of its child-path and adjacent dispositions, and compare the complete baseline with all final categories. Any unexplained disappearance or unprocessed material child path forces `coverage_incomplete`.

Do not hard-code company names, sectors, theme-specific chains, or expected answers. Concrete entities belong only to live research results.

### Classify the universe

Classify in two passes. First assign each entity to context, research lead, or the provisional verified eligible pool:

1. **Context node** when its access summary is `indirect_only`, `outside_boundary`, or `no_known_tradable_vehicle`, or it otherwise fails a verified user boundary. Show any eligible indirect fund separately as a reference route.
2. **Research lead** when its business link is unresolved or its access summary is `direct_unresolved` or `unresolved`. State the exact next verification step.
3. **Verified eligible candidate** when all company and direct-route checks pass. Place every such entity in one provisional pool; do not decide core versus extended by discovery order.

Then apply the iterative final-core-set remove-one test to the full provisional pool. Assign each eligible entity exactly once to **core** or **extended**: core is the smallest defensible coverage set, and the remaining eligible alternatives are extended.

Core and extended are report-compression groups, not quality scores. Both require dated candidate-specific public evidence for chain position and economic transmission, a security identity verified at the cutoff, and an `observed` or `insufficient_history` liquidity result with the available metrics disclosed. Layer-level sources explain why an economic path matters but cannot prove a company's exposure. When an explicit liquidity rule applies, a candidate needs enough history to evaluate and pass it. Without a rule, report `not_applicable`; never invent a liquidity pass. An `unavailable` observation remains a research lead. Do not use the display group as a first-round coarse-screening collection priority or persist it as a candidate state.

Default indirect funds are reference vehicles, not company candidates. If the user explicitly requests a fund universe, maintain a distinct fund-candidate pool. A fund route must have cutoff-valid official identity, satisfy the user's market and fund-type boundary, have an observed or permitted insufficient-history liquidity result, pass any explicit rule, and have current material entity or path exposure supported by official holdings or equivalent strong evidence. Record holdings date, weight where applicable, concentration, expense ratio, liquidity, and tracking limitations.

For every formal candidate, identify a dated candidate-specific economic-transmission anchor during candidate-pool construction and record whether the latest results or filing has been checked. The strongest exposure evidence may be an older contract, approval, patent, standards record, customer disclosure, supplier disclosure, filing, release, or transcript. Complete the latest-results check and reflect newer material changes before a candidate can continue from first-round coarse screening. A generic investor-relations landing page, company overview, search result, or taxonomy index is a navigation lead rather than the strongest candidate evidence. Cross-check material management claims through later delivery or a counterparty when the screening scope permits it. Research quality is determined by what the evidence supports, not by Markdown link style.

For each company candidate, record only chain position, entry reason, economic transmission, economic-entity identity, direct routes, applicable indirect references, liquidity observation status, strongest exposure evidence, latest-results check status, any known newer material change, unresolved checks, and discovery path. Do not build a complete investment dossier during discovery or make a missing valuation field a coverage blocker.

Use roughly 20 verified tradable candidates only as a presentation anchor. It does not limit discovery membership, baseline registration, evidence collection, or first-round coarse screening. A smaller pool is valid when the opportunity set is genuinely narrower, but documentation scarcity, market capitalization, expected elimination, or a desire for a tidy table cannot justify omission. Make core the smallest defensible coverage display and keep every other verified eligible entity in extended. If the displayed universe materially exceeds roughly 30 securities, preserve the full ledger and compress the prose with grouped rows or an explicitly named overflow appendix. Do not delete same-path alternatives or omit ODM/EMS, connectors, storage, smaller suppliers, general platforms, or other eligible names merely because another candidate looks stronger. Never add weak candidates merely to reach the anchor. Count alone cannot establish completeness.

### Audit mapped securities

After Stage 2 revises the preliminary security mapping, batch-audit every provisional eligible candidate and every security-mapped research lead with `scripts/audit_universe.py`. Do not fetch market data for unlisted context nodes. If the bounded delta review adds or changes a mapped security, audit that delta before final classification.

Prepare one route-aware JSON inventory with:

- `schema_version: "1.1"` and a timezone-aware `analysis_cutoff`; legacy `1.0` single-route inputs remain accepted
- `market_boundary` containing non-empty `markets`, `venues`, and `security_types`
- an optional benchmark object with `ticker`
- an optional liquidity rule using `median_turnover`, a 20- or 60-session window, `gte`, a numeric threshold, and a quote currency
- `securities`, each with a unique `route_id`, direct-or-indirect `route_type`, ticker, issuer, expected venue, expected security type, and expected official identifier when known; direct routes also require `issuer_entity_id`

Run:

~~~bash
python scripts/audit_universe.py --input universe.audit.input.json --output -
~~~

In discovery-only mode, use standard input or a temporary input file and keep the JSON result ephemeral. Do not create a run directory or persistent evidence tree.

The audit performs only deterministic checks:

- reconcile ticker, issuer, official identifier, and venue against the official mapping supported for the cutoff; identity status is `verified_at_cutoff`, `current_only`, `conflicting`, `unavailable`, or `unsupported`
- report 20/60-session median turnover, traded sessions, zero-volume sessions, last completed bar, staleness, and limited history
- keep market `observation_status` (`observed`, `insufficient_history`, `unavailable`) separate from liquidity `rule_status` (`pass`, `fail`, `not_applicable`, `unavailable`)
- calculate adjusted-close 20/60-session returns and common-session benchmark-relative returns
- reuse the shared technical formulas for close versus SMA50/SMA200, RSI14, latest MACD histogram and one-session change, ATR14 as a percentage of raw close, price/RSI/ATR 252-session percentiles, 20-session SMA slopes, and the transparent trend regime
- report the latest-five-session median volume divided by the preceding-20-session median volume
- expose duplicates, identifier or venue conflicts, unsupported security-type verification, source failures, and post-cutoff bars

The audit treats multiple direct routes for one `issuer_entity_id` as valid alternatives. It rejects duplicate route IDs, reports a direct ticker or identifier assigned to different issuer entities as a conflict, and audits one fund route only once regardless of how many semantic exposure links reference it.

Only completed bars available by the cutoff may enter calculations. Returns use adjusted close; the shared technical formulas use raw OHLCV and must disclose relevant corporate-action limitations. Turnover is close times volume in quote currency and is called dollar volume only for USD. Do not silently convert currencies.

The audit does not determine business relevance, discover companies absent from the relationship inventory, choose core versus extended, assign a combined score, or write recommendation prose. Use liquidity only to enforce an explicit user boundary. Use trend, momentum, volatility, or relative strength only to trigger another omission or relationship check and as later research context. Strong price action cannot prove theme exposure; weak price action cannot disprove it. For 6–18 month investing these observations remain subordinate to business transmission, earnings sensitivity, expectations, valuation, catalysts, and downside risk.

Network recovery is bounded. The official mapping request uses a certificate-aware HTTP context, an explicit user agent and timeout, and no more than one retry for transient TLS, timeout, rate-limit, or server failures. Market history uses one normal yfinance request and at most one same-vendor fallback request through a different yfinance path. Never loop until success, hide rate limits, switch silently to remembered values, or treat an empty response as verified data.

Script failure does not prohibit a manually verified result when browsing supplies equivalent evidence available by the cutoff. Merge scripted and manual evidence per route and per field rather than assigning one batch-wide status. Manual identity fallback uses the same identity statuses and historical-cutoff rules: a cutoff-valid authoritative manual result replaces `unavailable` for the fields it verifies on that route, while an existing `conflicting` result remains conflicting until the conflict itself is resolved. Never propagate a shared mapping-endpoint failure to routes already verified through authoritative issuer, exchange, regulator, or depositary evidence. Preserve identity and market-observation outcomes separately: an unavailable market observation does not erase a verified official identity, and a verified identity does not imply observed liquidity; for every mapped route, preserve the route-specific identity result and any available market-observation result. Manual liquidity fallback must reproduce completed-bar filtering, 20/60-session windows, quote-currency labeling, observation status, and explicit-rule evaluation; a current quote or a single bar is not equivalent. Record the fallback source, availability date, verified fields or metrics, and original script failure for each affected security. Manual fallback cannot erase a conflict or turn a missing measurement into a pass. The combined scripted and manual results must provide cutoff-valid route identity for every formal candidate. When the user supplied an explicit liquidity rule, the full-inventory audit must also provide a route-specific market observation sufficient to evaluate it. Without an explicit rule, unavailable or short market history is recorded but does not block candidate-pool completion; obtain usable price and valuation context during first-round coarse screening before a company continues. A global assertion, issuer-level check, or non-route-specific batch summary cannot substitute for route identity.

### Check coverage

Maintain a substantive coverage proof for every atomic material path. Record its economic function, demand driver, economic transmission, path-purity decision and reasons, membership criteria, result and evidence anchor for each reconstruction direction, surfaced-entity dispositions, parent-to-child conservation result, bounded-stop rationale, Stage 2 split or rebuild result, final audit-confirmed eligible count and `0`/`1`/`2`/`3+` bucket, bucket-appropriate sparse result, high-impact access outcomes, omission-review result, and unresolved gaps. Also retain the final entity-conservation result and a passed final identity sweep for every displayed ticker. Mark a pass `completed` only when the proof names a relevant evidence anchor, the meaningful alternative or adjacent relationship checked, the result, and any remaining gap. Repeated `completed` labels without this reasoning are declarations, not coverage evidence. Explain every `not_applicable` result; any `blocked` pass forces `coverage_incomplete`.

The proof may be written as prose, compact tables, grouped sections, or another readable chatbot response. Table shape, row count, category placement, candidate count per path, and Markdown style are never completion gates. Preserve resolved omission findings in the reasoning rather than silently dropping them.

A material layer is one whose removal would plausibly change theme-to-economics transmission or the eligible universe within the stated horizon. A high-impact omission is an unresolved gap that could add a distinct economic path or a plausible core candidate. A non-material adjacent path may remain context with a reason, but it cannot contribute candidates to a material path's count.

Finish as `coverage_complete` when both bounded stages and every audit required by the locked completion frontier are complete; every atomic material path passes purity and bounded two-direction reconstruction; every new material child path and materially changed path repeats or updates that work within the bound; every path has the substantive proof above; final audit-confirmed buckets are recomputed; every final bucket `0`, `1`, or `2` has respectively a matching path-and-access rebuild, concentration challenge, or lighter alternatives challenge; no sparse result is stale relative to the final bucket; every applicable high-impact pass has anchors, checked alternatives, results, and remaining gaps; every non-applicable pass has a reason; every material entity has an explicit cutoff-valid access summary; every Stage 2 material addition, split, conflict, and audited delta is resolved or recorded as a non-high-impact exact gap; every material `indirect_only`, `outside_boundary`, or `no_known_tradable_vehicle` outcome has completed targeted official evidence for all applicable direct-route families; every failed, blocked, ambiguous, or incomplete bulk or targeted lookup preserves the affected route as `direct_unresolved` or `unresolved`; the final core set passes the iterative remove-one test; every formal candidate has a dated candidate-specific economic-transmission anchor and at least one eligible verified direct route; every explicit liquidity rule is evaluated; and no unresolved high-impact omission remains. Latest-result completion, detailed market history, expectations, valuation, and comparator analysis belong to first-round coarse screening rather than this coverage status.

Any missing purity decision, reconstruction direction, parent-to-child conservation result, final entity-conservation result, stop rationale, membership disposition, required high-impact targeted fallback, final identity sweep, final count or bucket, matching sparse result, negative-access evidence, or per-route audit result forces `coverage_incomplete` only when it belongs to the locked material frontier or could change a material path, sparse-path access result, plausible core candidate, or finalist set. An unresolved access summary, a route covered only by a global or non-route-specific assertion, a displayed ticker unsupported as current at the cutoff, or an unavailable liquidity observation has the same materiality test. An unevaluable explicit liquidity rule always forces `coverage_incomplete`. Lower-impact unresolved adjacency must be disclosed but cannot downgrade an otherwise complete material universe. Candidate count and presentation format never determine this status.

Unavailable browsing or required current sources, material conflicts, identity that is only current for a historical cutoff, unverifiable listings or required liquidity, and evidence stale relative to the cutoff and horizon keep any plausibly eligible affected entity as a research lead. Use a context node only when ineligibility or indirect-only access is positively verified under the targeted evidence contract. If the problem could change a material layer or core pool, the result is `coverage_incomplete`.

For discovery-only requests, return one natural-language report and stop. Include a compact search audit grouped by source job: universe discovery, security routes, corporate actions, business verification, and market audit. For each job state the source classes or sites used, query or traversal lens, call count, failures or empty results, fallback taken, and any unresolved material entity. For every high-impact foreign entity and every principal global member triggered by a provisional `0`, `1`, or `2` path, disclose the entity-level route outcome, authoritative source or exact failed source, and remaining route family; a grouped claim that exchanges, regulators, or depositary sources were checked is insufficient. Returning `coverage_incomplete` does not excuse an unattempted high-impact route check or permit lower-impact expansion first. A list of issuer pages does not demonstrate that universe discovery or route mapping ran. Do not initialize a screening run, freeze evidence, create a run directory, rank, eliminate, register finalists, or execute councils unless the user explicitly asks for persistent artifacts. This applies to both completion statuses.

## First-round coarse screening

Begin a full theme screening run after registering either a `coverage_complete` full-universe baseline or, after the bounded targeted fallback, a `coverage_incomplete` resolved-subset baseline. Closed comparisons begin here without a theme coverage claim.

This remains a deterministic gate, but it no longer requires every discovered entity to be fully resolved before a terminal-outcome request can proceed. When bounded authoritative fallback leaves material unresolved routes, classify them as research leads and screen only verified candidates. The unresolved fact limits the conclusion's scope; it does not become an implicit elimination, enter finalist comparison, or justify an exhaustive-best claim. Stop with only an unranked discovery queue when no verified candidate set or no usable current evidence for that set remains. A shared batch endpoint, preferred search adapter, individual source failure, unavailable quote history, or one unresolved company is otherwise a disclosed limitation rather than a global stop.

After creating the temporary screening run and before freezing evidence, register one discovery baseline with `state_store.py baseline`. A fully resolved ledger uses `coverage_status: coverage_complete` and `screening_scope: full_universe`. A bounded partial ledger uses `coverage_status: coverage_incomplete` and `screening_scope: resolved_subset`; every unresolved route must be a `research_lead` with `impact_level`, `unresolved_fact`, `attempted_source_refs`, and `next_check`, while every formal `candidate` still needs an eligible verified requested-market route. The baseline contains every material candidate-pool-construction entity, its atomic path IDs and disposition, the fund policy, and a `route_resolution` checked through the exact cutoff. `route_resolution.direct_route_families` explicitly disposes `primary`, `secondary`, `depositary`, and `corporate_action`; `unresolved` is incompatible with `coverage_complete` but valid for a documented research lead in a resolved-subset baseline. Every attempted family records at least one source or evidence reference plus a reason. Every baseline candidate then appears exactly once in the first-round coarse-screening candidate ledger; research leads do not enter the candidate ledger or finalist comparison. Research prioritization may group paths for readability but must preserve each candidate's original atomic-path memberships. Any material discovery addition requires updating the affected path and registering a new run; screening cannot silently shrink, expand, or rewrite the baseline.

This registration is an execution gate, not optional documentation. The eligible candidate-pool IDs and their atomic-path memberships are immutable inputs to the coarse screen; display compression cannot change them. Run deterministic baseline reconciliation before rendering dispositions, including in a temporary chat run. If deterministic baseline reconciliation is not executed successfully, report that first-round coarse screening was not completed. A polished table, hand-checked subtotal, or self-consistent reduced list cannot substitute for this gate.

Liquidity is also a hard provenance rule. Only a numeric threshold or equivalent rule explicitly supplied by the user may produce `pass` or `fail`. Words such as "normal," "tradable," or "sufficient" do not authorize the model to invent a dollar-volume, market-cap, price, or history threshold. Without an explicit rule, keep `liquidity_rule` absent, set every rule result to `not_applicable`, disclose available observations only, and do not use liquidity as an advancement or elimination reason.

Map core and extended candidates into the existing candidate-ledger fields in `discovered` state. A research lead may enter only after issuer, unique security identity, venue, and market are resolved; otherwise retain it in the research queue. Do not add fields or states to preserve discovery display classes.

Treat one economic entity as one company thesis and normally one core council. Audit and compare all eligible direct routes, then use an explicitly requested route or the route best matching the user's market, instrument, currency, and liquidity constraints as the default market-data carrier. Comparable same-currency routes may use higher 60-session median turnover as a deterministic tie-breaker. Split out route-specific analysis or councils when voting, legal claim, tax, depositary, settlement, currency, or liquidity differences could materially change the conclusion, or when the user requests a cross-listing or arbitrage comparison. Ask the user only when the route choice is genuinely consequential and cannot be resolved from the stated constraints and evidence.

Default indirect fund references do not enter first-round coarse screening. When funds are explicitly part of the formal universe, hand off each unique eligible fund route using its `route_id` as candidate ID and analyze the fund as one portfolio vehicle rather than duplicating it because it has many holdings. An underlying company receives a company council only when it independently qualifies as a company candidate.

### Frame the screening decision

The objective is not to identify the strongest companies in hindsight. It is to find securities whose prospective reward over the user's horizon is attractive relative to what the market already expects and to the available alternatives.

Use this causal frame without turning it into a deterministic score:

`system change -> company earnings transmission -> expectations gap -> valuation and asymmetry -> catalyst timing -> downside and invalidation`

Scarcity, bottleneck control, qualification time, and expansion difficulty can strengthen the transmission or durability case, but none is a mandatory gate. A demand-side platform, diversified company, integrator, or downstream commercializer may advance when monetization, expectations, valuation, timing, and downside are more attractive. Do not eliminate a company solely because it is popular, diversified, a capital spender, a buyer rather than supplier, or outside the scarcest upstream layer.

Distinguish explicitly between:

- a good business;
- a business benefiting from the theme;
- an attractive security at the current price and horizon.

Evidence that proves only the first two cannot establish the third.

Do not mark a security advanced, shortlisted, or suitable to continue merely because valuation and expectations will be studied later. Every proposed continuer needs a cutoff-valid light expectations and valuation view before the decision; unavailable precision requires a labeled proxy, not postponement.

### Stage 1: prioritize economic layers

Restore prioritization only after discovery is complete. Compare atomic layers before companies and assign a working research priority of `priority`, `watch`, or `deprioritized`. These are natural-language research labels, not candidate states or permanent sector judgments.

Produce and present the layer-priority decision before assigning any company state. The decision must cover every atomic layer represented in the eligible pool, state the causal reason and horizon fit, and identify the candidates carried from that layer into deeper screening. Every later company transition must reference this layer decision while still giving a company-specific reason. If the layer decision is missing, implicit, or reconstructed after company selection, first-round coarse screening has not validly started.

For each layer explain:

- what system change is accelerating, decelerating, or changing direction;
- how demand reaches orders, utilization, price, revenue, margin, cash flow, or asset value;
- the transmission lag relative to the user's horizon;
- supply concentration, qualification time, expansion difficulty, scarce inputs, price acceptance, regulation, and infrastructure constraints where relevant;
- what customers can substitute, internalize, defer, or overbuild;
- what expectations appear embedded in capacity plans, guidance, public estimates, valuation, and recent price response;
- the dated catalysts and the principal cyclical or structural downside.

Do not rank a layer highly merely because it was a historic bottleneck. Ask whether the constraint is tightening or relaxing now, whether incremental economics accrue to listed suppliers, and whether the expected benefit arrives inside the horizon. Do not deprioritize a layer merely because it has many suppliers when demand growth, consolidation, operating leverage, or a company-specific change can still create attractive asymmetry.

Before excluding an entire buyer, demand-side, integrator, or downstream class as indirect or impure, test whether the system change can alter its pricing power, asset value, cost absorption, market share, capital returns, or downside. Retain materially differentiated eligible routes even when their exposure is not a pure upstream bottleneck. Path purity helps explain transmission; it is not an automatic exclusion rule.

### Stage 2: compare companies

Research progressively using [evidence.md](evidence.md). Reuse valid candidate-pool identity, exposure, latest-results, liquidity, and market-overlay evidence rather than recollecting it. Run a light baseline pass for every candidate, then spend deeper research only on companies that could plausibly advance.

Within each layer and across the highest-priority layers, compare every plausible contender on:

- **Transmission and materiality**: how much of the system change can reach the company's revenue, margin, cash flow, assets, or per-share value, and on what lag;
- **Delivery and financial quality**: orders, backlog conversion, utilization, pricing, margins, working capital, cash conversion, balance sheet, dilution, and management claim versus delivery as applicable;
- **Expectations gap**: what guidance, public estimates, valuation, narrative, recent earnings reaction, and price behavior imply, with unavailable consensus stated rather than invented;
- **Valuation and asymmetry**: valuation relative to growth, quality, history, peers, and plausible base/bull/bear outcomes; neither a high nor low multiple decides the result by itself;
- **Catalyst clock**: dated results, product ramps, qualifications, contracts, permits, capacity, pricing resets, regulatory decisions, or other events likely to resolve the thesis within the horizon;
- **Downside and invalidation**: substitution, customer concentration, cyclicality, capex reversal, execution, governance, financing, legal, geopolitical, liquidity, and thesis-breaking facts;
- **Relative opportunity**: why this security is preferable to its nearest listed substitute, the obvious incumbent, and the best candidate from another priority layer under comparable risk.

A cutoff-valid light expectations and valuation check is mandatory for every proposed continuer. Use the most decision-relevant available combination of public estimates or guidance, revision direction, peer and historical multiples, cash-flow or asset-value measures, scenario-implied outcomes, and recent catalyst reactions. Select the method before comparing numbers: normalize ADR/ADS depositary ratio, currency, route rights, and issuer economics; use FFO/AFFO or NAV and leverage for REITs; mid-cycle margins and free cash flow for cyclicals; cash runway, dilution, milestones, and scenario or risk-adjusted value for pre-revenue companies; and net debt, interest coverage, committed capex or leases, customer concentration, and free cash flow for capital-intensive operators. A conventional P/E may be useful for a mature profitable company, but a standalone forward P/E from an aggregator cannot decide continuation, elimination, or re-entry. If exact consensus or a standard multiple is unavailable, use and label a defensible proxy. Price strength or a strong operating result alone cannot establish an expectations gap. Expectations and valuation may not be postponed to a later round as the reason to advance now. Re-entry conditions must combine a business or evidence change with an expectations or valuation condition when price is material; do not use an arbitrary hard multiple threshold as the sole condition.

If the coarse screen uses numeric Bear/Base/Bull cases, either probability-weight them with probabilities totaling 100% and a stated rationale or label them as unweighted stress tests. Do not rank candidates by an unweighted base-case midpoint presented as expected value.

Build the comparison set before deciding. A proposed "nearest substitute" must first pass comparator eligibility: it should share substantially the same economic transmission or end-market need and be sufficiently comparable in commercialization or operating maturity, cash-flow and financing risk, catalyst horizon, and economic rights. Disclose material differences and use industry-appropriate valuation methods. Market capitalization, enterprise value, price momentum, or analyst targets alone do not make two securities comparable. If maturity, rights, financing, or horizon differences dominate, do not call the other security the nearest substitute; label it as a cross-layer or cross-stage opportunity-cost comparison instead.

Every proposed continuer needs one explicit head-to-head conclusion against a comparator-eligible nearest substitute. When no such listed substitute exists, document that fact and use the best available same-objective candidate only as a clearly labeled opportunity-cost comparison. Also challenge the candidate against the best company from another priority layer when risk and horizon are reasonably comparable. If the evidence cannot support a relative preference, keep researching or eliminate it for the current run rather than advancing a group of individually attractive companies together.

The shared macro snapshot and candidate-level technical or relative-strength observations may affect trading suitability, catalyst timing, crowding, risk budget, and entry conditions. They cannot prove theme exposure, rescue a weak investment transmission, or mechanically determine a company disposition. For longer-horizon investment screening they remain subordinate to earnings transmission, expectations, valuation, catalysts, and downside. Preserve missing VIX, rate, FX, percentile, or trend inputs as explicit limitations rather than neutral assumptions.

If no usable current source class is available for any verified candidate, do not rank remembered company names or classify them as trading or investment picks. Produce the system map, exact source plan, and an unranked research queue labeled unverified. An individual candidate or source failure stays outside the comparison as a research lead while the verified set continues.

### Maintain the candidate ledger

For every candidate record:

- candidate ID, ticker, company, market, and chain position
- why it entered
- layer priority and horizon fit
- theme-to-company transmission and materiality
- evidence collected and evidence strength
- management claims and delivery evidence
- expectations evidence and what appears priced in
- valuation context and scenario asymmetry
- dated catalysts and their expected resolution window
- liquidity and exitability
- missing proof
- main risks, invalidation, nearest substitutes, and relative-opportunity conclusion
- suitability for investment, trading, both, or neither when the evidence supports that distinction
- current state and transition reason
- what evidence could reverse an elimination

Before rendering or registering the shortlist, perform an exact-set reconciliation rather than comparing hand-written totals:

- the discovery entity union must equal eligible candidates plus explicitly classified research leads, indirect references, outside-boundary entities, and context nodes;
- the displayed candidate-map identifiers must equal the candidate-ledger identifiers unless an explicitly named overflow appendix contains the remainder;
- the eligible candidate set must equal the disjoint union of `discovered`, `researching`, `pending_verification`, `advanced`, and `eliminated` states at the stopping point;
- every displayed count must be derived from those sets, and every candidate must have its own transition reason and re-entry condition even when prose groups similar outcomes.

Any missing, duplicated, or silently disappearing entity blocks completion. Returning `coverage_incomplete` does not excuse an internally inconsistent map or ledger.

The deterministic candidate registration must also match the previously registered candidate-pool baseline. A self-consistent subtotal over a newly reduced coarse-screening list is not conservation and must be rejected.

Persisted states are:

- discovered
- researching
- pending_verification
- advanced
- eliminated

A pending candidate returns to researching when new evidence arrives. Only advanced candidates may enter `finalists.json`.

Layer `watch` is not a company disposition. Do not use `watch`, `observe`, `defer`, `暂缓`, or similar prose as an extra candidate state in the completed coarse-screen output. Map every company to the existing state model and explain the transition. For a coarse-screen-only request, a candidate selected for deeper screening remains `researching`; call it `advanced` only after the full finalist gates are met. Stopping before councils does not relax the expectations, valuation, relative-comparison, or pending requirements.

`pending_verification` is not a default parking state for every company lacking a perfect dossier. Use it only when one or a small number of named, decision-critical facts remain realistically obtainable and could change advancement. Record the exact source or event, why it matters, and when it can be checked. “Needs more evidence,” “AI exposure unclear,” or “valuation missing” without a bounded next check is invalid.

Short trading history is a market-observation status, not a candidate disposition. An official new listing with `insufficient_history`, an available ADR ratio, preliminary or partial official results, or a future periodic filing does not by itself justify `pending_verification`. Use the best cutoff-valid evidence already available and decide `researching` or `eliminated` when the economic case is sufficiently clear. A future periodic filing creates pending only when a named disclosure in that filing is realistically expected, is not already answerable from registration statements or current filings, and could plausibly change the finalist set.

Before freezing the shortlist, run one consolidated gap-closure pass for every material pending candidate. Then:

- advance it when the comparative case is supported;
- eliminate it for this run when the available evidence already makes it inferior, the missing basics remain unproven after the targeted pass, or the catalyst falls outside the horizon;
- retain it as pending only when the named unresolved fact could plausibly change the finalist set.

For a coarse-screen-only request, unresolved priority-layer pending candidates make the screen incomplete. For a terminal-outcome request, one consolidated gap-closure pass is still mandatory; any remaining name stays `pending_verification`, is excluded from finalists, and the verified finalists continue to councils. The final comparison must name those exclusions, describe how they could change the result, and state that its preference is conditional on the verified universe. A large pending population is evidence that baseline collection or prioritization failed and materially lowers confidence; never hide it behind an exhaustive-best claim.

### Apply the gates

A finalist must have:

- an identifiable chain position and a plausible path from theme demand to company economics
- credible candidate-specific evidence for business position and current results
- credible evidence for demand transmission, delivery, financial quality, or customer validation
- material control, supply, demand, asset, platform, distribution, or other economic exposure to the relevant layer
- an explicit view of what the market appears to expect and where the evidence may differ
- valuation or scenario evidence sufficient to judge prospective asymmetry
- at least one plausible catalyst or thesis-resolution event inside the user's horizon
- liquidity and exitability appropriate to the requested use
- no unresolved fatal financing, accounting, governance, legal, or geopolitical issue
- explicit failure conditions, substitution routes, and a comparative reason to prefer it over the nearest alternative

Do not waive the expectations, valuation, and relative-preference gates because the request says first pass, first round, or coarse screen. Those requests may stop before decision packs, finalist registration, or councils, but every company reported as continuing still needs enough evidence to justify spending the next unit of research effort relative to the alternatives.

Advancement is comparative, not a checklist victory. A candidate that technically passes every minimum gate may still be eliminated when another security offers clearly better transmission, expectations gap, catalyst timing, or downside-adjusted asymmetry. Conversely, obscurity, incomplete segment disclosure, or weaker source availability alone is not an elimination reason.

Eliminate for the current run when evidence supports one or more decisive conclusions: immaterial or too-slow transmission, thesis already more than reflected without compensating upside, unattractive downside-adjusted valuation, catalyst outside the horizon, structurally weak economics, fatal quality or governance risk, or clear inferiority to available alternatives. State the decisive reason and a concrete re-entry condition. Do not translate a missing document into a negative business fact.

### Review eliminations

The Screening Reviewer challenges every material elimination:

- Was weak visibility mistaken for weak economics?
- Did abundant English-language or issuer evidence privilege a familiar company over a less documented competitor?
- Was a popular leader advanced because its strength is obvious without proving prospective return relative to expectations?
- Was a company excluded using only its own statement or a single media report?
- Is the missing evidence realistically obtainable?
- Does a less obvious upstream layer deserve priority?
- Was a demand-side, diversified, integrator, or downstream company dismissed merely for not being a bottleneck?
- Is the claimed expectations gap supported, and was valuation compared on a like-for-like basis?
- Could any pending or eliminated candidate replace an advanced candidate under the same horizon and risk budget?
- What new fact would put the company back into research?

The reviewer also challenges every advanced candidate for evidence-availability bias, famous-name bias, stale bottleneck logic, hidden correlation with other finalists, and failure to beat its nearest substitute. Resolve material challenges before registering finalists.

The reviewer also challenges every whole-class exclusion. A claim that buyers, downstream companies, diversified operators, or other demand-side routes are insufficiently pure must show that differentiated transmission was tested rather than assumed away.

Commit natural-language scope, system map, candidate ledger, and shortlist reports. Register the matching machine-readable `candidates.json` and `finalists.json`.

An advanced candidate requires at least one usable frozen screening record. Every finalist also requires a usable record whose candidate ID or subject ID matches that finalist. Generic theme evidence alone cannot support finalist membership.

## Management claim versus delivery

Do not treat guidance as verified performance. Compare material management claims with later evidence where available:

- orders and backlog
- revenue mix and growth
- gross margin and pricing
- cash flow and working capital
- capital expenditure and capacity
- customer or supplier disclosures
- product qualification and regulatory progress

Classify the result as delivered, partly delivered, not yet testable, contradicted, or superseded. Explain the dates and evidence.

## Complete finalist councils

For each registered finalist:

1. Create an independent child instrument run linked to the parent screening run.
2. Inherit shared and candidate-relevant frozen screening evidence.
3. Add Yahoo Finance market data and any new candidate-specific public evidence.
4. Inherit the parent macro snapshot, calculate technical indicators and percentiles, reconcile the market snapshot, and freeze evidence once. Do not refetch shared macro series in the child.
5. Run every analyst, Bull/Bear round, Research Manager, Trader, risk round, and Portfolio Manager.
6. Assemble, commit the complete report, and verify state.

A failed or partial child is disclosed and excluded from cross-company ranking.

Bind every child manifest to the exact parent run ID, parent evidence hash, finalist candidate ID, requested and canonical ticker, market, and relevant subject IDs. Parent comparison accepts only terminal children whose manifests, state hashes, evidence, stage order, and committed artifacts verify.

## Final comparison

Compare completed Portfolio Manager decisions. Do not average role opinions or manufacture unanimity.

For every surviving company explain:

- chain position and scarce-layer relevance
- council rating and exposure intent
- whether it suits trading, longer-term investment, both, or neither
- management claim versus delivery result
- strongest evidence
- strongest dissent
- liquidity and exit conditions
- thesis invalidation

Return an unbounded ranked list and a preferred candidate only when justified. If no candidate clears the standard, say that there is no current recommendation and list the evidence that could change the result.

For a resolved-subset run, rank only completed verified finalists. Lead with the scope limitation, name unresolved research leads and pending candidates that could alter the order, and label any preference as conditional on the verified universe. Never describe it as the exhaustive best security across the original theme.

## Thesis timeline

Every full council states:

- when the thesis became plausible
- which evidence strengthened or weakened it
- what management said would happen
- what subsequently happened
- what future fact would downgrade or invalidate the thesis

Later runs must explain what changed instead of silently replacing the prior view.
