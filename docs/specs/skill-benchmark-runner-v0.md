---
id: skill-benchmark-runner-v0
status: active
depends-on: []
---

# Skill Benchmark Runner V0

## Goal

Add one stdlib Python command that can run a committed skill benchmark on Codex
or Pi with a user-selected model and compare `without_weft` with `with_weft`.

## Files To Touch

- `scripts/benchmark.py`
- `scripts/validate.py`
- `tests/test_benchmark.py`
- `tests/fixtures/benchmark/`
- `docs/architecture/skill-benchmark-runner.md`
- `docs/specs/skill-benchmark-runner-v0.md`
- `README.md`
- `skills/*/README.md`

## Command Contract

```sh
python3 scripts/benchmark.py run \
  --manifest skills/<name>/benchmarks/manifest.json \
  --target codex:gpt-5.6-sol \
  --target pi:opencode/deepseek-v4-pro

python3 scripts/benchmark.py publish \
  --manifest skills/<name>/benchmarks/manifest.json \
  --summary skills/<name>/benchmarks/results/<run>/summary.json \
  --readme skills/<name>/README.md
```

`--dry-run` prints the clean-room commands without calling a model. `--only`
limits case IDs. `--repetitions` can increase, but not reduce, the committed
manifest minimum. `--out` must be a new or empty directory so evidence is not
silently overwritten or mixed with an older run.

## Manifest Contract

The JSON manifest contains:

- version and skill name;
- a plain-language claim scope that states what the benchmark does and does not
  measure;
- one or more skill directories loaded only in `with_weft`;
- minimum repetitions;
- paid-action policy, which must be false in V0;
- cases with ID, prompt, optional fixtures, regular-expression checks, and
  independent truth provenance.

Fixture files must be below `fixtures/`. Codex receives them as clean-room files;
Pi receives the same path and content in its task prompt because Pi tools are
disabled. The runner rejects duplicate case IDs,
missing skills, empty checks, missing truth provenance, other fixture paths,
path escapes, and paid-enabled manifests.

## Required Behavior

- Permit real runs only on POSIX hosts. Keep dry-run planning cross-platform.
- Snapshot the complete skill execution tree once before any measured run.
- Create a separate temporary clean room per target, case, arm, and repetition.
- Keep harness and model fixed across paired arms.
- Load no Weft skill in `without_weft`; load the manifest skill set in
  `with_weft`.
- Save the raw harness stream and final answer for each run.
- Capture wall time and native total tokens. Pi totals include input, output,
  cache-read, and cache-write categories exactly once. Missing tokens exclude
  the run.
- Mark accomplishment true only when every committed check passes.
- Exclude environment and harness failures from the denominator and publish
  their counts and reasons.
- Aggregate median time, accomplishment rate, and median tokens by target and
  arm. Do not publish assertion percentage as accomplishment.
- Generate a deterministic README block and SVG evidence plot from verified raw
  paired runs and their complete summary.
- Recompute the summary from its sibling raw evidence before publication and
  reject partial-case runs, changed aggregates, stale skill or manifest files,
  or evidence outside the skill.
- Reread every final answer, re-run current manifest checks, and require the
  manifest repetition minimum for every target and every case.
- Run Pi with no tools and identical explicit base prompts in both arms. Add
  immutable text skill instructions only for `with_weft`.
- Give each Pi run a clean agent directory containing only copied
  authentication. Do not load global settings, model overrides, sessions, or
  packages. Require exact `provider/model` Pi target identifiers.
- Run Codex with a strict deny-root permission profile. Allow only minimal
  runtime reads and clean-room read/write access. Disable hosted web search and
  do not inherit the caller's environment into model shell commands.
- Pass only required runtime, harness configuration, and provider authentication
  variables to the harness process. Do not copy the full caller environment.

## Per-skill README Contract

Every `skills/*/README.md` has a marker-bounded `Benchmark` section and embeds
`benchmarks/chart.svg`. Until a complete result is committed, the README and
plot say `Status: Unmeasured`; the plot is blank and must not use decorative
marks that resemble observations. A measured plot compares `without_weft` with
`with_weft` for time, accomplishment rate, and tokens. It shows:

- every valid paired observation for time and tokens, with the same case and
  repetition connected across arms;
- median markers for time and tokens;
- exact accomplishments over valid runs and 95% Wilson intervals for each arm;
- paired accomplishment transitions, valid pair count, exclusions, exact
  harness/model version, case count, and measurement time.

The README states the manifest claim scope and calls each delta an observed
difference, not an impact. It makes no causal, statistical-significance,
forecast-accuracy, or financial-return claim. A measured block also names the
repetitions, skill digest, manifest digest, date, and raw-result path.
Publication writes both artifacts, and validation reproduces both from the
committed raw evidence.

## Acceptance

1. Unit tests fail before the runner exists and pass after implementation.
2. Dry-run shows paired Codex GPT-5.6-sol and Pi DeepSeek V4 Pro commands.
3. Fixture executions prove success, failure, missing-token, timeout, and
   authentication-error classification without live model calls.
4. Every current skill has a benchmark README section with a visible SVG chart.
5. Independent review finds no P0/P1 correctness, measurement, command-injection,
   credential, or misleading-publication defect.

## Acceptance Commands

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate.py
python3 scripts/benchmark.py run --manifest tests/fixtures/benchmark/manifest.json --target codex:gpt-5.6-sol --target pi:opencode/deepseek-v4-pro --dry-run
```
