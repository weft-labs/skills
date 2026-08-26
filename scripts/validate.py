#!/usr/bin/env python3
"""Validate skill frontmatter (real YAML, not line positions) and local links."""

import pathlib
import re
import sys

import yaml

root = pathlib.Path(__file__).resolve().parent.parent
errors = []
names = {}

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
