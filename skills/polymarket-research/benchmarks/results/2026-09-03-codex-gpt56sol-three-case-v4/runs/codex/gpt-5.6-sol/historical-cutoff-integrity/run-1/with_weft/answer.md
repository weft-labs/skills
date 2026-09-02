## Offline brief

**Evidence cutoff:** 2026-05-10T12:00:00Z

The admissible record consists of:

- **E-A:** published before the cutoff. Its later retrieval does not change its historical public availability.
- **E-C-ORIGINAL:** published before the cutoff. The later correction cannot be applied retroactively.
- **H1:** an archived trade observed 30 minutes before the cutoff.

Excluded from the historical view:

- **E-B:** although its underlying event occurred before the cutoff, it was not published until 2026-05-11.
- **E-C-CORRECTION:** published after the cutoff.
- **C1:** a current quote observed months after the cutoff.

The dossier provides no substantive contents for the evidence, no numerical value for H1, and no archived bid, ask, spread, or order-book depth. Consequently, it cannot support a defensible probability estimate, assessment of execution conditions, or proposed trade. Current market data must not be substituted for the missing historical snapshot.

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