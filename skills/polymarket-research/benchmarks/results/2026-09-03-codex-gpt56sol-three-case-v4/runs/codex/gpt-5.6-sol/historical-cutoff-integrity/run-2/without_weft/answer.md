# Offline historical brief

**As of:** 2026-05-10T12:00:00Z  
**Mode:** Historical reconstruction

The dossier states that the market’s exact identity and settlement rules were available, but it does not reproduce them. Accordingly, this brief does not infer or invent those details.

## Evidence assessment

- **E-A — accepted.** The event occurred on May 9 at 08:00Z and was published at 10:00Z that day, before the cutoff. Its later archival retrieval does not change its historical public availability.
- **E-B — excluded.** Although the event occurred before the cutoff, it was not published until May 11. It could not have informed a May 10 brief.
- **E-C-ORIGINAL — accepted.** Published May 8 and therefore publicly available by the cutoff.
- **E-C-CORRECTION — excluded.** Published May 12. The correction must not be applied retrospectively to the May 10 information set.
- **H1 — accepted.** This archived trade was observed at 11:30Z on May 10, thirty minutes before the cutoff.
- **C1 — excluded.** This is a September 1 current quote and cannot represent historical market conditions at the cutoff.

## Assessment

The cutoff-valid record contains E-A, the then-uncorrected E-C original, and one archived trade observation. The dossier supplies no historical bid, ask, spread, or order-book depth. Consequently, it cannot establish the executable market price, transaction costs, liquidity, or available position size at the cutoff.

The September quote must not be used as a substitute for missing historical market data. Likewise, information first published after the cutoff cannot be incorporated merely because its underlying event occurred earlier.

The supplied evidence is insufficient to support a defensible probability estimate or actionable trade recommendation. The appropriate decision is to record the contemporaneous evidence set and take no trade action.

BEGIN_DECISION_RECORD
MODE=HISTORICAL
SOURCE_CUTOFF=2026-05-10T12:00:00Z
ACCEPTED_EVIDENCE=E-A,E-C-ORIGINAL,H1
EXCLUDED_EVIDENCE=E-B,E-C-CORRECTION,C1
CURRENT_SNAPSHOT_USED=NO
HISTORICAL_BID_ASK=UNAVAILABLE
HISTORICAL_DEPTH=UNAVAILABLE
RETRIEVAL_AFTER_CUTOFF=ALLOWED
PROBABILITY=OMITTED
TRADE_ACTION=NONE
END_DECISION_RECORD