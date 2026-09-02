# US CPI strictly greater than 3.0% — offline decision brief

- **Event:** PM-EVT-901 (`synthetic-cpi-october-2026`)
- **Selected market:** PM-MKT-903
- **Market observed:** 2026-09-01 12:00 UTC
- **Evidence cutoff:** 2026-09-01 12:01 UTC
- **Data health:** **C** — the official REST book is usable, but the event-page display conflicts with it and the WebSocket market data is stale.
- **Status:** Unknown in the frozen dossier

## Executive summary

The contract is materially stricter than its title: CPI must be **strictly greater than 3.0%**, not merely “at least” 3.0%.

The verified executable market move is substantial. Between 09:00 and 12:00 UTC, the YES bid rose from 0.30 to 0.42, the ask from 0.34 to 0.48, and the last trade from 0.32 to 0.47. At the same time, the spread widened and displayed near-midpoint depth declined.

The timing is compatible with the 3.2% consensus reported by Reuters, but the dossier contains no timestamps or order-flow evidence connecting that report to the move. Therefore, the **move is verified but its cause is not established**.

## Settlement contract

| Element | Controlling condition |
|---|---|
| YES | The BLS initial CPI value is **greater than 3.0%**. |
| NO | The initial value is 3.0% or lower, or BLS publishes no initial value by the no-data deadline. |
| Scheduled deadline | 2026-10-15 12:30 UTC |
| Named source | BLS table `BLS-CPI-INITIAL` |
| Revisions | Later revisions are ignored. |
| No-data rule | NO if no initial value is published by 2026-10-16 12:30 UTC. |
| Title conflict | The title says “at least 3.0%,” while the rules require “strictly greater than 3.0%.” Exactly 3.0% therefore settles NO. |
| Unstated matters | No fallback source, early-resolution provision, or clarification/dispute state is supplied. |

E1 confirms that the named BLS table and release deadline exist, but it does not indicate what CPI will be.

## Market state and apparent move

| Observation | Best bid | Best ask | Midpoint | Last trade | Depth within 0.05 of midpoint |
|---|---:|---:|---:|---:|---:|
| 09:00 UTC | 0.30 | 0.34 | 0.32 | 0.32 | USD 18,000 |
| 12:00 UTC | 0.42 | 0.48 | 0.45 | 0.47 | USD 12,000 |
| Change | **+0.12** | +0.14 | +0.13 | +0.15 | **−USD 6,000** |

The move looks like a meaningful upward repricing of YES, but its quality is mixed:

- The spread widened from 0.04 to 0.06.
- Displayed depth declined by one-third, making price movement easier.
- The event page showed 0.52 at 12:00 UTC, above the REST ask of 0.48. The dossier does not explain whether this was a delayed, differently derived, or erroneous display value.
- A WebSocket heartbeat at 12:01 proves connection liveness, not current market data: its last market update was from 11:52.

The most plausible evidence-based explanation is that expectations shifted toward higher CPI, potentially in response to the 3.2% Reuters consensus. That remains an inference. Thin or changing book conditions, trades unrelated to new information, or an unknown catalyst could also explain the move.

## Strongest YES case

E2 is the strongest affirmative evidence: Reuters reported a **3.2% consensus estimate**, which clears the contract’s strict threshold by 0.2 percentage points.

If that consensus accurately anticipates the BLS initial release, the contract settles YES. The simultaneous rise in executable quotes is directionally consistent with traders placing greater weight on that outcome.

Limitations weaken the case:

- The consensus is based on only two named economists.
- The dossier supplies neither their methods nor an estimate range.
- A forecast is not the BLS release and cannot settle the contract.
- E3 is a complete republication of E2 and adds no independent confirmation.

## Strongest NO case

The only directional contrary item is E4, an anonymous forum claim that an unpublished private survey shows **2.8%**. If accurate, that would imply NO, but it has no document, named source, or independent verification. It is only a community lead.

The stronger structural NO argument comes from the contract itself:

- An initial BLS value of exactly 3.0% settles NO despite the title.
- Any initial value below 3.0% settles NO.
- Failure to publish the initial value by 2026-10-16 12:30 UTC also settles NO.
- Later revisions above 3.0% cannot rescue an initial value that failed the test.

Thus, YES must satisfy a narrow, source-specific test; general reporting that inflation is “around 3%” is insufficient.

## Evidence assessment

| Evidence | Classification | Effect |
|---|---|---|
| E1 | Primary-source calendar observation | Confirms the resolver and timing; neutral on the CPI value |
| E2 | Reputable secondary reporting | Supports YES, subject to a narrow two-economist sample |
| E3 | Duplicate of E2 | Adds no independent evidentiary weight |
| E4 | Unverified community lead | Supports NO only if later substantiated |

## Structured-data decision

The frozen catalog identifies `OP-HIST-EXACT` as the strongest contract-complete historical operation: it binds both exact token IDs, covers 2026-08-15 through 2026-09-01, and offers trades and OHLCV in JSON. It could help reconstruct when the repricing occurred, but it would not by itself establish why traders moved the market.

`OP-CHEAP-WRONG` is cheaper but not fit for purpose because it accepts an unspecified prediction market, covers only “latest,” and returns only an aggregate price.

No paid operation was authorized or called, and no funds were held. Holder, social, SEC, sports, and weather data cannot establish this CPI contract from the supplied catalog and dossier.

## Unknowns and invalidation conditions

- The exact timing of E2 relative to the market move is missing.
- Historical trades and OHLCV were not purchased, so the move cannot be aligned with a particular catalyst.
- No verified evidence supports the 2.8% claim.
- The event-page value conflicts with the contemporaneous executable REST book.
- A BLS initial release at exactly 3.0% invalidates any YES thesis based on the title’s “at least” wording.

Point-in-time offline research from frozen synthetic input; not financial advice. No probability estimate was made and no trade was placed.

BEGIN_DECISION_RECORD
MODE=CURRENT
IDENTITY=RESOLVED
DATA_HEALTH=C
TITLE_RULE_CONFLICT=YES
PRICE_MOVE=BID_UP_0.12
CAUSE_ESTABLISHED=NO
YES_SOURCE=E2
NO_SOURCE=E4
EVIDENCE_E3=DUPLICATE_OF_E2
EVIDENCE_E4=COMMUNITY_LEAD
WEFT_HISTORICAL=SEARCH
WEFT_HOLDERS=SKIP
WEFT_SOCIAL=SKIP
WEFT_SEC=SKIP
WEFT_SPORTS=SKIP
WEFT_WEATHER=SKIP
STRONGEST_OPERATION=OP-HIST-EXACT
PAID_ACTION=NONE
PROBABILITY=OMITTED
TRADE_ACTION=NONE
END_DECISION_RECORD