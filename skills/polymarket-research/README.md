# Polymarket Research

Create a cited, timestamped decision brief from a Polymarket link. The skill
separates settlement rules, live market state, outside evidence, and inference.
It is read-only and never places a trade.

## Install

```sh
npx skills add weft-labs/skills --skill polymarket-research
```

## Reproduce the benchmark

This is a narrow instruction-following benchmark on three frozen offline
dossiers: a conflicted current market, a historical cutoff, and an unresolved
market identity. It does not measure live research quality, source freshness,
probability calibration, forecast accuracy, trading performance, financial
returns, or paid-provider execution.

From the repository root:

```sh
python3 scripts/benchmark.py run --manifest skills/polymarket-research/benchmarks/manifest.json --target codex:gpt-5.6-sol --out benchmark-results/polymarket-research
```

Earlier methods-development runs were rejected after semantic-equivalence
checks found false negatives in the scorer. They are not part of the published
evidence. The published run started after the corrected scorer was frozen.

<!-- weft-benchmark:start -->
## Benchmark

**Claim scope:** Measures whether the model follows the committed Polymarket Research procedure on three frozen offline dossiers: a current conflicted market, a historical-cutoff request, and an unresolved market identity. It does not measure live web or API research, source freshness, probability calibration, forecast accuracy, trading performance, profitability, or paid-provider execution.

The same clean-room tasks run without the skill and with the skill. Results are descriptive paired observations; they do not establish causality or statistical significance. Headline metrics are maintainer-recorded harness process time, all committed checks passed, and total agent tokens.

The evidence writer redacts host paths, clean-room temporary paths, and opaque harness trace IDs from published native transcripts. Answers and token telemetry remain inspectable.

![Benchmark chart](benchmarks/chart.svg)

| Harness / model | Arm | Harness process time, median | All committed checks passed | Tokens, median | Complete / excluded pairs |
|---|---|---:|---:|---:|---:|
| Codex / `gpt-5.6-sol` | without weft | 24.362s | 66.7% | 19130 | 9 / 0 |
| Codex / `gpt-5.6-sol` | with weft | 28.58s | 66.7% | 38516 | 9 / 0 |
| Codex / `gpt-5.6-sol` | Observed difference | +4.218s | +0 pp | +19386 | — |

Actual repetitions per case: 3. Required complete pairs per target and case: 3. Excluded matched pairs: 0.
Measured: 2026-09-02T22:52:01Z. Skill digest: `9116abb6a401f568d4299b1255dc08e58ec049274e35a67d67f224aa594d683e`. Manifest digest: `9579330a74af97a46775a401f906e97b2d981266d3e3a84536834677931f9434`.
[Raw benchmark evidence](benchmarks/results/2026-09-03-codex-gpt56sol-three-case-v4/raw.json)
<!-- weft-benchmark:end -->
