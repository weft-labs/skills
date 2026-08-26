# Weft CLI reference

The `weft` CLI is the machine-local surface for the same account: same
search → choose → fetch loop, same receipts, same safety rules as the MCP
tools in [SKILL.md](../SKILL.md). Use it on a persistent machine with a
shell — for headless runs, scripts, and pipelines. Never install it in an
ephemeral cloud sandbox: its credential store dies with the container.

It prints one versioned JSON object per command — parse the output instead
of reading prose. `weft --help` and `weft <command> --help` return
machine-readable JSON and need no credential; read them before guessing a
flag.

## Install

```sh
npm install -g @weft-labs/cli
```

Zero-install equivalent for any command below:

```sh
npx --package @weft-labs/cli weft --help
```

## Commands

Once an authenticated credential exists — from the bootstrap flow below or
an existing `WEFT_API_KEY`:

```sh
weft me                                                  # who am I
weft balance                                             # wallet + spending policy
weft search "weather data API" --max-results 5           # free
weft fetch "https://merchant.example/data" --max-cost-usd 0.05
weft purchases                                           # receipt history
```

- `weft fetch` always requires `--max-cost-usd`. Set a tight ceiling; never
  omit it.
- Every spending rule from SKILL.md applies verbatim: balance before paid
  actions, state costs, no silent retries of paid calls, hard stop on policy
  refusals.

## Bootstrap (no credential yet)

The CLI can start with nothing but the human's email address. Never ask
for, accept, or store their password.

```sh
# 1. Create the temporary bootstrap; a claim link goes to the email only.
weft bootstrap --email "human@example.com" \
  --agent-name "Research agent" \
  --reason "Find weather data"

# 2. Search immediately — free, works while the claim is pending.
weft search "weather data API"

# 3. Tell the human to open the claim email and approve. Show them the
#    user code from the bootstrap response so they can match this session.

# 4. Poll at the interval the bootstrap response returned — no faster.
weft auth status

# 5. After approval the stored credential is promoted in place.
weft me

# 6. A new wallet holds nothing. Ask the human to fund it before any
#    paid fetch.
weft balance
```

Status lifecycle: `pending` (search works, keep polling) → `claimed` /
`consumed` (done — normal commands work) or `rejected` / `expired`
(terminal — stop; do not create a second bootstrap for the same request
without asking the user).

The temporary `wbt_` credential is secret, expires in 30 minutes, and is
search-only until claimed. Refusals on balance/fetch before the claim are
the contract, not bugs. The CLI stores every credential in a mode-0600
local file and never prints secrets — neither do you.

## Credentials

Precedence: `--api-key-stdin`, then `WEFT_API_KEY`, then the stored
bootstrap/OAuth credential. The CLI rejects API keys passed as command
arguments so they never reach shell history. Never echo any credential —
`wbt_`, `wk_`, or an OAuth token — into your output.

## Errors

One JSON object on stderr with a stable `error.code`. Exit codes: `2`
invalid usage, `3` missing auth or 401/403, `4` other 4xx or policy
rejection, `5` 5xx/network/internal. `POLICY_VIOLATION_*` and
`SETTLEMENT_FAILED` are handled exactly as in SKILL.md.
