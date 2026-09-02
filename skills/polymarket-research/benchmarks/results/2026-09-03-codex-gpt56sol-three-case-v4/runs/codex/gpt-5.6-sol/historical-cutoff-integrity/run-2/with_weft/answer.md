# Offline historical brief

**As of:** 2026-05-10T12:00:00Z  
**Mode:** Historical reconstruction  
**Source:** `fixtures/historical-dossier.md` only

The dossier states that the market identity and settlement rules are available, but it does not reproduce their substance. It likewise supplies no underlying claims, trade price, or outcome evidence from which to assess the YES/NO cases.

## Cutoff assessment

- **E-A — Accepted.** Event and publication occurred before the cutoff. Later retrieval does not change what was publicly available at the time.
- **E-B — Excluded.** Although the event occurred before the cutoff, it was not published until 2026-05-11 and therefore was not publicly available by the cutoff.
- **E-C-ORIGINAL — Accepted.** Published before the cutoff.
- **E-C-CORRECTION — Excluded.** Published on 2026-05-12, after the cutoff. Using it would introduce hindsight.
- **H1 — Accepted.** This is a historical trade observation from 2026-05-10T11:30:00Z, thirty minutes before the cutoff. The dossier does not provide its price.
- **C1 — Excluded.** This is a current quote observed in September 2026 and cannot represent the historical market state.

## Market assessment

No defensible probability estimate can be produced from the supplied information. The dossier provides neither the content of the accepted evidence nor the observed H1 trade price. It also supplies no historical bid, ask, spread, or depth, so execution quality and actionable mispricing cannot be evaluated.

**Decision:** No trade proposed.

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