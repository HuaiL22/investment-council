# Evidence

Read this reference when collecting, freezing, or interpreting evidence.

## Source statuses

Each source is `available`, `partial`, `conflict`, `stale`, `unavailable`, `historical_unavailable`, `quarantined`, or `inapplicable`.

- Use available evidence normally and partial evidence with a visible caveat.
- Show conflicting values without inventing a reconciliation.
- Do not use stale, unavailable, historically unavailable, or quarantined records as support.
- Omit inapplicable fields without treating them as missing.

## Time integrity

Every analytical record needs a trustworthy availability time at or before the cutoff.

- Exclude future or undated historical news.
- Treat daily bars as available no earlier than the next local midnight.
- Treat current-only identity and fundamental snapshots as available at fetch time; quarantine them when fetched after the cutoff.
- Require publication or filing dates for historical statements.
- Use raw OHLC for quotes, entries, stops, targets, and indicators.
- Use adjusted close only for total-return and outcome calculations.
- Select the latest completed session at or before the cutoff.

`state_store.py freeze` rechecks the bundle hash, record hashes, record and OHLC availability, run ID, ticker identity, and cutoff.

## Frozen contract

Each evidence record contains an evidence ID, source, source URL when available, fetch time, observation time, availability time, status, subject, field, value, unit or currency, adjustment basis, and content hash.

The frozen envelope contains schema version, bundle kind, run ID, cutoff, fetch time, source statuses, rejected records, OHLCV, evidence records, blocks, and optional parent metadata. Screening bundles have empty OHLCV.

Codex cites material facts and exact numbers with evidence IDs. Evidence IDs provide traceability; they do not force the prose into a schema.

## Macro and technical snapshots

Every complete run enables one compact macro snapshot unless the user explicitly disables it. The default series are VIX, the U.S. 2-year and 10-year Treasury yields, and DXY; derive the 2s10s spread only from same-date available yield observations. Add an issuer-relevant FX pair when translated revenue, foreign assets, funding currency, or a depositary route makes it material. For each available source series retain the latest completed observation, 20/60-session change, 252-session percentile, observation time, availability time, source ticker, and unit. Express yield changes and the term spread in basis points, and index or FX changes in percent. Do not store the full macro price history in the frozen bundle.

For theme runs, collect macro context once in the screening parent as shared evidence. Finalist children inherit the frozen records rather than refetching them. A source failure remains visible per series and lowers timing confidence; it does not become a neutral value or invalidate otherwise usable company evidence. Numeric macro records are analytical inputs. Council roles, not the collector, infer whether the combined environment is risk-on, neutral, risk-off, or mixed.

The technical block retains its calculated series and adds one compact current snapshot. The snapshot contains RSI14, price/RSI/ATR 252-session percentiles, SMA50/SMA200 20-session slopes, and a transparent trend regime. Preserve `insufficient_history` unless the full configured window exists. Use raw close for indicators and adjusted close only for return comparisons. Technical and macro evidence may alter execution timing, exposure, and confidence; neither can independently establish business quality, valuation attractiveness, or a Buy/Sell rating.

## Evidence strength and kind

- Strong: filings, exchange or regulator records, official announcements, transcripts, contracts, patents, standards, certifications, and hard technical documents.
- Medium: reputable financial media, trade publications, industry associations, company product pages, and customer or supplier cross-checks.
- Weak: specialist commentary with incomplete assumptions, social posts, forum discussion, screenshots, or unexplained price action.
- Unverified: an important lead lacking adequate source, date, or confirmation.

Classify each supplemental record as:

- `observed_fact`: a dated public observation
- `management_claim`: company guidance, targets, forecasts, customer claims, strategy, or capacity claims
- `analytical_input`: a sourced technical or industry input
- `unverified_lead`: a lead awaiting confirmation

Weak or unverified evidence may guide research but cannot independently support advancement, finalist membership, ranking, or a trading-versus-investment classification. Codex inference stays in prose.

## Supplemental JSON

Use a UTF-8 JSON object with a `records` array. Each record requires:

- source and absolute HTTP(S) source URL or null
- subject ID, field, and JSON value
- observed time or null
- timezone-aware availability and fetch times
- evidence strength and kind
- scope: `shared` or `candidate`
- candidate IDs, empty for shared records

Missing or invalid availability is rejected. A record after the cutoff is rejected. A current record without a source URL becomes an unverified lead; a historical record without a URL is rejected.

Identical identities deduplicate. Different values for the same subject, field, and time remain visible as conflicts. Rejections appear in `supplement_rejections` and never support analysis.

Inherited records preserve IDs and hashes. The child records the exact parent run ID, parent evidence hash, and inherited evidence IDs.

## Source order

Prefer:

1. primary disclosure or official technical record
2. independent primary cross-check from a customer, supplier, regulator, or project
3. reputable media or trade publication
4. specialist analysis
5. social or forum lead

For a finalist, seek one credible source for business position and another for demand, customer validation, or financial quality.

## Progressive screening evidence

Do not build a full council dossier for the entire discovery universe. Allocate evidence in three waves and preserve valid candidate-pool-construction records:

1. **Baseline pass — every candidate**: cutoff-valid identity and route, available liquidity observation, strongest economic-exposure anchor, latest results or filing, the material system change, and current price context. This is first-round coarse-screening work, not a candidate-pool completion gate. Obtain a light financial, expectations, and valuation snapshot for every candidate that could continue; use labeled proxies when exact consensus or a standard multiple is unavailable. If no explicit liquidity rule exists, unavailable or short quote history is disclosed and cannot by itself stop the screen or determine the disposition.
2. **Contender pass — plausible candidates from relevant layers**: quantify or bound demand-to-earnings transmission, management delivery, financial quality, expectations, valuation, catalyst timing, downside, and the nearest alternatives. Use one consolidated targeted search to close the decision-critical gaps identified by the baseline.
3. **Decision pack — potential finalists**: obtain the strongest candidate-specific and independent evidence needed to support advancement, including a counterparty, regulator, project, customer, supplier, competitor, or later reported result when the thesis depends on one. Record base, upside, downside, catalyst, and invalidation evidence without pretending to complete the later council.

Research depth follows decision relevance, not company fame, discovery order, market capitalization, source convenience, or the candidate-pool core/extended display split. A candidate with abundant issuer material does not automatically outrank one requiring local-language, regulator, customer, project, or technical records.

Select sources from the company's actual transmission mechanism. Relevant records may include periodic and current filings, earnings calls, exchange inquiries, investor Q&A, tenders and awards, environmental or energy approvals, construction and grid records, patents, standards, customer qualification, product certification, customs or shipment data, contracts, backlog, capacity reservations, pricing, and counterparty disclosures. This is a routing menu, not a mandatory checklist for every company.

For expectations and valuation, prefer cutoff-valid public estimates, company guidance, peer and historical multiples, revision direction, recent earnings or catalyst reactions, and scenario-implied outcomes. Establish like-for-like comparability before using peer multiples or relative valuation: account for commercialization or operating maturity, revenue and cash-flow stage, capital structure and financing needs, currency, catalyst horizon, and the economic rights actually owned by the listed issuer. When those differences dominate, use an industry-appropriate scenario, asset, cash-flow, or risk-adjusted method and label the comparison as cross-stage or opportunity-cost rather than nearest-substitute evidence. Analyst targets, enterprise value, or recent price performance cannot by themselves establish relative attractiveness. When consensus, segment economics, or a comparable multiple is unavailable, state the gap and use labeled proxies; never invent a consensus figure or imply that price appreciation proves expectations.

Choose valuation evidence by security and business model before looking at the result:

- for ADR/ADS and cross-listed routes, verify the depositary ratio, currency, economic rights, and issuer-route relationship before accepting per-share or enterprise-value fields;
- for REITs and asset-backed operators, prefer FFO/AFFO, NAV, leverage, financing cost, development yield, and contracted cash-flow conversion;
- for cyclicals, normalize margins, working capital, capex, and free cash flow across the cycle instead of capitalizing peak earnings;
- for pre-revenue, clinical, early-energy, or milestone businesses, use cash runway, dilution, milestone timing, probability-weighted or scenario value, and downside funding needs;
- for capital-intensive cloud, data-center, manufacturing, or infrastructure operators, include net debt, interest coverage, leases and committed capex, customer concentration, utilization, and free-cash-flow conversion;
- for mature profitable companies, P/E may be one input alongside cash flow, revisions, quality, and history.

Preserve financial-statement taxonomy when converting source material into evidence. Total receivables, trade receivables, other receivables, customer deposits, contract liabilities, commitments, and financing proceeds are not interchangeable. Use the source's reported label unless a cited note supports a narrower classification.

Numeric Bear/Base/Bull cases are either probability-weighted decision inputs or unweighted stress tests. A probability-weighted presentation must show probabilities totaling 100%, the rationale for those weights, and the calculation. An unweighted presentation must not describe the base-case midpoint as expected value, a target, or supported upside.

Reject or label third-party valuation fields when currency, share class, depositary ratio, negative earnings, accounting basis, or corporate action makes them non-comparable. A standalone forward P/E, sales multiple, analyst target, or hard multiple threshold cannot by itself continue, eliminate, rank, or define re-entry for a candidate.

A candidate cannot be marked for advancement or continued deep screening on operating strength alone while expectations or valuation are reserved for the next round. The first pass need not build a full valuation model, but it must establish enough current price context and asymmetry evidence to justify further research relative to the nearest alternative.

Missing evidence has different consequences:

- a missing non-decisive detail lowers confidence but need not create pending;
- a named, obtainable fact that could change the finalist set may create `pending_verification` and one consolidated gap-closure pass;
- missing basic exposure, current results, or transmission evidence after that pass prevents advancement;
- unavailable evidence is not evidence of weak economics and must not be rewritten as a negative fact.

Do not convert market-data or document-timing labels into candidate states. `insufficient_history`, a recent official listing, preliminary official results, or an upcoming 10-Q/20-F is not by itself `pending_verification`. Use existing registration statements, current reports, exchange or depositary records, and issuer evidence first. Pending is valid only for a named fact that remains unavailable after that work and could plausibly alter the comparative decision.

## Market-specific paths

- United States: SEC filings, transcripts, investor materials, official releases, customer and supplier filings, standards, patents, and trade publications. Check dilution, converts, compensation, insider selling, customer concentration, backlog, margins, utilization, and liquidity.
- A-shares: periodic and temporary announcements, exchange inquiries, 互动易 or 上证 e 互动, tenders, approvals, project filings, patents, standards, customer certification, customs data, and chain disclosures. Check receivables, inventory, contract liabilities, cash flow, margins, utilization, construction in progress, related transactions, refinancing, pledges, goodwill, subsidies, and order quality.
- Hong Kong: HKEX filings, annual and interim reports, placements, subscriptions, converts, connected transactions, presentations, and relevant mainland records. Check liquidity, refinancing, governance, Stock Connect, and policy exposure.
- Taiwan, Japan, Korea, and Europe: local filings, monthly operating data where available, IR, export statistics, trade journals, standards, customer cross-checks, and official project records. Check FX, geopolitics, concentration, capex timing, liquidity, and grant dependence.

## Missing evidence

State what failed, what remains usable, and how confidence changes. Missing primary proof creates `pending_verification` only when the missing fact is named, obtainable, decision-critical, and could change the finalist set. Otherwise disclose the confidence reduction or prevent advancement when a minimum proof is absent. Name the exact filing, exchange, regulator, customer, or technical source to check next.

For an instrument run with no usable record, stop before analyst roles and emit no rating or exposure intent. Never replace missing evidence with a model guess.

For crypto, company statements and insider data are `inapplicable`, not unavailable.
