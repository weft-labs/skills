# Weft Skills

Canonical agent skills for [Weft](https://weft.network) — search the agent
web and pay any x402/MPP endpoint from a wallet the user controls.

**This repo is the single source of truth.** Every other place a Weft
skill appears — `weft.network`, the Claude plugin, the `@weft-labs/cli`
npm package — is a byte-identical mirror pinned to one commit of this repo
by a `SKILLS_REF` file and enforced by that consumer's CI drift check.
Never edit a mirror. To change a skill: PR this repo, merge, then bump
each consumer's `SKILLS_REF` and re-vendor.

## Skills

| Skill | Job | Lifecycle |
|---|---|---|
| [`weft`](skills/weft/SKILL.md) | Find and buy paid data, APIs, and real-world actions: the search → choose → fetch loop, receipts, spending safety. [`rules/cli.md`](skills/weft/rules/cli.md) adds the machine-local CLI surface. | Installed; persists on the host |
| [`weft-setup`](skills/weft-setup/SKILL.md) | Connect a user's Weft Account from any surface: plugin, MCP config ([per-host shapes](skills/weft-setup/rules/hosts.md)), connector UI, or bootstrap a new account. | One-shot; fetched, executed, discarded |

## Install

```sh
npx skills add weft-labs/skills
```

Or point an agent at the hosted copies:

- Setup (start here): `https://weft.network/setup.md`
- Usage: `https://weft.network/skills/weft/SKILL.md`

## Distribution

| Mirror | Mechanism |
|---|---|
| `weft.network/setup.md` + `/skills/weft/SKILL.md` | vendored into `weft-app` at its `SKILLS_REF` commit, drift-checked in its CI |
| Claude plugin `weft-labs/weft-claude-plugin` | vendors `skills/weft/` at its `SKILLS_REF` commit, drift-checked in its CI |
| `@weft-labs/cli` npm package | bundles `skills/weft/` at its `SKILLS_REF` commit, drift-checked in its CI |

## License

MIT
