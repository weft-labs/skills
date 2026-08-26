# Per-host MCP configuration shapes

Lookup table for [Step 1, branch 2](../SKILL.md) of `weft-setup`. Server:
`https://weft.network/mcp`, streamable HTTP, OAuth in the browser on first
use. Merge into existing structured config — never replace it. After any
change, follow the host's reload step, then verify.

For the no-account bootstrap variant, add the temporary key as a static
`Authorization: Bearer` header alongside the `url` in the same shape.

## Claude Code (when not using the plugin)

```sh
claude mcp add --transport http weft https://weft.network/mcp
```

The URL is positional — there is no `--url` or `--remote` flag. Uninstall:
`claude mcp remove weft`.

## Codex CLI / Codex App

```sh
codex mcp add weft --url https://weft.network/mcp
codex mcp login weft
```

After browser OAuth, start a new Codex task or restart the app. Uninstall:
`codex mcp logout weft && codex mcp remove weft`.

## Cursor

Merge into `~/.cursor/mcp.json` — the presence of `url` marks it remote,
no `type` field needed:

```json
{ "mcpServers": { "weft": { "url": "https://weft.network/mcp" } } }
```

## Cline

Merge into `~/.cline/mcp.json` — `type` is required; omitting it falls
back to legacy `sse`, which this server does not speak:

```json
{ "mcpServers": { "weft": { "type": "streamableHttp", "url": "https://weft.network/mcp" } } }
```

## opencode

Merge into `~/.config/opencode/opencode.json` — the remote transport is
named `remote`, and `enabled` must be set:

```json
{ "mcp": { "weft": { "type": "remote", "url": "https://weft.network/mcp", "enabled": true } } }
```

## OpenClaw

```sh
openclaw mcp set weft '{"url":"https://weft.network/mcp","transport":"streamable-http","auth":"oauth"}'
openclaw mcp login weft
```

Reload with `openclaw mcp reload`, then start a new session.

## Hermes

Merge into `~/.hermes/config.yaml`, then `hermes mcp login weft` and start
a new session (`/reload-mcp` does not reload skills). Hermes prefixes MCP
tool names — verify with `mcp_weft_weft_balance`:

```yaml
mcp_servers:
  weft:
    url: "https://weft.network/mcp"
    auth: oauth
```

## VS Code / GitHub Copilot Chat

Merge into the project's `.vscode/mcp.json`, then Command Palette →
`MCP: List Servers` → restart `weft`, approve OAuth, enable its tools:

```json
{ "servers": { "weft": { "type": "http", "url": "https://weft.network/mcp" } } }
```

## GitHub Copilot CLI

Inspect `copilot mcp add --help` first. If it lists `--type`:

```sh
copilot mcp add weft --type http --url https://weft.network/mcp --tools '*'
```

If it instead lists `--transport`:

```sh
copilot mcp add --transport http weft https://weft.network/mcp
```

If neither contract appears, stop and ask the user to upgrade.

## Anything else

Stop rather than guessing a config shape. Report the host name and
version, and point the human at the host's official remote streamable
HTTP + OAuth setup with `https://weft.network/mcp`, or at
https://weft.network/dashboard/connect.
