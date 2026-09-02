# Polymarket Data Reference

Read this file before collecting market data. It defines the public surfaces,
identifier boundaries, labels, and failure checks. Current official documentation
owns endpoint behavior when it differs from this workflow reference.

## Official Surfaces

| Need | Surface | Official reference |
|---|---|---|
| Event, market, tags, search, and sports metadata | Gamma API | <https://docs.polymarket.com/market-data/overview> |
| Canonical event from a URL slug | Gamma `GET /events/slug/{slug}` | <https://docs.polymarket.com/api-reference/events/get-event-by-slug> |
| Current prices, books, midpoint, spread, and price history | CLOB | <https://docs.polymarket.com/concepts/prices-orderbook> |
| Public market updates | CLOB market WebSocket | <https://docs.polymarket.com/api-reference/wss/market> |
| Positions, activity, open interest, holders, and trades | Data API | <https://docs.polymarket.com/market-data/overview> |
| Public comments | Gamma comments | <https://docs.polymarket.com/api-reference/comments/list-comments> |
| Live score, period, elapsed time, and game state | Sports WebSocket | <https://docs.polymarket.com/api-reference/wss/sports> |
| Resolution and disputes | UMA-backed resolution flow | <https://docs.polymarket.com/concepts/resolution> |
| Current request limits | Rate limits | <https://docs.polymarket.com/api-reference/rate-limits> |

Public market data does not require a Polymarket API key or wallet. Trading and
authenticated user channels are outside this workflow.

## Canonical Identity

A Polymarket event can contain several markets or outcome legs. Keep these
values separate even when an API or library uses similar names:

| Identifier | Meaning |
|---|---|
| event ID / slug | page-level event and the slug in the event URL |
| market ID / slug | one market or selected outcome under the event |
| condition ID | on-chain binary or conditional market identity |
| question ID | oracle or question identity; not a token ID |
| token / asset ID | one tradable outcome token used for CLOB book requests |
| outcome index | position of one label inside the market's outcome list |

Resolve the event first. Then map every market leg and outcome token from the
same response family. Do not send a condition ID where a CLOB token ID is
required. An empty response after an identifier swap is an error signal, not
proof that the market has no data.

Some Gamma fields can arrive as JSON-encoded strings rather than parsed arrays,
including outcomes, outcome prices, and token IDs. Parse defensively and verify
equal lengths before joining by index.

## Market-State Labels

Use exact labels. Do not call every price "the probability."

| Field | Meaning and use |
|---|---|
| best bid | highest current visible buy order for that outcome |
| best ask | lowest current visible sell order for that outcome |
| midpoint | arithmetic center of current bid and ask when both exist |
| last trade | most recent matched price; it can be stale or non-executable |
| displayed or outcome price | Polymarket-provided display value; identify its source field |
| spread | best ask minus best bid for the same outcome |
| depth | available size at price levels; show the requested band or size basis |
| liquidity | use the API's labeled measure; do not silently equate it with depth |
| volume | cumulative or windowed traded amount as labeled |
| open interest | report only when the surface exposes a current value |

Prices between 0 and 1 can be read as market-implied probabilities, subject to
spread, fees, liquidity, and contract risk. They are not independent forecasts.

For a tradeability comparison, use the executable ask for buying an outcome and
the executable bid for selling it. Do not calculate an edge from midpoint or
last trade alone.

## Settlement Contract

The full rules control settlement. The title is a summary. Extract:

- the exact subject and predicate;
- outcome condition and threshold;
- start, cutoff, and timezone;
- named primary source and any fallback order;
- early YES or early NO conditions;
- cancellation, postponement, tie, correction, and no-data rules;
- clarification and dispute state.

The structured `resolutionSource` field can be absent or less complete than the
rules prose. Preserve both, but treat the full live rules as the contract and
flag disagreement.

For automated crypto, sports, or weather markets, use the exact named data
series, station, competition, observation window, and tie rule. A nearby source
or a front-end display is not equivalent.

## Data-Health Grade

Assign one grade to the point-in-time snapshot:

| Grade | Contract |
|---|---|
| A | exact identity; full rules; current official book; material values agree; named source reachable |
| B | exact identity and current core values; one non-critical field is missing or cannot be cross-checked |
| C | material value is stale, delayed, empty, or conflicting; conclusions must be constrained |
| D | identity, rules, or critical market state cannot be established; stop the decision brief |

State the evidence for the grade. Do not use an A grade when observation times
are missing.

## Known Failure Modes

- WebSocket liveness is not data liveness. Heartbeats can continue while market
  updates are delayed or absent. Cross-check a current REST snapshot.
- Empty and zero are different. A true zero, an omitted field, a never-traded
  sentinel, an invalid identifier, and a retention gap must remain distinct.
- Gamma, CLOB, and Data API values can update on different cadences. Compare
  observation times before declaring a conflict.
- A recent large trade can move a thin book without new external information.
  Public flow does not reveal motive, hedges, or wallet ownership.
- Comments and social posts are research leads. They are not settlement facts.
- Search results and Polymarket's AI market context can be stale or derivative.
  They never replace the named source or full rules.
- Public APIs do not provide dependable complete historical level-two order books.
  State the archive or vendor provenance when historical depth is used.
- Sports markets can clear resting orders at the official game start. Observe
  current lifecycle state before comparing pre-game and live books.
- A resolved outcome should be checked against resolution state or winning-token
  evidence, not one convenient structured boolean alone.

## External Evidence Ledger

Store these fields in working notes for every material source:

`claim | contract condition | source class | source URL | publication time | event time | retrieval time UTC | direction | confidence | contradiction family`

Source classes:

- `primary`: named resolver, authority, filing, official release, organizer;
- `reputable-secondary`: original reporting with accountable sourcing;
- `specialist`: domain analysis with visible method or data;
- `community-lead`: Reddit, X, forums, or comments that require verification;
- `inference`: the agent's synthesis, never presented as a source fact.
