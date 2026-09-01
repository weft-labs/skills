#!/usr/bin/env python3
"""Validate skill frontmatter (real YAML, not line positions) and local links."""

import json
import pathlib
import re
import struct
import sys

import yaml

root = pathlib.Path(__file__).resolve().parent.parent
errors = []
names = {}

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
    text = path.read_text()
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

    # V0 protects the executable artifacts introduced by weft-seo. A
    # gallery-wide contract can generalize this after legacy workflows have
    # the same files.
    if name == "weft-seo":
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
        if not prompts_path.is_file():
            errors.append(
                f"{prompts_path.relative_to(root)}: weft-seo missing starter prompts"
            )
        else:
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
                elif (
                    not isinstance(prompts_document["prompts"], list)
                    or not prompts_document["prompts"]
                ):
                    errors.append(f"{prompts_rel}: prompts must be a non-empty list")
                elif len(prompts_document["prompts"]) > 4:
                    errors.append(f"{prompts_rel}: prompts cannot contain more than 4 entries")
                else:
                    for index, prompt in enumerate(prompts_document["prompts"]):
                        entry = f"{prompts_rel}: prompts[{index}]"
                        if not isinstance(prompt, dict) or set(prompt) != {
                            "title",
                            "prompt",
                        }:
                            errors.append(
                                f"{entry}: keys must be exactly `title` and `prompt`"
                            )
                            continue
                        title = prompt["title"]
                        body = prompt["prompt"]
                        if (
                            not isinstance(title, str)
                            or not title.strip()
                            or len(title) > 60
                        ):
                            errors.append(
                                f"{entry}: title must be a non-empty string of at most 60 characters"
                            )
                        if (
                            not isinstance(body, str)
                            or not body.strip()
                            or len(body) > 800
                        ):
                            errors.append(
                                f"{entry}: prompt must be a non-empty string of at most 800 characters"
                            )

        evals_path = path.parent / "evals/evals.json"
        if not evals_path.is_file():
            errors.append(f"{evals_path.relative_to(root)}: weft-seo missing evals")
        else:
            evals_rel = evals_path.relative_to(root)
            try:
                evals_document = json.loads(evals_path.read_text())
            except json.JSONDecodeError as exc:
                errors.append(f"{evals_rel}: not valid JSON: {exc}")
            else:
                if not isinstance(evals_document, dict):
                    errors.append(f"{evals_rel}: must be a JSON object")
                elif evals_document.get("skill_name") != name:
                    errors.append(f"{evals_rel}: skill_name must equal `{name}`")
                elif (
                    not isinstance(evals_document.get("evals"), list)
                    or not evals_document["evals"]
                ):
                    errors.append(f"{evals_rel}: evals must be a non-empty list")
                else:
                    seen_eval_ids = set()
                    required_eval_keys = {
                        "id",
                        "prompt",
                        "expected_output",
                        "files",
                        "expectations",
                    }
                    for index, item in enumerate(evals_document["evals"]):
                        entry = f"{evals_rel}: evals[{index}]"
                        if not isinstance(item, dict) or set(item) != required_eval_keys:
                            errors.append(f"{entry}: keys must match the eval schema")
                            continue
                        if not isinstance(item["id"], int) or item["id"] in seen_eval_ids:
                            errors.append(f"{entry}: id must be a unique integer")
                        else:
                            seen_eval_ids.add(item["id"])
                        if (
                            not isinstance(item["prompt"], str)
                            or not item["prompt"].strip()
                        ):
                            errors.append(f"{entry}: prompt must be a non-empty string")
                        if (
                            not isinstance(item["expected_output"], str)
                            or not item["expected_output"].strip()
                        ):
                            errors.append(
                                f"{entry}: expected_output must be a non-empty string"
                            )
                        if not isinstance(item["files"], list) or not all(
                            isinstance(value, str) for value in item["files"]
                        ):
                            errors.append(f"{entry}: files must be a list of strings")
                        else:
                            for value in item["files"]:
                                input_path = pathlib.Path(value)
                                skill_root = path.parent.resolve()
                                resolved_input = (skill_root / input_path).resolve()
                                try:
                                    resolved_input.relative_to(skill_root)
                                except ValueError:
                                    errors.append(
                                        f"{entry}: input file must stay inside the skill: `{value}`"
                                    )
                                    continue
                                if input_path.is_absolute():
                                    errors.append(
                                        f"{entry}: input file must be relative: `{value}`"
                                    )
                                elif not resolved_input.is_file():
                                    errors.append(
                                        f"{entry}: missing input file `{value}`"
                                    )
                        if (
                            not isinstance(item["expectations"], list)
                            or not item["expectations"]
                            or not all(
                                isinstance(value, str) and value.strip()
                                for value in item["expectations"]
                            )
                        ):
                            errors.append(
                                f"{entry}: expectations must be a non-empty list of strings"
                            )

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
    "skills/weft-seo/SKILL.md": [
        "never rely on a stored provider list or price",
        "typed inputs",
        "request bindings",
        "Choose the cheapest exact contract",
        "Copy its attribution fields",
        "`weft_balance` before the first paid fetch",
        "tight `max_cost_usd`",
        "Do not automatically retry any paid fetch",
        "paid_usd + held_usd",
        "Never request or forward wallet keys",
        "hard stop",
        "Do not claim durable idempotency",
    ],
}
for rel, phrases in REQUIRED_CONTENT.items():
    text = (root / rel).read_text()
    for phrase in phrases:
        if phrase.lower() not in text.lower():
            errors.append(f"{rel}: required safety phrase missing: `{phrase}`")

# Relative links in every markdown file must resolve.
for path in sorted(root.glob("skills/**/*.md")):
    rel = path.relative_to(root)
    for target in re.findall(r"\]\(([^)#]+?)(?:#[^)]*)?\)", path.read_text()):
        if re.match(r"[a-z]+:", target):  # absolute URL
            continue
        if not (path.parent / target).resolve().exists():
            errors.append(f"{rel}: broken relative link `{target}`")

if errors:
    print("\n".join(f"FAIL {e}" for e in errors))
    sys.exit(1)
print(f"ok: {len(skill_files)} skills, names: {', '.join(sorted(names))}")
