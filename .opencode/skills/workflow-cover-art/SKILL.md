---
name: workflow-cover-art
description: Create or replace a repository-owned workflow cover through Weft. Use when adding an optional public workflow, preparing gallery artwork, refreshing a skill cover, or when a skills PR changes `skills/<name>/cover.webp`.
---

# Workflow Cover Art

Create one precise gallery cover for an optional workflow. The committed asset
is `skills/<name>/cover.webp`; it is visual content, not gallery metadata.

Load the `weft` skill before any provider discovery or paid request. Its wallet,
cost-cap, receipt, and no-ambiguous-retry rules are authoritative.

## Inputs

- The target optional skill directory.
- Its standard `name` and `description` frontmatter.
- An optional art-direction note from the reviewer.

Core skills `weft` and `weft-setup` are excluded. Stop if the target is either
name or if its frontmatter does not validate.

## Visual Contract

- Output: WebP, exactly `1600x900`, at most 750 KB.
- No words, letters, numbers, logos, brand marks, UI screenshots, or people.
- Show the workflow's outcome as one clear abstract mechanism, not a literal
  stock-photo subject.
- Use the Weft cover family: cloud white, mineral blue, cool slate, and
  graphite. Rust can mark one meaningful signal only; it is not decoration.
- Prefer crisp paper-cut, screenprint, diagram, or field-guide material. Avoid
  glossy 3D, neon, blurred photography, generic gradients, and AI fantasy art.
- Keep useful negative space so the cover survives responsive crops.

## Required Flow

### 1. Read the workflow

Read `SKILL.md`. Reduce its outcome to a visual sentence with one subject, one
transformation, and one result. Examples:

- flight search: two terminal nodes joined by one route arc;
- lead enrichment: one source node resolving into verified connections.

Do not put the workflow name in the image. The card supplies the text.

### 2. Discover a provider through Weft

Call `weft_search` for a text-to-image API that supports a landscape aspect and
returns image bytes, base64, or a downloadable URL. Prefer the cheapest valid
operation. Read its current request schema and live price; do not rely on a
provider name or endpoint recorded in this file.

Before the first paid call, call `weft_balance`. State the expected maximum
cost. Use a tight `max_cost_usd` equal to the selected operation's current
single-image price. If the merchant returns an exact pre-payment price refusal,
report the corrected price before deciding whether to submit once at that cap.

### 3. Generate once

Request one `16:9` image. Include the Visual Contract and the workflow's visual
sentence in the prompt. Set one output and a fixed seed when the provider
supports them.

Preserve the full Weft receipt. Do not repeat a paid generation after a timeout,
decoder failure, missing body, or other ambiguous response. A clear pre-payment
refusal is not a charge and can be corrected once.

When the response contains `body_base64`, decode the JSON in memory and extract
the generated image URL. Download that URL immediately in the same operation;
temporary provider URLs can expire. Never log credentials or persist a signed
download URL in the repository.

### 4. Inspect and normalize

View the generated image at full resolution. Reject it if it contains forbidden
text or marks, a misleading literal claim, an unclear focal mechanism, or a
style outside the Visual Contract. Do not silently buy a replacement. Report
the problem and wait for reviewer direction before another paid request.

Use `cwebp` for format conversion and resizing when available:

```sh
cwebp -quiet -q 86 -resize 1600 900 input.png -o skills/<name>/cover.webp
```

Do not stretch a non-landscape composition. Generate the correct aspect instead.

### 5. Validate and report

Run:

```sh
python3 scripts/validate.py
```

Report the provider and operation, paid plus held USD, transaction hash when
available, seed when available, output path, dimensions, byte size, and visual
inspection result. Do not commit provider URLs, wallet addresses, credentials,
or receipt bodies.

## Stop Conditions

- The target is a core skill.
- Frontmatter is invalid or the workflow outcome is unclear.
- No Weft-discovered provider supports the required image result.
- The wallet or spending policy refuses the planned cost.
- A paid result is ambiguous or the generated image fails inspection.
