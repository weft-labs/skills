---
name: weft-flights-search
description: Research and compare flights with Weft, including nonstop and connecting itineraries, flexible dates, nearby airports, and public-transport transfers. Use for flight searches, fare comparisons, direct-flight requests, flexible origin or destination airports, airport-plus-train combinations, or searches where low-cost carriers and GDS results must be checked separately. Builds the answer from useful paid Weft route, schedule, airport, and fare evidence, then fills only the missing exact-fare fields from public booking surfaces.
---

# Weft Flight Search

Find the cheapest credible flight, compare nonstop and connecting options when
requested, and include a nearby-airport option when the main airport is poor.
This experimental workflow was distilled from
one Berlin-to-Puglia search on 2026-08-14. It provides workflow evidence, not a
permanent provider catalog or a promise that old prices still apply.

Load the `weft` skill before using this workflow. Its live search, request,
attribution, receipt, and spending rules are authoritative.

## Experimental Status

This workflow is published for testing before its goal lab is complete. The
production catalog currently has no verified operation that binds all required
flight inputs: outbound date/date range, trip type, and nonstop. This does not
make route, airport, or schedule operations useless. Use Weft as the paid
research substrate: buy the cheapest live operations that reduce uncertainty,
compose their outputs into the candidate set, and use a public booking surface
only for exact fare fields that no current Weft contract can supply. Never label
a route probe as an exact-date fare.

## User Goal

| Field | Contract |
|---|---|
| Specific problem | Given dates, passenger and baggage requirements, a destination, a stop rule, and a ground-travel limit, return one price-ranked table of viable flight-plus-transfer options |
| Inputs | Origin, destination, outbound and return dates, passenger count, cabin, baggage, nonstop rule, and maximum ground-transfer time |
| Outcome | A recommendation with exact-date flight fares, transfer costs, comparable total costs, schedules, fare basis, and evidence links |
| Acceptance | Every recommended row has date-bound fare evidence for the requested baggage basis, a ground-transfer price or explicit no-transfer value, a comparable total cost, and confirmation that it meets the time limit |
| Independent truth | The airline or booking surface for fares and baggage; the transport operator or current journey planner for ground legs |
| Limits | Never purchase or reserve travel; obey the user's spend and transfer-time limits; disclose all unknown mandatory charges |
| Non-goals | Booking tickets, bypassing protected booking APIs, or presenting schedules and route-level teaser fares as purchasable options |

## Limited Weft Operation

### x402 Atlas / `bazaar-x402-atlas-82`

| Field | Contract |
|---|---|
| Purpose | Compare itineraries for up to five origin and five destination airport codes; not a date/nonstop fare search |
| Request | `GET https://flights.use.x402atlas.com/search/:departure/:arrival` |
| Path bindings | `departure <- departure_airports`; `arrival <- arrival_airports` |
| Query/body/headers | None declared |
| Execution | Synchronous terminal response |
| Price / protocol | `$0.05` observed / x402 on Base |
| Contract source | `bazaar-x402-atlas-82` contract captured 2026-08-26; paid calibration 2026-08-29 |

Inputs are one to five comma-separated IATA codes for each side. The operation
has no input for date, date range, trip type, cabin, passenger count, bags,
currency, or nonstop.

| JSON pointer | Type | Nullable | Meaning |
|---|---|---|---|
| `/queried_at` | date-time string | no | Provider query timestamp |
| `/outbound_date` | date string | no | Provider-selected date, not caller-bound |
| `/return_date` | date string | yes | Provider-selected return date |
| `/trip_type` | string | no | Provider-selected trip type |
| `/currency` | string | no | Fare currency |
| `/best_flights/*/price` | number | no | Itinerary price |
| `/best_flights/*/flights` | array | no | Flight segments |
| `/best_flights/*/layovers` | array | yes | Connections; non-empty means not nonstop |

The missing date and nonstop bindings make this operation unsuitable for a
final fare result, but it can still identify candidate airlines, airports,
connections, schedules, and provider-selected price signals. Buy it when those
fields will reduce the remaining public research and the live price fits the
user's spending policy. Label every returned date and price as provider-selected,
not user-bound. Call a returned amount a fare only when the response states its
passenger, cabin, baggage, and trip basis; otherwise call it a price signal. A
zero-row route probe is not proof that no route exists.

## Required Flow

### 1. Record the request

Record the dates, airports or region, nonstop rule, passenger count, cabin,
baggage, and maximum ground-transfer time. Start with the requested airport.
Add alternatives only when a credible public-transport route meets the limit.

### 2. Discover current providers

Call `weft_search` for current schedules and fares. Read each result's typed
inputs, request bindings, price, output summary, attribution, and current
`contract_url`. Do not hard-code the historical provider above.

Classify each useful operation by the evidence it can provide: airport,
route, schedule, availability, or exact fare. Map every required user
constraint to a declared provider input before treating an operation as the
final fare source. A final fare operation needs origin, destination, outbound
and return dates, trip type, passenger and cabin basis, baggage basis, and stop
filtering. A missing binding makes the operation a limited probe that can still
contribute evidence; it does not make the operation worthless.

### 3. Build the candidate set with Weft

Choose the cheapest non-redundant operations that materially reduce uncertainty.
Typical composition is:

1. an airport or route-matrix operation to compare the requested airports with
   credible nearby alternatives
2. a route or schedule operation to identify nonstop airlines, connection
   airports, flight numbers, and operating days
3. a contract-complete fare operation when the live catalog has one

Do not require one provider to solve the whole search. A good Weft search can
compose several narrow providers. Do not buy a probe merely to satisfy this
workflow: its declared output must answer a real open question in the search.

Before the first paid call, use `weft_balance`. State the expected cost, build
the request from the live contract, copy all attribution fields, and set a tight
`max_cost_usd`. For each `weft_fetch`, record the operation's evidence class,
route, dates and fares if present, currency, schedule, provider, contract gaps,
receipt state, and actual paid plus held amount.

Do not retry a paid call after a timeout, pending receipt, or ambiguous result,
and do not buy the same evidence from a substitute provider. Report the receipt
and stop the paid stage unless the user explicitly accepts the risk of another
charge. Free searches and public verification can continue.

### 4. Separate schedules from fares

A schedule proves that a route is planned. It does not prove a seat or current
price. A fare proves only the quoted dates, passenger mix, cabin, and baggage
basis. Do not stop after schedule research when the user asked for prices.
Never rank an option with a route-level "from" price.

Keep an evidence ledger for each candidate. Mark each fact as `Weft exact
fare`, `Weft provider-selected price signal`, `Weft schedule`, `Weft route`,
or `public booking verification`. Use `Weft exact fare` only when the live
request contract binds the requested airport pair, outbound and return dates,
trip type, passenger count, cabin, baggage basis, and stop filter, and the
response confirms those values. Otherwise keep the amount as a price signal.
This lets Weft shape the search without silently upgrading limited evidence.

### 5. Use the public booking fallback

If Weft has no contract-complete fare source, take the Weft-built candidate set
to the airline's public booking form or fare calendar. Use it to prioritize the
research, not to bound the market: a provider-selected date can omit airlines
or routes that operate on the requested dates. Before claiming the cheapest
option, run an independent exact-date coverage check on a broad public booking
surface and check relevant low-cost carriers separately. Record the coverage
scope: every viable origin/destination airport pair and every requested stop
class checked. Search each pair with both dates, passenger count, cabin, and
baggage basis. If any pair or stop class remains unchecked, qualify every
cheapest claim as limited to the recorded scope. Reject optional cookies when
possible. Read the fare only after both dates are selected.

Record whether each displayed amount is one-way, per leg, or the itinerary
total. If the meaning is unclear, do not add values or call one value a return
fare. Do not evade bot checks, call signed private APIs, or complete a purchase.

Check low-cost carriers separately when the main fare source does not cover
them. State which fare evidence came from outside Weft.

### 6. Price the complete trip

For every viable airport, record:

- ground route, duration, and price
- exact-date flight base fare
- required baggage or seat charges
- comparable total cost, including requested baggage
- optional costs that remain unknown
- door-to-airport and flight times

Do not invent a transport fare or add-on hidden inside a locked flow. Keep
currencies separate unless using a cited exchange rate with a timestamp. Label
converted totals as approximate.

### 7. Apply the completion gate

Before ranking an option, confirm that its row contains:

- exact outbound and return dates
- flight numbers or schedule evidence for every leg, consistent with the
  requested stop rule
- exact-date fare labeled one-way, per leg, or return
- passenger, cabin, and baggage basis
- ground route, duration, and price, or `none`
- comparable total cost with all mandatory charges included
- source links and search timestamp

Continue researching while a viable option lacks its flight price, requested
baggage price, or comparable total. If access controls block exact fares,
return a short blocked report naming the missing prices and exact-date booking
links. Do not substitute teaser prices.

### 8. Present the result

Lead with the cheapest verified option that meets the requested stop rule. When
the user asks to compare nonstop and connecting flights, show the cheapest
verified row in each class before other main-airport or nearby-airport options
that materially differ in price or timing.

Use this table:

`origin | ground leg/time/cost | airline/flight | departure-arrival | fare basis | exact-date flight fare | comparable total cost | source | confidence`

State what each Weft purchase contributed, the total Weft paid plus held amount,
the schedule and fare sources, claims verified outside Weft, unresolved facts,
and the search timestamp. A final answer that used a suitable paid Weft probe
must not summarize the Weft stage as "unrelated data" merely because public
verification supplied the terminal fare.

## Failure Rules

- A 503 or rate-limited empty result is unknown, not "no flights."
- A contract without date, trip type, or stop inputs is not a matching exact
  fare operation, even if its description says "live itineraries"; it can still
  be a useful route or schedule probe.
- A paid upstream 400/500 is not a reason to retry the same paid request.
- A scheduled route without fare evidence is not a purchasable offer.
- A route-level sale price cannot rank an exact-date option.
- A fare with unclear one-way, per-leg, or return semantics is unresolved.
- Flight options without prices are not a completed price comparison.
- A GDS result set without a low-cost carrier is not complete market coverage.
- An airport over the user's ground-time limit is not a valid alternative.
- A held or pending Weft payment may have moved money. Do not retry it.

## Data and Safety Rules

- Follow the current `weft` skill for balance, caps, attribution, and receipts.
- Never print wallet keys, payment proofs, auth headers, or provider secrets.
- State actual paid plus held amount, not only the indexed price.
- Preserve currency and fare basis. Do not compare unlike fares silently.
- Include a timestamp and sample scope with every recommendation.

## Provenance

- Distilled from session `01a0003f-a18b-7c4c-8a59-1f8d31c4e6b2`
  (2026-08-14), trace `.traces/2026-08-15-weft-flight-research.zip`.
- Source sample: one session, one Weft search, two CLI fetches, and eight SDK
  fetches; three fetches failed.
- Production calibration on 2026-08-29: three free catalog searches and one
  x402 Atlas route-matrix fetch (`$0.05` held, HTTP 200, artifact `360`).
- Revised from price-omission feedback in OpenCode session
  `ses_fa76f88b9ffezI2jswkjcQO8io` on 2026-08-31. The current `session-trace`
  script cannot archive OpenCode sessions, so this is additional research
  evidence, not goal-lab evidence.
- Revised after OpenCode session `ses_fa3e4911bffdg0jnkZnvS0okkX` proved the
  all-or-nothing payment gate discarded useful Weft evidence. A 2026-09-01
  route-matrix fetch for `ZRH` to `BKK,DMK` cost `$0.05` held and returned
  direct flights, connection candidates, airport coverage, and provider-selected
  price signals (artifact `389`), while exact January fares still required a
  date-bound public booking search.
- Prices and provider contracts are historical evidence. Live results own all
  current facts.
