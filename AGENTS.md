# Weft Skills

Canonical customer-facing Weft skills. Read [README](README.md) for the skill
map, installation and distribution contract.

- `skills/` owns the skill source; consumers carry byte-identical mirrors
  pinned with `SKILLS_REF`. Change this repo before updating consumers.
- Read the affected `SKILL.md` and its referenced rules before editing a
  workflow. Preserve the distinction between durable usage and one-shot setup.
- Do not add credentials, funded keys or customer data to examples.
- Inspect `.github/workflows/` for current validation; do not invent a test
  command or publish a release as part of a prose change.

## Workflow and context

Use an isolated Git worktree for changes. Product changes use PRs based on
`main`; native stack layers target their parent. Keep configured hooks enabled
and required checks passing. Patrick owns the merge gate.

Start with README.md for setup, usage, and documentation.
