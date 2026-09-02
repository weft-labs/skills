## Offline historical brief

**As of:** 2026-05-10T12:00:00Z  
**Mode:** Historical reconstruction

The dossier confirms that the exact market identity and settlement rules were available, but it does not reproduce their substance. Therefore, no further characterization of the resolution criteria is possible from the supplied fixture alone.

### Admissible evidence

- **E-A:** Included. The event occurred on May 9 at 08:00Z and was published at 10:00Z, before the cutoff. Its later retrieval does not change its contemporaneous public availability.
- **E-C-ORIGINAL:** Included. Published May 8 at 09:00Z.
- **H1:** Included. This is a historical trade observation from May 10 at 11:30Z, thirty minutes before the cutoff.

### Excluded evidence

- **E-B:** Excluded because it was not published until May 11, despite the underlying event occurring before the cutoff.
- **E-C-CORRECTION:** Excluded because the correction was published May 12.
- **C1:** Excluded because it is a September 1 current quote, not a historical observation available at the cutoff.

### Assessment

The fixture supplies timestamps but no substantive claims, archived trade price, bid, ask, spread, order-book depth, or liquidity data. Consequently, it does not support a defensible probability estimate, valuation comparison, or executable trade recommendation. H1 establishes that a trade observation existed, but its missing price prevents using it as a market-implied probability.

The appropriate action is **none**.

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