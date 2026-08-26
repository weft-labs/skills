---
name: weft-setup
description: Connect this agent's user to a Weft Account — a wallet for finding and paying for paid data, APIs, and real-world actions. Use when asked to set up, install, or connect Weft, when `weft_*` tools are missing, or when a task needs Weft and no credential exists. One-shot — after setup, the installed `weft` skill owns ongoing usage.
---

# Set up Weft

Weft gives the user one account that agents can search and spend from,
inside a spending policy. Setup means establishing that account connection
from wherever you are running. Four MCP tools arrive with it:
`weft_balance`, `weft_search`, `weft_fetch`, `weft_connection_status`.

**Auth is OAuth in the browser on first use.** There is no API key to
paste, and you must never ask the user for a password, API key, or token.

## The one decision: credential scope

| Credential | Scope | Survives |
|---|---|---|
| OAuth grant (plugin or MCP) | the user's **account** | every surface, every device, container reclaim |
| CLI credential store | one machine | that machine only |

Always establish the **account-level OAuth connection first** — it is the
only credential whose scope matches a user rather than a machine, so it is
never wasted work. The CLI is an optional machine-local add-on, offered
last and only where it can survive.

## Step 1 — establish the account connection (always)

Work down this list; take the first branch that applies to the surface you
are running on. Do not ask the user to choose between mechanisms — the
surface decides, and every branch ends in the same OAuth grant.

1. **Claude surface with plugin support** (Claude Code, Claude desktop,
   claude.ai, Cowork): install the Weft plugin — it bundles the MCP server
   and this skill set.

   ```
   /plugin marketplace add weft-labs/weft-claude-plugin
   /plugin install weft@weft-labs
   ```

   If the plugin is already installed, stop — do not add a second manual
   MCP connection beside it.

2. **Host with an MCP configuration** (Codex, Cursor, Cline, opencode,
   OpenClaw, Hermes, VS Code, Copilot CLI, or any host speaking streamable
   HTTP): add the hosted server `https://weft.network/mcp`. Exact per-host
   config shapes are in [rules/hosts.md](rules/hosts.md) — copy the shape
   for the detected host; never guess a config format for an unknown host.

3. **GUI host with a connectors UI** (ChatGPT, other GUI clients): the
   human adds `https://weft.network/mcp` as a custom connector in the
   host's Connectors/Apps settings.

4. **None of the above**: send the human to
   https://weft.network/dashboard/connect for manual instructions. Stop
   rather than guessing.

The first tool call opens a browser sign-in; that is expected. The grant
appears under the user's Weft Connections and is revocable at any time.

## Step 2 — no account yet?

OAuth signs in an account that already exists. If the user has none, ask
for **their email address only** and create a temporary bootstrap:

```sh
curl -fsS -X POST "https://weft.network/api/v1/account_bootstraps" \
  -H "Content-Type: application/json" \
  -d '{"email":"THEIR_EMAIL","agent_name":"YOUR_AGENT_NAME"}'
```

The response contains `temporary_api_key` (a secret `wbt_` bearer — never
print it). Configure the MCP server as in Step 1, but send it as a static
`Authorization: Bearer` header instead of OAuth. Claude Code example:

```sh
claude mcp add --transport http weft https://weft.network/mcp \
  --header "Authorization: Bearer THE_TEMPORARY_KEY"
```

A claim link goes to the email. The human approves; the same credential is
promoted in place — search works while pending, balance and fetch unlock
after the claim. `weft_connection_status` reports progress. There is no
promotional balance: the human funds the wallet before the first paid
fetch.

On a persistent machine with a shell, `weft bootstrap` from the CLI
(Step 3) is an equivalent, more automated path to the same flow.

## Step 3 — offer the CLI (only where it survives)

Offer the machine-local CLI as an **add-on** — never instead of Step 1 —
when all three hold:

- you can execute shell commands,
- Node.js is available,
- the filesystem persists across sessions — **not** an ephemeral cloud
  sandbox or container that is reclaimed after the task.

```sh
npm install -g @weft-labs/cli
```

One line to the user is enough: "Your account is connected. This machine
can also run the Weft CLI for headless and scripted use — want it?" If any
condition fails, skip this step silently; in an ephemeral environment a
CLI credential would appear to work and then vanish with the container.

## Verify

1. Follow the host's reload step (restart, or start a new session — the
   tools appear in the next session, not this one).
2. Call `weft_balance` — or `weft_connection_status` if a claim is still
   pending.
3. Confirm the `weft` usage skill is discoverable. It owns everything from
   here: searching, spending rules, receipts. Do not duplicate its content.

If either check fails, report exactly what you changed and what the host
said. Do not invent an API key or fall back to an unrelated config.

## Hard rules

- Never ask for, accept, generate, or store a password, `wk_` key, or
  OAuth token. Never print a `wbt_` credential.
- One connection per host — plugin OR manual MCP entry, never both.
- No promotional balance, free credit, or subsidy exists. Say so before
  the user expects a paid fetch to work on an unfunded wallet.
