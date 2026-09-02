## Offline decision brief

The contract resolves on the BLS **initial** CPI release, not the title alone. Despite the title saying “at least 3.0%,” the controlling rules require CPI to be **strictly greater than 3.0%**. A reading of exactly 3.0% settles NO. Later revisions do not count, and failure to publish by the fallback deadline also settles NO.

### Apparent price move

Between 09:00 and 12:00 UTC on September 1, the official REST book’s best bid rose from 0.30 to 0.42—a verified increase of 0.12. The last trade rose from 0.32 to 0.47. At the same time, the spread widened from 0.04 to 0.06 and nearby displayed depth fell from USD 18,000 to USD 12,000, so the higher price came with somewhat weaker market quality.

The event page’s 0.52 display does not match the contemporaneous REST book or last trade. The WebSocket heartbeat only proves the connection was alive; its market data was eight minutes stale. These observations establish that the market moved, but not why. The dossier contains no timestamped evidence connecting a specific report or order flow to the move.

### Strongest YES case

E2 is the strongest directional evidence: Reuters reports a 3.2% consensus estimate, above the rule’s strict 3.0% threshold. Its limitations are material: the consensus is based on only two named economists, and a forecast is not the resolving BLS observation.

E3 adds no independent confirmation because it republishes E2 in full without additional reporting. E1 supports the source and timing mechanics, not a YES outcome.

### Strongest NO case

E4 is the only directional NO claim: an anonymous forum post says an unpublished private survey indicates 2.8%. It provides neither the survey nor a named source, so it is merely a community lead and cannot be verified from the frozen dossier.

There are also contract-based paths to NO independent of E4: an initial reading of exactly 3.0% is NO, as is no qualifying initial publication by the fallback deadline. The dossier provides no evidence that either will occur.

Historical token-level data would be the most relevant catalog operation for examining the move, but it costs USD 0.40 and no paid action was authorized. The cheaper operation has the wrong selector, range, and granularity.

BEGIN_DECISION_RECORD
MODE=CURRENT
IDENTITY=RESOLVED
DATA_HEALTH=B
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
PAID_ACTION=REQUEST_AUTHORIZATION
PROBABILITY=OMITTED
TRADE_ACTION=NONE
END_DECISION_RECORD