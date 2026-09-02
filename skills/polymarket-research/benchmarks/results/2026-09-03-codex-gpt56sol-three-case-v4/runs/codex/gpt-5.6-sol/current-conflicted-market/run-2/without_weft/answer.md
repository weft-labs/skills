# Offline decision brief

The official REST order book shows a verified upward move on September 1: the best bid rose from 0.30 to 0.42, the best ask from 0.34 to 0.48, and the last trade from 0.32 to 0.47. Liquidity conditions worsened during the move: the spread widened from 0.04 to 0.06, while displayed near-midpoint depth fell from USD 18,000 to USD 12,000.

The event page’s 0.52 is not enough to establish a further move because the dossier does not define what that number represents or make it directly comparable with the REST quotes. The WebSocket confirms connectivity, but its market data was already eight minutes old at noon. The REST observations therefore provide the clearest price evidence.

No cause is established. Reuters’ 3.2% consensus could explain increased YES demand, but the dossier supplies no publication timestamp or trading evidence connecting that report to the move. E3 merely republishes Reuters and is not independent confirmation. E4 points the other way, but it is anonymous and unsupported.

A material contract issue also matters: the title says “at least 3.0%,” whereas the controlling rules require a value strictly greater than 3.0%. An initial reading of exactly 3.0% therefore settles NO. Later revisions do not count, and failure to publish an initial value by the fallback deadline also settles NO.

Strongest YES case: E2 reports a 3.2% consensus estimate, above the rule’s strict 3.0% threshold. Although based on only two named economists, it is the strongest outcome-relevant evidence in the dossier and is directionally consistent with the observed rise.

Strongest NO case: E4 claims an unpublished private survey at 2.8%, below the threshold. This is only a community lead—not verified evidence—because it supplies neither a document nor a named source. The NO side also benefits from the exact-3.0% title/rule discrepancy and the no-publication fallback, but the dossier provides no evidence that either circumstance is likely.

The exact-token historical operation is the only catalog option appropriately scoped to this market and date range. It costs USD 0.40, however, so it cannot be run without authorization. The cheaper operation has the wrong selector, range, and data granularity.

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