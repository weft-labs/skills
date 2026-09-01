# Weft Flight Search

Research and compare flights, nearby airports, and ground transfers with Weft
evidence and public booking verification.

```sh
npx skills add weft-labs/skills --skill weft-flights-search
```

[Read the skill](SKILL.md)

Run its committed benchmark:

```sh
python3 scripts/benchmark.py run --manifest skills/weft-flights-search/benchmarks/manifest.json --target codex:gpt-5.6-sol --out benchmark-results/weft-flights-search
```

<!-- weft-benchmark:start -->
## Benchmark

**Status: Unmeasured.** No reproducible with-Weft versus without-Weft result has been published for this skill yet.
<!-- weft-benchmark:end -->
