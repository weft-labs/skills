# SEO Report Contract

Use this structure. Remove sections that do not apply; do not fill them with
generic advice.

## 1. Executive Summary

State the requested outcome, what the evidence supports, and the three to five
highest-priority actions. State whether external evidence was bought and the
total `paid_usd + held_usd`.

## 2. Scope And Limits

Record:

- target, market, language, device, and date range;
- pages or templates inspected;
- first-party sources supplied by the user;
- external datasets bought through Weft;
- blocked checks, missing access, and sample limits.

## 3. Findings

Use only applicable groups:

- crawl, indexability, canonicals, redirects, and internal discovery;
- titles, descriptions, headings, intent, copy, and duplication;
- structured data and visible-content agreement;
- measured performance evidence;
- search demand, result pages, competitors, and backlinks;
- AI-search readiness;
- local search evidence.

Each finding uses this compact shape:

```text
Finding:
Class: observed fact | provider evidence | inference
Evidence:
Why it matters:
Severity: critical | high | medium | low
Confidence: high | medium | low
```

Severity describes consequence. Confidence describes evidence strength. Do not
combine them into a score.

## 4. Prioritized Actions

Use this table:

| Priority | Action | Evidence | Expected impact | Effort | Confidence | Completion test |
|---|---|---|---|---|---|---|

Keep the action concrete. “Improve SEO” is not an action. A useful completion
test is observable, such as a changed directive, a valid rendered field, a set
of linked pages, or a new measurement after a stated wait period.

Separate immediate fixes from experiments. For an experiment, state the target
page set, change, primary measurement, comparison period, and stop condition.

## 5. Unknowns And Next Evidence

List important unresolved questions. For each one, name the next free check or
the exact paid capability required. Do not name a provider unless it was found
in the current Weft search.

## 6. Evidence And Spend Ledger

| Claim or dataset | Source/provider | Operation | Query or URL | Scope and timestamp | Receipt state | Paid | Held |
|---|---|---|---|---|---|---:|---:|

For direct target inspection, use `direct observation` and `$0`. For user data,
use `user supplied` and describe its date range. For bought data, preserve the
provider and operation from live attribution plus safe receipt identifiers.
Use `not applicable` for the operation on free and user-supplied rows.

Close with:

```text
Total Weft cost: paid_usd + held_usd = $X
```

When no purchase was made, state `$0` and why.
