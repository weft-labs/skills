#!/usr/bin/env python3
"""Validate skill frontmatter (real YAML, not line positions) and local links."""

import json
import pathlib
import re
import struct
import sys

import yaml

from benchmark import (
    BENCHMARK_CHART_PATH,
    load_manifest,
    render_benchmark_block,
    render_benchmark_chart,
    render_unmeasured_chart,
    verify_case_minimums,
    verify_publication,
)

root = pathlib.Path(__file__).resolve().parent.parent
errors = []
names = {}

CORE_SKILLS = {"weft", "weft-setup"}
COVER_WIDTH = 1600
COVER_HEIGHT = 900
COVER_MAX_BYTES = 750_000


def webp_dimensions(path):
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("not a WebP RIFF file")

    offset = 12
    while offset + 8 <= len(data):
        chunk_type = data[offset : offset + 4]
        chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
        payload = offset + 8
        if payload + chunk_size > len(data):
            raise ValueError("truncated WebP chunk")
        if chunk_type == b"VP8X" and chunk_size >= 10:
            width = int.from_bytes(data[payload + 4 : payload + 7], "little") + 1
            height = int.from_bytes(data[payload + 7 : payload + 10], "little") + 1
            return width, height
        if chunk_type == b"VP8 " and chunk_size >= 10:
            if data[payload + 3 : payload + 6] != b"\x9d\x01\x2a":
                raise ValueError("invalid VP8 frame header")
            width = struct.unpack_from("<H", data, payload + 6)[0] & 0x3FFF
            height = struct.unpack_from("<H", data, payload + 8)[0] & 0x3FFF
            return width, height
        if chunk_type == b"VP8L" and chunk_size >= 5:
            if data[payload] != 0x2F:
                raise ValueError("invalid VP8L frame header")
            bits = int.from_bytes(data[payload + 1 : payload + 5], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        offset = payload + chunk_size + (chunk_size % 2)

    raise ValueError("WebP image chunk not found")

skill_files = sorted(root.glob("skills/*/SKILL.md"))
if not skill_files:
    errors.append("no skills/*/SKILL.md files found")

for path in skill_files:
    rel = path.relative_to(root)
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        errors.append(f"{rel}: missing YAML frontmatter block")
        continue
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"{rel}: frontmatter is not valid YAML: {exc}")
        continue
    if not isinstance(meta, dict):
        errors.append(f"{rel}: frontmatter must be a YAML mapping")
        continue
    name = meta.get("name")
    description = meta.get("description")
    if not name:
        errors.append(f"{rel}: frontmatter missing `name`")
    elif name != path.parent.name:
        errors.append(f"{rel}: name `{name}` != directory `{path.parent.name}`")
    elif name in names:
        errors.append(f"{rel}: duplicate name `{name}` (also {names[name]})")
    else:
        names[name] = rel
    if not description or not str(description).strip():
        errors.append(f"{rel}: frontmatter missing `description`")

    if name and name not in CORE_SKILLS:
        cover_path = path.parent / "cover.webp"
        cover_rel = cover_path.relative_to(root)
        if not cover_path.is_file():
            errors.append(f"{cover_rel}: optional skill missing `cover.webp`")
        else:
            try:
                dimensions = webp_dimensions(cover_path)
            except ValueError as exc:
                errors.append(f"{cover_rel}: {exc}")
            else:
                if dimensions != (COVER_WIDTH, COVER_HEIGHT):
                    errors.append(
                        f"{cover_rel}: dimensions {dimensions[0]}x{dimensions[1]} "
                        f"!= {COVER_WIDTH}x{COVER_HEIGHT}"
                    )
            if cover_path.stat().st_size > COVER_MAX_BYTES:
                errors.append(
                    f"{cover_rel}: {cover_path.stat().st_size} bytes exceeds "
                    f"{COVER_MAX_BYTES}"
                )

        prompts_path = path.parent / "examples/starter-prompts.yml"
        if prompts_path.exists():
            prompts_rel = prompts_path.relative_to(root)
            try:
                prompts_document = yaml.safe_load(prompts_path.read_text())
            except yaml.YAMLError as exc:
                errors.append(f"{prompts_rel}: not valid YAML: {exc}")
            else:
                if not isinstance(prompts_document, dict):
                    errors.append(f"{prompts_rel}: must be a YAML mapping")
                elif set(prompts_document) != {"version", "prompts"}:
                    errors.append(f"{prompts_rel}: keys must be exactly `version` and `prompts`")
                elif prompts_document["version"] != 1:
                    errors.append(f"{prompts_rel}: version must be 1")
                elif not isinstance(prompts_document["prompts"], list) or not prompts_document["prompts"]:
                    errors.append(f"{prompts_rel}: prompts must be a non-empty list")
                elif len(prompts_document["prompts"]) > 4:
                    errors.append(f"{prompts_rel}: prompts cannot contain more than 4 entries")
                else:
                    for index, prompt in enumerate(prompts_document["prompts"]):
                        entry = f"{prompts_rel}: prompts[{index}]"
                        if not isinstance(prompt, dict) or set(prompt) != {"title", "prompt"}:
                            errors.append(f"{entry}: keys must be exactly `title` and `prompt`")
                            continue
                        title = prompt["title"]
                        body = prompt["prompt"]
                        if not isinstance(title, str) or not title.strip() or len(title) > 60:
                            errors.append(f"{entry}: title must be a non-empty string of at most 60 characters")
                        if not isinstance(body, str) or not body.strip() or len(body) > 800:
                            errors.append(f"{entry}: prompt must be a non-empty string of at most 800 characters")
    readme = path.parent / "README.md"
    if not readme.is_file():
        errors.append(f"{readme.relative_to(root)}: missing skill README")
    else:
        readme_text = readme.read_text(encoding="utf-8")
        start = "<!-- weft-benchmark:start -->"
        end = "<!-- weft-benchmark:end -->"
        if readme_text.count(start) != 1 or readme_text.count(end) != 1:
            errors.append(
                f"{readme.relative_to(root)}: benchmark markers must occur exactly once"
            )
        elif readme_text.index(start) > readme_text.index(end):
            errors.append(f"{readme.relative_to(root)}: benchmark markers are reversed")
        else:
            block = readme_text.split(start, 1)[1].split(end, 1)[0]
            chart = re.search(r"!\[Benchmark (?:chart|status)\]\(([^)]+)\)", block)
            chart_path = None
            if not chart:
                errors.append(
                    f"{readme.relative_to(root)}: benchmark has no chart image"
                )
            elif chart.group(1) != BENCHMARK_CHART_PATH:
                errors.append(
                    f"{readme.relative_to(root)}: benchmark chart must use `{BENCHMARK_CHART_PATH}`"
                )
            else:
                chart_path = readme.parent / BENCHMARK_CHART_PATH
            measured = all(
                term in block
                for term in (
                    "Time",
                    "Accomplishment rate",
                    "Tokens",
                    "Raw benchmark evidence",
                )
            )
            unmeasured = "Status: Unmeasured" in block
            if measured == unmeasured:
                errors.append(
                    f"{readme.relative_to(root)}: benchmark must be either measured with evidence or explicitly unmeasured"
                )
            elif measured:
                evidence = re.search(r"\[Raw benchmark evidence\]\(([^)]+)\)", block)
                if not evidence:
                    errors.append(
                        f"{readme.relative_to(root)}: measured benchmark has no raw evidence link"
                    )
                else:
                    raw_path = (readme.parent / evidence.group(1)).resolve()
                    try:
                        raw_path.relative_to(readme.parent.resolve())
                    except ValueError:
                        errors.append(
                            f"{readme.relative_to(root)}: raw benchmark evidence escapes the skill directory"
                        )
                    else:
                        summary_path = raw_path.with_name("summary.json")
                        try:
                            raw = json.loads(raw_path.read_text(encoding="utf-8"))
                            summary = json.loads(
                                summary_path.read_text(encoding="utf-8")
                            )
                            manifest_payload = load_manifest(
                                path.parent / "benchmarks" / "manifest.json", root
                            )
                            verify_publication(
                                summary,
                                raw,
                                manifest_payload,
                                root,
                                summary_path.parent,
                            )
                            verify_case_minimums(summary)
                            expected = render_benchmark_block(
                                summary, evidence.group(1)
                            )
                            if block.strip() != expected.strip():
                                errors.append(
                                    f"{readme.relative_to(root)}: measured benchmark block differs from evidence"
                                )
                            if chart_path is not None:
                                expected_chart = render_benchmark_chart(summary, raw)
                                try:
                                    actual_chart = chart_path.read_text(
                                        encoding="utf-8"
                                    )
                                except OSError as exc:
                                    errors.append(
                                        f"{chart_path.relative_to(root)}: missing benchmark chart: {exc}"
                                    )
                                else:
                                    if actual_chart != expected_chart:
                                        errors.append(
                                            f"{chart_path.relative_to(root)}: measured chart differs from evidence"
                                        )
                        except (OSError, ValueError) as exc:
                            errors.append(
                                f"{readme.relative_to(root)}: invalid benchmark evidence: {exc}"
                            )
            elif unmeasured and chart_path is not None:
                try:
                    actual_chart = chart_path.read_text(encoding="utf-8")
                except OSError as exc:
                    errors.append(
                        f"{chart_path.relative_to(root)}: missing benchmark chart: {exc}"
                    )
                else:
                    if actual_chart != render_unmeasured_chart():
                        errors.append(
                            f"{chart_path.relative_to(root)}: unmeasured chart is stale"
                        )

    manifest = path.parent / "benchmarks" / "manifest.json"
    if not manifest.is_file():
        errors.append(f"{manifest.relative_to(root)}: missing benchmark manifest")
    else:
        try:
            payload = load_manifest(manifest, root)
            if payload["skill"] != path.parent.name:
                errors.append(
                    f"{manifest.relative_to(root)}: skill `{payload['skill']}` != directory `{path.parent.name}`"
                )
        except ValueError as exc:
            errors.append(f"{manifest.relative_to(root)}: {exc}")

# Safety-content invariants: these phrases are load-bearing (spending
# safety, secret handling). A rewrite that drops one is a regression, not
# a style choice — see cto-os/directives/agent-skills-distribution.md.
REQUIRED_CONTENT = {
    "skills/weft/SKILL.md": [
        "max_cost_usd",
        "paid_usd + held_usd",
        "`weft_balance` before the first paid fetch",
        "Do not retry a paid call",
        "Do not automatically retry any paid fetch",
        "Never request or forward wallet keys",
        "hard stop",
        "Do not claim durable idempotency",
    ],
    "skills/weft/rules/cli.md": [
        "--max-cost-usd",
        "mode-0600",
        "Never echo any credential",
        "Never ask",
    ],
    "skills/weft-setup/SKILL.md": [
        "never print, echo, log, or paste",
        "Never ask for, accept, generate, or store a password",
        "promotional balance",
        "do not add a second manual",
    ],
}
for rel, phrases in REQUIRED_CONTENT.items():
    text = (root / rel).read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase.lower() not in text.lower():
            errors.append(f"{rel}: required safety phrase missing: `{phrase}`")

# Relative links in every markdown file must resolve.
for path in sorted(root.glob("skills/**/*.md")):
    rel = path.relative_to(root)
    for target in re.findall(
        r"\]\(([^)#]+?)(?:#[^)]*)?\)", path.read_text(encoding="utf-8")
    ):
        if re.match(r"[a-z]+:", target):  # absolute URL
            continue
        if not (path.parent / target).resolve().exists():
            errors.append(f"{rel}: broken relative link `{target}`")

if errors:
    print("\n".join(f"FAIL {e}" for e in errors))
    sys.exit(1)
print(f"ok: {len(skill_files)} skills, names: {', '.join(sorted(names))}")
