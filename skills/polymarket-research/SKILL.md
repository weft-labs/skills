---
name: polymarket-research
description: "Research any Polymarket market or event link into a cited, timestamped decision brief. Use whenever a user shares a Polymarket URL, asks what a market actually resolves on, wants current odds, liquidity, order-book context, financial, sports, or news evidence, asks for the YES and NO cases, or wants to know what changed or whether a market may be mispriced. This is read-only research: never connect a wallet or place a trade."
---

# Polymarket Research

Turn one Polymarket link into an evidence-led brief about the contract, the
current market, and the outside world. Research the contract before the
headline. A correct forecast of the real-world event can still lose when the
market settles on a narrower source, definition, or deadline.

Before research, read:

- [references/polymarket-data.md](references/polymarket-data.md) for official
  surfaces, identifier rules, and data-quality checks;
- [references/report-template.md](references/report-template.md) for the exact
  output structure.

This workflow is read-only. Never place an order, connect a wallet, or automate
execution. The report is research, not financial advice.

## Input

Accept one of:

- a `polymarket.com/event/<slug>` URL;
- a Polymarket market URL or sports URL;
- an unambiguous event slug.

If the user gives several links, compare them only when requested. Otherwise,
ask which one owns the decision. Never silently replace a missing market with a
title-similar market.

Record at the start:

- the canonical URL;
- research start time in UTC;
- requested depth: `quick` or `thorough`;
- whether the user wants a probability range or only an evidence brief;
- any prior report supplied for refresh mode.

For a current report, do not use the research start as the evidence cutoff. Set
the cutoff only during final reconciliation, after the last source retrieval or
live-market observation that the report accepts. Use Historical cutoff mode when
the user asks what was knowable as of a past date.

Use `quick` when the user wants a short factual check. Use `thorough` for a
pre-decision brief, a disputed or ambiguous contract, or an explicit request for
many searches or subagents.

## Required Flow

### 1. Resolve the exact market

Resolve the URL to the canonical event and all relevant market legs. Keep these
identifiers separate:

- event ID and event slug;
- market ID and market slug;
- condition ID and question ID;
- outcome token or asset IDs;
- outcome labels and indexes.

Start with the event slug endpoint. If the URL selects one leg, retain the full
event context and mark the selected leg. If the exact slug does not resolve,
use Polymarket's public search only to diagnose the missing identity. Stop with
a blocked report unless the user confirms a replacement.

Do not use a search-engine excerpt, AI-generated market context, or copied title
as the controlling rules. Read the complete live rules and the named resolution
source from the canonical market.

### 2. Capture a point-in-time market snapshot

Collect and label the current public state that is available:

- outcome price or prices;
- best bid, best ask, midpoint, last trade, and spread;
- useful book depth near the market, not only the top quote;
- volume, recent volume, liquidity, and open interest when exposed;
- price history and recent public trades;
- resolution or dispute state;
- live score and game state for sports when applicable;
- related legs and markets that depend on the same event.

Timestamp every live observation. Assign the data-health grade defined in the
data reference. Cross-check important values across official surfaces when
possible. A last-trade price is not an executable quote. A WebSocket that still
answers heartbeats is not proof that its data is current.

Report empty, missing, stale, sentinel, delayed, or conflicting values. Do not
claim complete historical level-two data, private order flow, trader identity,
or intent.

### 3. Compile the settlement contract

Translate the full rules into:

- a plain-language YES test;
- a plain-language NO test;
- deadline and timezone;
- named resolution source and fallback hierarchy;
- early-resolution conditions;
- tie, cancellation, postponement, correction, or no-data handling;
- clarification and dispute state;
- ambiguous verbs, thresholds, entities, or evidence standards.

Compare the title with the controlling rules. Quote only the short fragments
needed to show a material condition, and link the full rules. Verify that the
named source exists and can publish the required fact. When settlement depends
on "credible reporting," state what must be reported, by when, and how
contradictory reports are treated.

Do not predict an oracle or dispute vote as fact. Separate the real-world event
from the question of how the contract can settle.

### 4. Route external research from the contract

Research the sources that can prove or disprove the settlement test. Prefer:

1. the named resolution source;
2. primary official sources;
3. reputable independent reporting;
4. specialist analysis;
5. Reddit, X, forums, and market comments as leads or sentiment only.

Use the market family to route the search:

- politics and geopolitics: official statements, legislation, court records,
  election authorities, and high-quality reporting;
- company and finance: filings, investor relations, earnings documents,
  statistical agencies, central banks, and underlying market data;
- sports: official tournament or league results, schedule, lineup, injuries,
  standings, and relevant weather;
- weather: the exact station, measure, observation window, timezone, and agency;
- technology and culture: official releases, repositories, organizers, and the
  named judging or ranking source.

Search for confirming and disconfirming evidence. For every material item,
record publication time, event time when different, retrieval time, source
class, which contract condition it bears on, and direction of impact. Group
syndicated copies and articles that repeat one original report into one evidence
family.

### 5. Use independent lanes for thorough research

When subagents are available, use them for a `thorough` run or when the user
asks for many web searches. Keep the lanes independent:

1. contract and precedent: rules, named sources, clarifications, prior contracts;
2. primary evidence: official and domain-specific current facts;
3. counter-evidence and public discussion: the strongest contrary case, Reddit,
   X, forums, and credible alternative explanations.

Give each lane the canonical URL, exact selected leg, UTC research start, any
user-supplied maximum evidence date, and the required source ledger. Run the
lanes in parallel when possible. The lead agent owns the official market
snapshot and final adversarial reconciliation.

When subagents are unavailable, run the same lanes sequentially. Never weaken
the source or timestamp contract because the host has fewer tools.

### 6. Use Weft only for a material structured-data gap

Ordinary public-web research does not require payment. When a material financial,
sports, news, or historical-data gap remains and a structured provider would
change the report, load the current `weft` skill.

Before declaring a structured-data gap, use free `weft_search` for every
applicable intent below. These prompts make useful catalog capabilities visible
without assuming that a remembered provider is still present:

- `Polymarket historical orderbook snapshots, trades, OHLCV, and cumulative volume`
  for historical mode, price-move reconstruction, and liquidity changes;
- `prediction-market holders, wallet positions, and public positioning` when
  the user asks about public flow or concentration;
- `X, Reddit, and structured news discovery` for wider reporting, rumor, and
  community-lead discovery;
- `SEC facts, filings, earnings history, transcripts, and analyst estimates`
  for company and earnings contracts;
- `official sports schedules, results, injuries, lineups, player form, and odds`
  for sports contracts when primary public coverage is incomplete;
- `event-specific current and historical weather` when weather can affect the
  settlement test or a sports event.

Do not hard-code provider names or prices. Reformulate weak searches and let the
live catalog own operation contracts, availability, and cost. A free search is
not permission to pay. Fetch only when an operation binds the exact market,
token, entity, event, date, measure, and output needed by the report.

In the report, list each searched capability class, why it applies, and the
strongest contract-complete operation found. Name the skipped capability classes
and explain why they cannot change this report. Record provider, operation,
observed price, and retrieval time as point-in-time catalog facts. If the run is
search-only, state that no paid operation was called and no funds were held.

Follow its free search, contract-fit, balance, cost-cap, attribution, receipt,
and no-paid-retry rules. Search the live catalog instead of naming a remembered
provider. Pay only for an operation whose declared inputs bind the required
entity, event, date, measure, and output. State the expected maximum before a
paid call and the actual paid plus held amount after it.

If Weft is unavailable or no contract-complete provider exists, continue with
public evidence and name the gap. Never treat a paid result as authority over
the market's named resolution source. Treat holder, wallet, social, and sentiment
data as public activity or research leads, never proof of motive, coordination,
or inside information.

### 7. Reconcile before writing

Perform an adversarial pass:

- confirm the URL, selected leg, and identifiers;
- check every material claim against its cited source;
- distinguish facts, source claims, and inferences;
- test the strongest YES and NO cases against the exact settlement test;
- identify duplicate evidence, stale reports, and unresolved contradictions;
- check whether a price move can be thin-book noise instead of new information;
- state when the evidence is insufficient.

For a current report: Set the evidence cutoff after the last accepted retrieval
or live observation. Then verify that every material retrieval and observation
time is less than or equal to the evidence cutoff. If a later item is accepted,
advance the cutoff before writing.

For Historical cutoff mode, keep three times separate:

- source-availability cutoff: the user's past `as of` time;
- retrieval time: when the current research run accessed the source;
- market observation time: when the quoted market state was actually observed.

Filter claims by when the evidence was publicly available, not by when it was
retrieved. Retrieval time can be later than a user-supplied historical cutoff.
Do not present a current market snapshot as historical market state. Use only
price history or archived observations with known observation times, and mark
historical bid, ask, spread, and depth unavailable when no suitable archive
exists.

Use the bundled report template. Keep the market-implied probability separate
from any independent estimate.

## Probability And Mispricing Requests

Provide an independent probability only when the user asks for one. Use a range,
not false precision. State the evidence cutoff, method, important assumptions,
and main sensitivity. Compare the range with the executable bid and ask, not
only the displayed probability.

Do not output BUY, SELL, position size, expected profit, or a claim that a gap is
actionable. Fees, depth, settlement risk, and evidence uncertainty can remove an
apparent difference. Do not describe any result as risk-free.

## Refresh Mode

When the user supplies an earlier brief, preserve its observation time and
compare only evidence available after that cutoff. Report:

- changed market state;
- new or corrected source evidence;
- rule, clarification, or resolution-state changes;
- which earlier conclusions remain supported, weakened, or invalidated.

Do not imply continuous monitoring. This skill owns no durable watchlist or
background process.

## Failure Rules

- Unresolved URL or identity mismatch: stop; do not substitute another market.
- Missing full rules: return a blocked report; do not infer them from the title.
- Stale or conflicting critical market data: lower the data-health grade and
  constrain the conclusion.
- Named source unavailable: explain the fallback rule and the unresolved risk.
- Access-controlled evidence: name the missing fact; do not invent it or evade
  access controls.
- Paid request timeout or ambiguous result: preserve the receipt and stop; do
  not repeat the paid request.
- Market already resolved: produce an audit or retrospective only; do not write
  as though it is still open.

## Safety And Integrity

- Never place an order or call a trading endpoint.
- Never request or handle wallet keys, payment headers, exchange credentials,
  cookies, or authorization tokens.
- Never identify public wallet activity as insider trading or proof of intent.
- Never convert market comments or social posts into verified facts.
- Never hide a source conflict to make the report decisive.
- Mark the brief as point-in-time research and not financial advice.
- State all source, data, geographic, and legal limitations that materially
  affect the requested use.
