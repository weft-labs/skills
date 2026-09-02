## Offline brief

The original market (`fed-cut-before-december-2026`) cannot be reliably identified from the available offline data.

The canonical lookup returned no event. Search produced `fed-rate-cut-by-december-2026`, but its predicate differs from the original, so it cannot be treated as the same market without confirmation.

Unavailable information includes the original market’s:

- Full resolution rules
- Market, condition, and question IDs
- Outcome token IDs
- Current market snapshot

Because identity and rules remain unresolved, no probability assessment, trading proposal, or paid action is appropriate.

BEGIN_DECISION_RECORD
MODE=BLOCKED
IDENTITY=UNRESOLVED
REPLACEMENT=UNCONFIRMED
REPORT=BLOCKED
RULES=UNAVAILABLE
MARKET_SNAPSHOT=NOT_ATTEMPTED
PROBABILITY=OMITTED
PAID_ACTION=NONE
TRADE_ACTION=NONE
END_DECISION_RECORD