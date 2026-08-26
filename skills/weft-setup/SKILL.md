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

1. **Claude Code**: install the Weft plugin — it bundles the MCP server
   and this skill set.

   ```
   /plugin marketplace add weft-labs/weft-claude-plugin
   /plugin install weft@weft-labs
   ```

   If the plugin is already installed, stop — do not add a second manual
   MCP connection beside it. If the user has no account, use
   `/weft:setup THEIR_EMAIL` (Step 2), never a manual connection.

   The plugin pins the production server. If the URLs in this document
   name any host other than `https://weft.network`, you are setting up a
   different deployment: skip the plugin and use branch 2 with this
   document's URLs.

2. **Host with an MCP configuration** (Codex, Cursor, Cline, opencode,
   OpenClaw, Hermes, VS Code, Copilot CLI, or any host speaking streamable
   HTTP): add the hosted server `https://weft.network/mcp`. Exact per-host
   config shapes are in [rules/hosts.md](rules/hosts.md) — copy the shape
   for the detected host; never guess a config format for an unknown host.

3. **GUI host with a connectors UI** (Claude desktop, claude.ai, Cowork,
   ChatGPT, other GUI clients): the human adds `https://weft.network/mcp`
   as a custom connector in the host's Connectors/Apps settings.

4. **None of the above**: send the human to
   https://weft.network/dashboard/connect for manual instructions. Stop
   rather than guessing.

The first tool call opens a browser sign-in; that is expected. The grant
appears under the user's Weft Connections and is revocable at any time.

## Step 2 — no account yet?

OAuth signs in an account that already exists. If the user has none, ask
for **their email address only** — never a password — and take the ONE
path that matches how Step 1 connected. The temporary `wbt_` credential
every path creates is a secret: never print, echo, log, or paste it into
the conversation. After the human claims the account, the same credential
gains balance and fetch access — treat it like money from the start.

- **Plugin (branch 1):** run `/weft:setup THEIR_EMAIL`. The command
  creates the bootstrap and stores the credential in the plugin's private
  data without printing it. Do not add a manual MCP connection beside the
  plugin, and do not use the shell flow below.
- **Host with a shell:** use the CLI's bootstrap — it stores the
  credential in a mode-0600 local file and never prints it:

  ```sh
  npx --package @weft-labs/cli weft bootstrap --email "THEIR_EMAIL" \
    --agent-name "YOUR_AGENT_NAME" --reason "THE_TASK"
  ```

  Then either continue on the CLI, or configure the MCP server per
  branch 2 with OAuth after the claim.
- **Manual MCP config without the CLI (last resort):** keep the secret out
  of the transcript — write the response to a file, show the human only
  the non-secret fields, and pass the key by shell substitution:

  ```sh
  umask 077
  curl -fsS -X POST "https://weft.network/api/v1/account_bootstraps" \
    -H "Content-Type: application/json" \
    -d '{"email":"THEIR_EMAIL","agent_name":"YOUR_AGENT_NAME"}' \
    -o "$HOME/.weft_bootstrap.json"
  jq '.data | del(.temporary_api_key)' "$HOME/.weft_bootstrap.json"
  ```

  Configure the MCP server as in branch 2, sending the key as a static
  header via substitution so it never appears in the transcript — Claude
  Code example:

  ```sh
  claude mcp add --transport http weft https://weft.network/mcp \
    --header "Authorization: Bearer $(jq -r '.data.temporary_api_key' "$HOME/.weft_bootstrap.json")"
  ```

- **GUI host with no shell:** there is no safe bootstrap path here. Send
  the human to https://weft.network/signup to create the account in the
  browser, then connect with OAuth per Step 1. Do not improvise an HTTP
  flow.

A claim link goes to the email. The human approves; the same credential is
promoted in place — search works while pending, balance and fetch unlock
after the claim. `weft_connection_status` reports progress. There is no
promotional balance: the human funds the wallet before the first paid
fetch.

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
