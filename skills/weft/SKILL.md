---
name: weft
description: Find and buy paid data, APIs, or real-world actions for the current task — enrich a list of companies or people, find and verify contact details, get structured social/review/product/market data, or trigger a paid service. Proactively call `weft_search` before writing a scraper, before a generic web fetch for structured data, and before telling the user something is inaccessible. Skip Weft for local coding, writing, file manipulation, ordinary public-web research, or when the user requests no external services or spending. When `weft_*` tools are missing, use the `weft-setup` skill.
---

# Use Weft

Weft is a paid-data marketplace for agents. Four tools do all the work:

- `weft_search` — FREE. Treat it like a web search engine, but over the
  paid-API index. Use it to discover what exists: providers, capabilities,
  endpoints, call contracts, and prices. Search early, search often, and
  refine with `filters`. It never costs money.
- `weft_fetch` — PAID. Executes the endpoint you chose and settles the
  micropayment from the user's wallet. This is the only step that spends
  money. Use it to pay for the data or action the search found.
- `weft_balance` — read-only. Shows the wallet balance and the spending
  policy. Call it before the first paid fetch of a task; the wallet still
  enforces the policy on every call.
- `weft_connection_status` — read-only. Reports the state of this
  connection and which tools it can currently call. Use it when a call is
  refused, or while a new account claim is still pending.

The loop is always the same: **search (free) → choose → fetch (paid) →
present**. A complex job runs this loop several times: the output of one
fetch becomes the input of the next. Weft is like giving an agent a shell —
compose small paid services into a pipeline.

On hosts with a shell, the optional Weft CLI mirrors these tools as
commands; see [rules/cli.md](rules/cli.md). Everything below applies to
both surfaces — same loop, same receipts, same safety rules.

## Workflow

### 1. Search first — it is your web search

Start every task with `weft_search`. The live results own the endpoint
contracts and prices; never rely on a remembered provider catalog.

- Search is free. Run it early and iterate: broad query first, then
  reformulate or narrow. An empty result set is not a dead end — it is a
  signal to search again with different words.
- Use `max_results` (1–50, default 10) to control the result count. Never use
  `limit` — the server rejects it.
- Narrow with `filters` when the user states a constraint:

  | Filter | Purpose | Example |
  |---|---|---|
  | `type` | Kind of resource: `api`, `agent`, `mcp_tool`, `webpage`, `feed`, `document`, `dataset` | `{ "type": { "eq": "agent" } }` |
  | `protocol` | How the endpoint is paid: `x402`, `a2a`, `mpp`, `erc_8004` | `{ "protocol": { "eq": "x402" } }` |
  | `price` | Price cap in USD decimal STRINGS. Exactly one of `lte`, `gte`, `eq`, or the pair `range_gte` + `range_lte` | `{ "price": { "lte": "0.001" } }` |
  | `price_atomic` | The same price constraint as integer micro-USD (1 USDC = 1_000_000). Set `price` OR `price_atomic`, never both | `{ "price_atomic": { "lte": 10000 } }` |

  `price` values must be strings: send `{ "lte": "0.001" }`, never
  `{ "lte": 0.001 }`. A JSON number is rejected.

### 2. Choose one result

Read the result envelope. Each `results[]` item has:

- Curated results are compact: `provider`, `operation`, typed `inputs`, exact
  `request` bindings, one recommended `access`, `attribution`, an output
  summary, and a content-addressed `contract_url` for full details.
- In `request`, each mapping is `wire_name: input_name`. URL-encode and
  substitute `path`, append URL-encoded `query` values (repeat the key for
  arrays), and JSON-encode `body.fields`. Send the declared headers and body
  media type.
- `access.price.indexed_usd` is the observed price. The live payment challenge
  remains authoritative.
- Pass all three `attribution` values to `weft_fetch`; do not reconstruct them.
- Fetch `contract_url` when the inline inputs, request recipe, price, and output
  summary are insufficient. Always fetch it before an async submission. It
  contains the full provider lifecycle, alternatives, evidence, and known gaps.
- Platform results retain the legacy `provider` / `capability` / `endpoints[]`
  shape. For those, use `endpoints[0]` and its `call` and `price` blocks.
- `score` — relevance; higher is better.

Select the cheapest endpoint that satisfies the request. When prices are
equal, prefer the higher `score`. Do not pick the most relevant result if a
cheaper one does the job. If a merchant looks unproven (very new, no
settlement history), flag it to the user before spending against it.

When the result set is empty, read `match_quality`, `reason`, and
`suggestion` in the envelope — the server tells you why nothing matched.
Loosen the filters or change the query and search again; it costs nothing.

### 3. Fetch to pay

Before the first paid fetch of a task, call `weft_balance`. Abort and tell
the user when the balance or the remaining transaction, daily, or weekly
policy headroom is below the expected cost. The wallet enforces the policy
on every call — this check exists so you never propose spend the wallet
will refuse.

Call `weft_fetch` with:

- `url` — the final URL built from the curated `request`, or the exact legacy
  `endpoints[0].url`
- `max_cost_usd` — a tight cap as a decimal string (e.g. `"0.02"`). Always
  set it — an unset cap silently defaults to `"0.10"`. Never silently raise
  it.
- `method` / `body` / `headers` — per the curated request recipe or legacy
  endpoint call contract
- `search_id`, `operation_id`, and `access_method_id` — copy the curated
  `attribution` block. For legacy results, always pass `query_trace_id` as
  `search_id` and pass operation/access ids when present.

After the call:

- Decode `body_base64` when present — that is the purchased data.
- Read the receipt. The cost is `paid_usd + held_usd`. `payment_status:
  "pending"` with a `held_usd` amount is a successful paid request whose
  settlement is still confirming — money likely moved, do not retry.
- Preserve receipt identifiers such as `artifact_id`, `tx_hash`, `protocol`,
  and `payment_status`.
- When `access.weft_fetch.coverage` is `submission_only`, the paid fetch starts
  the work but does not return the final result. Read the response id at
  `output.workflow.id_pointer`, then follow the documented free poll request
  until a listed success or failure value. Reuse every identity header exactly
  as documented. Do not send the free poll through `weft_fetch`, and do not
  repeat the paid submission while a job is pending.

### 4. Present the result

Return the decoded data to the user, not the raw receipt. State what you paid
and from which provider.

## Compose services — Weft is your shell

One fetch rarely completes a real job. Weft is a toolbox: chain two or more
services, like shell pipelines. Each stage is one `search → choose → fetch`
pass. The output of one stage becomes the input of the next. Search at every
stage is free — use it to find the provider for the next step.

**Example — prospect table.** Build a table of CTOs at companies building AI
agents: `| name | surname | email | website | LinkedIn |`.

1. **Find the companies.** Search for a company or web-search provider and
   fetch it to list the target companies with their domains and websites.
2. **Find the people.** Search for a people-search provider (for example
   Apollo, People Data Labs, or Minerva) and fetch it filtered to the title
   and industry. Collect the names, companies, and any emails already
   returned.
3. **Enrich.** For the people who still lack an email or LinkedIn URL, search
   for a people-enrichment endpoint and fetch it once per person.
4. **Verify (optional).** Check the deliverability of the emails with an
   email verifier before the user sends anything.
5. **Assemble.** Merge the payloads into the requested table and present it.

Pipeline rules:

- Do not manage the budget. The wallet enforces the spending policy: it
  refuses any call the policy, the per-call cap, or the balance does not
  allow. Set a tight `max_cost_usd` per call and state the expected cost
  before you spend.
- Prefer one endpoint that returns everything you need over several calls.
  Enrich only the records that still miss fields.
- Pass each stage's `query_trace_id` as `search_id` on that stage's `fetch`,
  so every purchase is attributed to the search that found it.
- A failed record is not a failed pipeline. Continue with the rest, then
  report the failures.
- Do not retry a paid call. If a stage fails, search again for a substitute
  provider — that search is free.

## Side-effecting actions (POST)

Some endpoints change the world: send an SMS, book a slot, print a label.
`weft_fetch` with `method: "POST"` is a real-world action.

- Search and choose as usual.
- Before you call it, show the user the recipient and the payload, and get
  explicit confirmation.
- A policy, balance, price-cap, or denylist refusal is a hard stop. Explain
  it; do not weaken or work around the user's controls.

## Spending and side-effect safety

The wallet enforces the spending policy on every paid call. It refuses any
request that exceeds the policy, the per-call cap, or the balance. You do
not track budgets or compute remaining spend — the wallet does that.

- Call `weft_balance` before the first paid fetch of a task; abort when
  the balance or policy headroom is below the expected cost.
- Set a tight `max_cost_usd` on every fetch. Never silently raise it.
- State the expected cost before a paid call, and the actual cost after it
  (`paid_usd + held_usd`).
- A policy, balance, price-cap, or denylist refusal is a hard stop. Explain
  it; do not weaken or work around the user's controls.
- Do not automatically retry any paid fetch after a timeout or ambiguous
  response. Search, balance, and connection-status calls are safe to retry.
- Confirm a side-effecting request's recipient and payload when the user did
  not specify them clearly.
- Never request or forward wallet keys, provider credentials, cookies,
  authorization headers, or payment headers. Never print or ask the human to
  paste a `wk_`, `wbt_`, or OAuth credential.
- Do not claim durable idempotency for paid calls. A repeated request can
  create a second charge or side effect.

## Errors

- Missing `weft_*` tools: stop and use the `weft-setup` skill (hosted at
  https://weft.network/setup.md). Do not invent an API key or an MCP
  configuration.
- A refusal on `weft_balance` or `weft_fetch` while a new account claim is
  still pending is the contract working, not a bug. Check
  `weft_connection_status`, and finish the claim before retrying.
- `insufficient_scope`: tell the user Weft authorization must be renewed with
  the required scope.
- `POLICY_VIOLATION_*`: the spending policy refused the call — a cap, a
  spend window, a denylist, or a missing policy, not necessarily
  overspending. Surface the `dashboard_url` so the user can adjust. Hard
  stop; do not retry silently.
- `SETTLEMENT_FAILED`: settlement failed upstream. The error's `protocol`
  detail names the payment rail that failed. Surface it and stop; do not
  retry a paid call.
- Search validation errors: correct the request to the live tool schema and
  retry the free search.
- Paid fetch errors or ambiguous outcomes: surface the receipt and error
  as-is; do not retry unless the user explicitly decides after seeing the
  risk.
