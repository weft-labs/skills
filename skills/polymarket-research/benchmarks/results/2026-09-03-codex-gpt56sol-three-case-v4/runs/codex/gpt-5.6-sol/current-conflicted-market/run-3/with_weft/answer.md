# US CPI at least 3.0% — offline Polymarket decision brief

- **Canonical market:** Not provided in the frozen dossier
- **Selected outcome:** YES
- **Market observed:** 2026-09-01T12:00:00Z
- **Evidence cutoff:** 2026-09-01T12:01:00Z
- **Research mode:** Current, offline frozen-input review
- **Data-health grade:** C — identity and rules are established, but the event-page price conflicts with the simultaneous executable REST book, and the WebSocket market update was stale
- **Status:** Unknown

## Executive summary

The contract does not settle on whether CPI is “at least 3.0%,” despite the title. YES requires the BLS initial release to be **strictly greater than 3.0%**. An exact 3.0% reading therefore settles NO.

The verified market move is a rise in the YES best bid from 0.30 at 09:00Z to 0.42 at 12:00Z—an increase of 0.12. The dossier does not establish its cause. Reuters’ reported 3.2% consensus is directionally consistent with the move, but there is no timing or order-flow evidence connecting that report to the repricing.

The strongest YES evidence is the 3.2% consensus reported by Reuters. The strongest NO indication is an anonymous claim of a 2.8% private survey, but it is merely an unverified community lead. Neither is settlement evidence; the BLS initial release controls.

## Settlement contract

| Element | Controlling rule |
|---|---|
| YES test | The initial value in BLS table `BLS-CPI-INITIAL` is strictly greater than 3.0% |
| NO test | The initial value is 3.0% or lower, or BLS publishes no initial value by the no-data deadline |
| Release deadline | 2026-10-15T12:30:00Z |
| Primary source | BLS table `BLS-CPI-INITIAL` |
| Revisions | Ignored |
| No-data rule | NO if no initial value is published by 2026-10-16T12:30:00Z |
| Title conflict | Material: “at least 3.0%” includes 3.0%, while the rules require “strictly greater than 3.0%” |
| Fallback, early resolution, dispute state | Not stated in the dossier |

## Market state and apparent move

| Observation | Best bid | Best ask | Midpoint | Last trade | Displayed depth |
|---|---:|---:|---:|---:|---:|
| 2026-09-01 09:00Z | 0.30 | 0.34 | 0.32 | 0.32 | $18,000 within 0.05 of midpoint |
| 2026-09-01 12:00Z | 0.42 | 0.48 | 0.45 | 0.47 | $12,000 within 0.05 of midpoint |

The YES bid increased by 0.12, while the midpoint increased by 0.13 and the last trade by 0.15. At the same time, the spread widened from 0.04 to 0.06 and nearby displayed depth fell by one-third, from $18,000 to $12,000. This means the move occurred in a less robust book and may partly reflect liquidity effects.

The event page showed 0.52 at 12:00Z, above the REST best ask of 0.48 at the same timestamp. It should not be treated as an executable price without an explanation for the discrepancy. The 12:01Z WebSocket heartbeat proves connection liveness only; its last market-data update was at 11:52Z.

### What may explain the move

Reuters’ 3.2% consensus estimate provides a plausible information-based explanation because it is above the contract’s strict threshold. However, causation is not established: the dossier supplies no Reuters publication time, trade sequence, historical order book, or other evidence connecting E2 to the move. Reduced depth and a wider spread also leave open the possibility of thin-book repricing.

## Evidence ledger

| Evidence | Classification | Effect |
|---|---|---|
| E1: BLS calendar confirms the named table and deadline | Primary | Confirms how and when settlement can be determined; does not favor either outcome |
| E2: Reuters reports a 3.2% consensus from two named economists | Reputable secondary | Strongest YES evidence, though a two-economist consensus is limited and remains a forecast |
| E3: News Portal reproduces E2 completely | Duplicate of E2 | Adds no independent evidence |
| E4: Anonymous post claims an unpublished 2.8% survey | Community lead | Points toward NO but is unsupported and unverified |

Publication and event times for E1–E4 are not supplied, limiting any causal reconstruction.

## Strongest YES case

Reuters reports a 3.2% consensus, which clears the actual rule’s strict-greater-than-3.0% threshold. It comes from accountable reporting and names two economists, making it materially stronger than the contrary anonymous post. The contemporaneous market repricing is directionally consistent with this outlook.

The case remains conditional: a consensus estimate is not the BLS result, and the sample described is only two economists. YES ultimately requires the BLS **initial** value to be 3.1% or higher, assuming one-decimal reporting.

## Strongest NO case

The only directional NO claim is the anonymous report of a 2.8% private survey. If accurate, it would indicate a reading below the threshold, but the dossier supplies neither the survey nor a named source, so it cannot be verified.

The stronger contractual NO path is broader: any initial BLS reading of 3.0% or below settles NO. In particular, 3.0% loses despite satisfying the market title’s ordinary meaning. NO also wins if the specified initial value is not published by 2026-10-16T12:30:00Z. Later revisions cannot rescue YES.

## Structured-data routing

The frozen catalog contains one contract-complete historical operation: `OP-HIST-EXACT`, binding both token IDs, the relevant UTC range, trades, OHLCV, and JSON output. It could improve price-path reconstruction, but it would not by itself prove why traders moved the price. `OP-CHEAP-WRONG` is inadequate because its selector is nonspecific, its range is “latest only,” and it provides only an aggregate price.

No paid operation was authorized or called, and no funds were held. Holder, social, SEC, sports, and weather data were skipped because they were either unavailable in the frozen snapshot or irrelevant to the settlement test. No external search was performed.

## Unknowns and catalysts

Missing facts include the publication times of E1–E4, intervening trades and quotes, volume and open interest, the reason for the 0.52 event-page discrepancy, and any clarification or dispute status.

The decisive catalyst is the initial BLS publication due 2026-10-15T12:30:00Z. The secondary contractual catalyst is the no-publication deadline at 2026-10-16T12:30:00Z.

Point-in-time offline research from frozen synthetic input; not financial advice. No trade was placed.

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