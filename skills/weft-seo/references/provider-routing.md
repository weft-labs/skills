# Provider Routing

Use this reference after target inspection identifies an external evidence gap.
The current `weft` skill owns tool syntax and payment safety.

## Convert Gaps Into Capabilities

| Decision | Useful capability query | Required contract inputs | Minimum useful output |
|---|---|---|---|
| Which pages compete for a query? | current search results for query, market, language, and device | query, country or location, language; device when material | ranked URLs, titles or snippets, query, location, timestamp |
| Is a topic worth a content test? | keyword demand and trend for topic in market and date range | keyword or topic, geography, language, date range | metric definition, values, unit, geography, period |
| Which sites link to a page or domain? | backlinks for exact URL or domain with current scope | target, target type, freshness or limit | source URL, target URL, link attributes, observed date or provider timestamp |
| Who competes locally? | local business or map search for category near location | category or query, precise location, radius or result limit | business identity, address, category, position or order, rating scope, timestamp |
| What changed on competing pages? | current web search and page extraction for named URLs | query or URL, freshness, extraction fields | source URLs, extracted facts, timestamp |

These are contract shapes, not provider recommendations. Search the live Weft
index for the capability each time.

## Selection Checklist

Before payment, answer all of these questions from the current search result or
its `contract_url`:

1. Can every material user input map to a declared typed input?
2. Does the request recipe bind each input to path, query, body, or header?
3. Does the output contain the evidence needed for the decision?
4. Are geography, language, device, date range, freshness, and sample size clear?
5. Is the operation synchronous, or does its full contract define safe free
   polling after one paid submission?
6. Is the live price within wallet policy and the tight per-call cap?
7. Are attribution fields present and copied exactly?

Reject the operation when any required answer is no. Do not infer an input from
an operation description or append an undeclared query field.

## Purchase Record

Before `weft_fetch`, record:

```text
purpose | provider | operation | required inputs | expected output | indexed price | max_cost_usd
```

One selected exact contract permits one paid call. A report can use more than
one selected contract when separate evidence gaps can change the decision, but
state the expected cost before each call and avoid overlapping purchases.

After `weft_fetch`, add:

```text
timestamp | payment_status | paid_usd | held_usd | artifact_id or transaction identifier | returned scope
```

Report cost as `paid_usd + held_usd`. Preserve currencies and metric definitions
from the result. A search-volume number without its period, geography, match
method, and provider definition is not comparable evidence.

## Failure Rules

- Empty search: reformulate the free search and read the envelope's reason.
- Incomplete contract: do not pay. Name the missing binding or output.
- Over-policy price: stop. Do not weaken wallet policy or silently raise the cap.
- Pending or ambiguous payment: preserve the receipt and do not retry the paid
  call.
- Upstream error after payment: report the returned error and cost; search for a
  substitute only if a new purchase is still justified.
- Partial rows: use returned rows with their sample limit. Do not treat omitted
  records as proof that no other records exist.
