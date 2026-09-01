---
name: weft-seo
description: Audit and improve organic search visibility with evidence bought through Weft. Use for SEO audits, technical SEO, indexability, on-page content, structured data, keyword and competitor research, backlinks, local SEO, or AI-search visibility. Inspect the target first, then load the current `weft` skill to discover live providers for missing external evidence. Never rely on a stored provider list or price.
---

# Weft SEO

Turn an organic-search goal into a prioritized action plan. Inspect the target
with free public or first-party evidence first. Use Weft for external evidence
that the target cannot prove, such as current result pages, search demand,
competitors, backlinks, trends, or local listings.

Load the `weft` skill before provider discovery. Its live search, contract,
attribution, wallet, receipt, and secret-safety rules are authoritative. When
`weft_*` tools are missing, use the `weft-setup` skill.

Read these focused references when needed:

- [provider routing](references/provider-routing.md) for evidence gaps and paid
  contract selection;
- [report contract](references/report-contract.md) for findings, priorities,
  and the evidence ledger;
- [primary sources](references/primary-sources.md) before making general SEO
  claims.

## Outcome Contract

| Field | Contract |
|---|---|
| Goal | Explain what blocks or limits the requested organic-search outcome and identify the next actions |
| Inputs | Target URL or domain, desired outcome, market or location, known competitors, first-party data, freshness need, and paid-data preference |
| Output | Evidence-led findings, prioritized actions, unknowns, and an evidence and spend ledger |
| Acceptance | Every important finding has evidence or an inference label; every action has impact, effort, confidence, and a completion test |
| Limits | No ranking promise, no hidden purchase, no automatic paid retry, no unobserved traffic or search-volume claim |
| Non-goals | Editing the site, buying links or reviews, publishing content, changing Search Console, or creating a permanent provider catalog |

## Required Flow

### 1. Define the decision

Record what the user wants to improve. Examples are discovery for a product,
qualified non-brand traffic, local visits, indexed documentation, or recovery
from a known decline.

Record the target, market and language, location when local intent matters,
known competitors, time range, and access to first-party analytics or search
data. Do not block a first pass when optional inputs are absent. State how each
missing input limits confidence.

Respect a no-spend request. If the user did not state a paid-data preference,
free discovery is allowed, but state the expected price before each paid call
as required by `weft`.

### 2. Inspect the target first

Use available public-web tools and user-supplied data to observe the target.
Inspect only what is relevant:

- response and redirect behavior;
- robots directives, sitemap discovery, canonical references, and index
  signals;
- titles, descriptions, headings, visible copy, images, and internal links;
- structured data and whether it agrees with visible content;
- important templates and duplicate or near-duplicate patterns;
- performance evidence when a current field or lab source is available.

Record exact URLs, timestamps, and sample size. A blocked page is unknown, not a
passing page. A small sample is not a site-wide conclusion.

Do not recommend meta keywords. Do not promise that a valid sitemap, structured
data block, or technically crawlable page will be indexed or rank.

### 3. Name the external evidence gaps

Do not buy data because it is available. Write the decision that each purchase
will support. Common gaps are:

- which queries and result pages define the real competitive set;
- current demand, seasonality, geography, and intent;
- which domains and pages earn relevant links;
- current local listings, categories, reviews, or map competitors;
- which facts need current web search or page extraction at scale.

Keep observed facts, provider evidence, and recommendations separate.

### 4. Discover a current provider

For each necessary gap, call `weft_search` with a capability query that includes
the subject, geography, language, freshness, and required output fields. Search
is free. Reformulate an empty or weak query before concluding that no operation
exists.

Read every candidate's typed inputs, request bindings, output summary,
freshness, attribution, price, and `contract_url`. Fetch the full contract when
the inline result is insufficient and always before an asynchronous submission.

Reject a contract when it cannot bind every material input. A description that
mentions keywords, rankings, backlinks, or local data is not enough. Do not use
a historical provider name, endpoint, price, or sample as a current contract.

Choose the cheapest exact contract. Prefer better relevance only when price is
equal, or when its declared freshness, geography, coverage, or output is needed
for the user's decision.

### 5. Make one bounded paid call

Call `weft_balance` before the first paid fetch. Stop when balance or policy
headroom is below the expected cost. State the provider, operation, purpose,
expected price, inputs, and evidence it should return.

Build the request from the live contract. Copy its attribution fields. Set a
tight `max_cost_usd` on every `weft_fetch`; never silently raise it. Make the
smallest useful request and call it once.

Do not retry a paid call after a timeout, pending receipt, or ambiguous result.
Do not automatically retry any paid fetch. Search for a substitute provider or
return the evidence gap. A policy or balance refusal is a hard stop.

After the call, decode the result and preserve the provider, query, timestamp,
scope, receipt identifiers, protocol, payment status, and cost. Report actual
cost as `paid_usd + held_usd`. A held amount can mean money moved even when the
final result is not ready.

Never request or forward wallet keys, provider credentials, cookies,
authorization headers, or payment proofs. Do not claim durable idempotency for
a paid request.

### 6. Analyze without false precision

For each finding, state:

- the claim;
- whether it is an observed fact, provider evidence, or inference;
- source and sample;
- why it matters to the requested outcome;
- severity and confidence;
- the smallest action that can test or fix it.

Do not create an overall numerical SEO score unless the user supplies a scoring
model. Do not call a page's current rank, traffic, search volume, backlink
count, local position, or performance good or bad without current evidence.

For AI-search visibility, apply the same crawlability, content quality,
structured-data, and people-first principles. Do not require special AI-only
markup or promise inclusion in a generated answer.

### 7. Deliver the report

Follow the [report contract](references/report-contract.md). Lead with the few
actions most likely to change the user's outcome. Include only applicable
sections and put supporting detail after the action plan.

End with:

- unknowns and blocked checks;
- evidence timestamps and sample limits;
- each Weft provider and operation used;
- receipt state and identifiers safe to show;
- total `paid_usd + held_usd`, including zero when no purchase was made.

## Completion Gate

Do not call the work complete until:

- the target and business outcome are explicit;
- important facts have a source, and inferences are labeled;
- every paid result came from a live exact contract;
- every priority names impact, effort, confidence, and a completion test;
- missing evidence remains visible;
- provider provenance, receipt state, and real spend are reported.

If the evidence is insufficient, return a useful partial report. Name the next
free check or exact capability needed. Do not fill gaps with generic SEO advice.

## Safety

- Do not buy or recommend deceptive links, reviews, traffic, or content.
- Do not bypass access controls, robots restrictions, or authenticated systems.
- Do not expose private analytics, search data, customer data, or credentials.
- Do not make changes to a site or third-party account without a separate,
  explicit user request and confirmation for the exact side effect.
