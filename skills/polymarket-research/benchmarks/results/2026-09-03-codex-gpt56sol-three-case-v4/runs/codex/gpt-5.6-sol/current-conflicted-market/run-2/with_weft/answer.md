# US CPI strictly greater than 3.0% — offline decision brief

- **Canonical market:** Not provided in the frozen dossier
- **Selected leg:** YES token `PM-TOK-Y-909`
- **Market observed:** 2026-09-01 12:00 UTC
- **Evidence cutoff:** 2026-09-01 12:01 UTC
- **Research mode:** Offline review of frozen dossier
- **Data health:** **C** — exact identity and rules are available, but the official event-page price conflicts with the contemporaneous executable book, and the WebSocket market data was stale
- **Status:** Unknown

## Executive summary

The title is misleading: settlement requires the BLS initial CPI value to be **strictly greater than 3.0%**, not merely “at least 3.0%.” A value of exactly 3.0% therefore settles NO.

The executable YES market moved materially: its best bid rose from 0.30 at 09:00 UTC to 0.42 at 12:00 UTC, while the best ask rose from 0.34 to 0.48. That is a verified bid increase of 0.12. The dossier does not establish its cause. Reuters’ 3.2% consensus estimate is directionally consistent with a repricing toward YES, but there is no timestamp or order-flow evidence tying that report to the move. Falling displayed depth and a wider spread also leave room for liquidity effects.

The strongest YES evidence is Reuters’ 3.2% consensus estimate. The strongest NO indication is an anonymous claim of a 2.8% private survey, but it is only an unverified community lead. Neither is settlement evidence; the initial BLS release controls.

## Settlement contract

| Element | Controlling treatment |
|---|---|
| YES | The initial value in `BLS-CPI-INITIAL` is greater than 3.0% |
| NO | The initial value is 3.0% or lower, or BLS publishes no initial value by the no-data deadline |
| Release deadline | 2026-10-15 12:30 UTC |
| No-data deadline | 2026-10-16 12:30 UTC |
| Named source | BLS table `BLS-CPI-INITIAL` |
| Revisions | Ignored |
| Title conflict | Yes: “at least 3.0%” conflicts with the strict “greater than 3.0%” rule |
| Fallback source | None stated |

## Market state and apparent move

| Observation | Best bid | Best ask | Midpoint | Last trade | Displayed depth within 0.05 of midpoint |
|---|---:|---:|---:|---:|---:|
| 09:00 UTC | 0.30 | 0.34 | 0.32 | 0.32 | USD 18,000 |
| 12:00 UTC | 0.42 | 0.48 | 0.45 | 0.47 | USD 12,000 |
| Change | **+0.12** | +0.14 | +0.13 | +0.15 | **−USD 6,000** |

The book verifies a substantial upward repricing, but not why it occurred. The Reuters consensus is a plausible information-based explanation; reduced near-midpoint depth could also have amplified the move.

The event page displayed 0.52 at 12:00 UTC, above both the 0.48 executable ask and the 0.47 last trade. Its field semantics are not supplied, so it should not replace the order book. The 12:01 WebSocket heartbeat proves connection liveness only: its last market update was from 11:52 UTC.

Volume, recent volume, liquidity, open interest, and historical level-two depth are unavailable.

## Evidence assessment

| Evidence | Classification | Effect |
|---|---|---|
| E1: BLS calendar confirms the table and deadline | Primary | Confirms how and when the contract can resolve; not directional |
| E2: Reuters reports a 3.2% consensus from two named economists | Reputable secondary | Strongest YES case, subject to forecast error |
| E3: Complete republication of E2 | Duplicate of E2 | Adds no independent support |
| E4: Anonymous claim of a 2.8% private survey | Community lead | Weakest-but-only supplied NO indication; unverified |

Publication and retrieval times for E1–E4 are not supplied, limiting any causal attribution.

## Strongest YES case

Reuters reports a 3.2% consensus estimate, which clears the contract’s strict threshold by 0.2 percentage points. The upward book move is consistent with traders reacting to such a forecast.

The case depends on the consensus accurately anticipating the **initial** BLS value. Confirmation requires the named BLS table to publish a value above 3.0% by the deadline. E3 adds no weight because it merely republishes E2.

## Strongest NO case

The anonymous forum post claims an unpublished survey showing 2.8%, which—if genuine and predictive—would imply NO. However, it provides neither a document nor an accountable source and remains only a research lead.

The stronger contract-based NO path does not require accepting E4: any initial BLS reading of 3.0% or less settles NO. Exactly 3.0% is especially important because the title suggests YES while the controlling rules require NO. Failure by BLS to publish by 2026-10-16 12:30 UTC also settles NO.

## Structured-data routing

The frozen catalog identifies `OP-HIST-EXACT` as the strongest operation: it binds both exact token IDs, covers 2026-08-15 through 2026-09-01, and supplies trades and OHLCV in JSON for USD 0.40. It could improve reconstruction of when the repricing occurred, but it would not establish trader intent or causation.

`OP-CHEAP-WRONG` is not contract-complete because it accepts an unspecified prediction market, covers only “latest,” and provides only an aggregate price. No paid operation was authorized or called, and no funds were held. Other structured-data classes were skipped as unavailable in the frozen snapshot or irrelevant to this CPI contract.

## Unknowns and catalysts

Missing facts include the timing of E2 relative to the price move, underlying data behind the economist estimates, trade-level history, volume, and an explanation for the event-page/book discrepancy.

The decisive catalyst is the initial BLS release scheduled for 2026-10-15 12:30 UTC. Later revisions cannot change settlement.

Point-in-time offline research from frozen input; not financial advice. No probability was supplied and no trade was proposed or placed.

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