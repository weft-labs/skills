# Polymarket Research Report Template

Use this structure for the final answer. Omit only a clearly marked optional
section. Keep prose concise and put the most decision-relevant contract risk
before narrative background.

# [Exact selected market question] — Polymarket research brief

- **Canonical market:** [linked URL]
- **Selected outcome or leg:** [label]
- **Market observed:** [UTC timestamp, or historical state unavailable]
- **Evidence cutoff:** [current-run cutoff, or user-supplied historical source-availability cutoff]
- **Research retrieval completed:** [UTC timestamp]
- **Research depth:** [quick or thorough; number of independent lanes]
- **Data-health grade:** [A–D and one-line reason]
- **Status:** [open, closed, proposed, disputed, resolved, or unknown]

## Executive summary

- **What the contract actually asks:** [one sentence]
- **What the market currently says:** [executable bid/ask or outcome range with timestamp]
- **What the outside evidence says:** [one sentence, with uncertainty]
- **Main risk:** [resolution, evidence, liquidity, timing, or data-health risk]
- **Bottom line:** [research conclusion, not a trade instruction]

## Settlement contract

| Element | Exact contract |
|---|---|
| YES test | [plain-language predicate] |
| NO test | [plain-language predicate] |
| Cutoff and timezone | [value] |
| Primary source | [linked source] |
| Fallback hierarchy | [ordered list or none stated] |
| Early resolution | [rule or none stated] |
| Cancellation, tie, or no-data rule | [rule] |
| Ambiguity and title conflict | [material wording, or none found] |
| Clarification or dispute state | [state and evidence] |

Quote only short controlling fragments. Link the complete rules.

## Current market state

| Outcome | Best bid | Best ask | Midpoint | Last trade | Depth basis |
|---|---:|---:|---:|---:|---|
| [outcome] | [value/time] | [value/time] | [value/time] | [value/time] | [size or price band/time] |

Add volume, recent volume, liquidity, open interest, and material price changes
below the table. Label unavailable fields. Explain stale, empty, sentinel, or
conflicting values. Do not infer intent from public wallet activity.

## Evidence ledger

| Evidence | Source class | Publication / event time | Contract effect | Confidence |
|---|---|---|---|---|
| [fact or attributed claim with link] | [class] | [times] | [supports YES, supports NO, neutral, or changes resolution risk] | [high, medium, low] |

Group copied or syndicated reports under their original evidence family.

## Structured-data routing

Complete this section after the required free Weft searches. If Weft is
unavailable, state that fact and preserve the material data gaps.

| Capability class | Searched or skipped | Why it applies or cannot change the report | Provider and operation | Observed price and retrieval time | Contract-fit result or remaining gap |
|---|---|---|---|---|---|
| [capability] | [searched or skipped] | [report-specific reason] | [strongest complete operation, none found, or not applicable] | [point-in-time catalog facts or not applicable] | [bound identifiers, dates, measures, output, and limits] |

Do not hard-code providers or prices. Treat the live operation contract and
later payment challenge as authoritative. For a search-only run, state:
`No paid operation was called and no funds were held.` If a paid fetch occurs,
record its attribution, receipt, and actual `paid_usd + held_usd` instead.

## YES case

State the strongest evidence-led path to YES. Name assumptions and the evidence
that would confirm it. Do not make the case stronger than its sources.

## NO case

State the strongest evidence-led path to NO, including failure to satisfy the
exact source, definition, or deadline. Include the best contrary interpretation.

## Related contracts

Optional. Show only markets that depend on the same fact, actor, source, or
deadline. Compare exact predicates before prices. Label each relationship
`equivalent`, `related but different`, or `unsafe to compare`.

## Independent probability range

Optional and only when requested.

- **Range:** [x–y%]
- **Market comparison:** [range versus executable bid/ask]
- **Method and prior:** [short explanation]
- **Main sensitivities:** [what moves the range]
- **Settlement-risk adjustment:** [separate from event probability]

This range is a point-in-time estimate, not financial advice or an execution
instruction.

## Unknowns and invalidation conditions

- [missing decisive fact]
- [source conflict]
- [event that would invalidate the YES case]
- [event that would invalidate the NO case]

## Next catalysts

| Catalyst | Expected time | Source to watch | Why it matters |
|---|---|---|---|
| [event] | [timestamp or window] | [linked primary source] | [contract or evidence effect] |

## Sources and limitations

- List the primary market, rule, resolver, and external source links.
- State the market-data observation times and any paid provider attribution.
- State actual Weft `paid_usd + held_usd` when used. For a search-only run, say
  `No paid operation was called and no funds were held.`
- State missing coverage, access controls, geographic or legal limits, source
  drift, and other material uncertainty.
- End with: `Point-in-time research; not financial advice. No trade was placed.`
