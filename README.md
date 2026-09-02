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
| [`weft-flights-search`](skills/weft-flights-search/SKILL.md) | Experimental Weft-powered flight research with route, schedule, fare, nearby-airport, and ground-transfer evidence. | Experimental outcome workflow |
| [`weft-gtm-lead-enrichment`](skills/weft-gtm-lead-enrichment/SKILL.md) | Enrich a LinkedIn profile, find or verify a work email, or retrieve a social newsfeed through OneShot Agent. | Optional workflow; experimental |

Each skill also has a README with its reproducible benchmark status:

- [`weft`](skills/weft/README.md)
- [`weft-setup`](skills/weft-setup/README.md)
- [`weft-flights-search`](skills/weft-flights-search/README.md)
- [`weft-gtm-lead-enrichment`](skills/weft-gtm-lead-enrichment/README.md)

## Install

```sh
npx skills add weft-labs/skills --skill weft --skill weft-setup
```

Install an optional workflow separately:

```sh
npx skills add weft-labs/skills --skill weft-flights-search
npx skills add weft-labs/skills --skill weft-gtm-lead-enrichment
```

Use the space-separated `--skill <name>` form. Do not use
`--skill=<name>`; affected Skills CLI versions can ignore that filter and
install every skill in the repository.

Each optional workflow also owns a `1600x900` `cover.webp` beside its
`SKILL.md`. The public repository contains the finished cover, not Weft's
internal mascot source or generation workflow. Core skills do not appear in the
gallery and do not need a cover.

Or point an agent at the hosted copies:

- Setup (start here): `https://weft.network/setup.md`
- Usage: `https://weft.network/skills/weft/SKILL.md`

## Benchmarks

The benchmark runner compares the same task and model in two clean rooms:
without Weft and with the selected Weft skill. It reports only three headline
dimensions: end-to-end time, full-task accomplishment rate, and total agent
tokens. Authentication, unavailable models, timeouts, and missing token
telemetry are excluded and reported. They do not count as task failures.
Each skill README embeds an evidence plot at `benchmarks/chart.svg`. A measured
plot shows every valid paired time and token observation, medians, exact
accomplishments with 95% Wilson intervals, paired outcome changes, sample size,
exclusions, and the exact harness version. Before a complete benchmark is
published, that plot is blank and shows an explicit unmeasured state.

Run one manifest on any supported harness and model:

```sh
python3 scripts/benchmark.py run \
  --manifest skills/weft-setup/benchmarks/manifest.json \
  --target codex:gpt-5.6-sol \
  --target pi:opencode/deepseek-v4-pro \
  --out benchmark-results/weft-setup
```

Use `--dry-run` to inspect both commands without calling a model. A manifest
can select other Codex or Pi model identifiers. See the
[benchmark specification](docs/specs/skill-benchmark-runner-v0.md) and
[architecture](docs/architecture/skill-benchmark-runner.md).

After you inspect and move a complete result below the skill directory, publish
its verified README table and SVG chart:

```sh
python3 scripts/benchmark.py publish \
  --manifest skills/weft-setup/benchmarks/manifest.json \
  --summary skills/weft-setup/benchmarks/results/<run>/summary.json \
  --readme skills/weft-setup/README.md
```

## Distribution

| Mirror | Mechanism |
|---|---|
| `weft.network/setup.md` + `/skills/weft/SKILL.md` | vendored into `weft-app` at its `SKILLS_REF` commit, drift-checked in its CI |
| Claude plugin `weft-labs/weft-claude-plugin` | vendors `skills/weft/` at its `SKILLS_REF` commit, drift-checked in its CI |
| `@weft-labs/cli` npm package | bundles `skills/weft/` at its `SKILLS_REF` commit, drift-checked in its CI |

## License

MIT
