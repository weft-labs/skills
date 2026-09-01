# Weft GTM Lead Enrichment

Run OneShot Agent enrichment, email verification, and social-newsfeed jobs with
safe payment and result recovery.

```sh
npx skills add weft-labs/skills --skill weft-gtm-lead-enrichment
```

[Read the skill](SKILL.md)

Run its committed benchmark:

```sh
python3 scripts/benchmark.py run --manifest skills/weft-gtm-lead-enrichment/benchmarks/manifest.json --target codex:gpt-5.6-sol --out benchmark-results/weft-gtm-lead-enrichment
```

<!-- weft-benchmark:start -->
## Benchmark

**Status: Unmeasured.** No reproducible with-Weft versus without-Weft result has been published for this skill yet.
<!-- weft-benchmark:end -->
