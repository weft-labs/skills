#!/usr/bin/env python3
"""Run reproducible with-Weft versus without-Weft skill benchmarks."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import pathlib
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
ARMS = ("without_weft", "with_weft")
SUPPORTED_HARNESSES = ("codex", "pi")
START_MARKER = "<!-- weft-benchmark:start -->"
END_MARKER = "<!-- weft-benchmark:end -->"
CODEX_DISABLED_FEATURES = (
    "apps",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "image_generation",
    "multi_agent",
    "multi_agent_v2",
    "plugins",
    "skill_search",
    "standalone_web_search",
)
PI_SYSTEM_PROMPT = (
    "You are a benchmark task agent. Follow the user task exactly. "
    "No tools are available."
)
PI_COMMON_APPEND_PROMPT = (
    "Benchmark isolation is active. Use only the task input and explicit "
    "benchmark skill bundle."
)
PI_TASK_ARGUMENT_PREFIX = "Benchmark task input follows.\n\n"
COMMON_HARNESS_ENVIRONMENT_NAMES = (
    "PATH",
    "HOME",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "no_proxy",
)
CODEX_ENVIRONMENT_NAMES = (
    "CODEX_HOME",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_BASE_URL",
    "AZURE_OPENAI_RESOURCE_NAME",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_DEPLOYMENT_NAME_MAP",
)
PI_ENVIRONMENT_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_OAUTH_TOKEN",
    "COPILOT_GITHUB_TOKEN",
    "ANT_LING_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_BASE_URL",
    "AZURE_OPENAI_RESOURCE_NAME",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_DEPLOYMENT_NAME_MAP",
    "DEEPSEEK_API_KEY",
    "NVIDIA_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "XAI_API_KEY",
    "FIREWORKS_API_KEY",
    "TOGETHER_API_KEY",
    "BASETEN_API_KEY",
    "OPENROUTER_API_KEY",
    "AI_GATEWAY_API_KEY",
    "ZAI_API_KEY",
    "ZAI_CODING_CN_API_KEY",
    "MISTRAL_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_CN_API_KEY",
    "MOONSHOT_API_KEY",
    "OPENCODE_API_KEY",
    "KIMI_API_KEY",
    "CLOUDFLARE_API_KEY",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_GATEWAY_ID",
    "QWEN_TOKEN_PLAN_API_KEY",
    "QWEN_TOKEN_PLAN_CN_API_KEY",
    "XIAOMI_API_KEY",
    "XIAOMI_TOKEN_PLAN_CN_API_KEY",
    "XIAOMI_TOKEN_PLAN_AMS_API_KEY",
    "XIAOMI_TOKEN_PLAN_SGP_API_KEY",
    "AWS_PROFILE",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AWS_CONTAINER_CREDENTIALS_FULL_URI",
    "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_CLOUD_QUOTA_PROJECT",
)


@dataclasses.dataclass(frozen=True)
class Target:
    harness: str
    model: str

    @property
    def label(self) -> str:
        return f"{self.harness}:{self.model}"


class UnsupportedSkillAssetError(ValueError):
    """A harness cannot load one file from the skill execution snapshot."""


class MalformedHarnessOutputError(ValueError):
    """A nonempty harness output record is not valid JSON."""


@dataclasses.dataclass
class RunResult:
    harness: str
    model: str
    case_id: str
    arm: str
    repetition: int
    duration_seconds: float
    total_tokens: int | None
    accomplished: bool | None
    answer: str | None
    checks: list[dict]
    exclusion: str | None
    exit_code: int | None
    run_path: str

    @classmethod
    def fixture(
        cls,
        harness: str,
        model: str,
        case_id: str,
        arm: str,
        repetition: int,
        duration_seconds: float,
        total_tokens: int | None,
        accomplished: bool | None,
        exclusion: str | None = None,
        answer: str | None = "fixture answer",
        run_path: str = "",
    ) -> "RunResult":
        return cls(
            harness=harness,
            model=model,
            case_id=case_id,
            arm=arm,
            repetition=repetition,
            duration_seconds=duration_seconds,
            total_tokens=total_tokens,
            accomplished=accomplished,
            answer=answer,
            checks=[],
            exclusion=exclusion,
            exit_code=0 if exclusion is None else None,
            run_path=run_path,
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def validate_generated_at(value: object) -> None:
    if not isinstance(value, str):
        raise ValueError("benchmark evidence requires a UTC generated_at timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError(
            "benchmark evidence requires a UTC generated_at timestamp"
        ) from exc


def parse_target(value: str) -> Target:
    if ":" not in value:
        raise ValueError("target must use <harness>:<model>")
    harness, model = value.split(":", 1)
    if harness not in SUPPORTED_HARNESSES:
        raise ValueError(f"supported harness values: {', '.join(SUPPORTED_HARNESSES)}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:+-]*", model):
        raise ValueError(
            "model must be a safe identifier using letters, numbers, and ._/@:+-"
        )
    if harness == "pi" and not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._@:+-]*/[A-Za-z0-9][A-Za-z0-9._/@:+-]*",
        model,
    ):
        raise ValueError("Pi model must use an exact <provider>/<model> identifier")
    return Target(harness=harness, model=model)


def relative_path(value: str, field: str) -> pathlib.Path:
    path = pathlib.Path(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not value
        or path == pathlib.Path(".")
    ):
        raise ValueError(f"{field} must be a non-empty relative path without `..`")
    return path


def contained_path(root: pathlib.Path, value: str, field: str) -> pathlib.Path:
    path = root / relative_path(value, field)
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} resolves outside the repository") from exc
    return path


def validate_manifest(payload: dict, repo_root: pathlib.Path = ROOT) -> dict:
    if isinstance(payload.get("version"), bool) or payload.get("version") != 1:
        raise ValueError("manifest version must be 1")
    if not isinstance(payload.get("skill"), str) or not payload["skill"].strip():
        raise ValueError("manifest skill must be a non-empty string")
    skills = payload.get("skills")
    if not isinstance(skills, list) or not skills:
        raise ValueError("manifest skills must contain at least one skill directory")
    seen_skill_paths: set[pathlib.Path] = set()
    seen_skill_names: set[str] = set()
    for index, value in enumerate(skills):
        if not isinstance(value, str):
            raise ValueError(f"skills[{index}] must be a relative path string")
        skill_path = contained_path(repo_root, value, f"skills[{index}]")
        if skill_path.resolve() in seen_skill_paths:
            raise ValueError(f"duplicate skill directory: {value}")
        seen_skill_paths.add(skill_path.resolve())
        skill_name = portable_path_key(skill_path.name)
        if skill_name in seen_skill_names:
            raise ValueError(
                f"skill directories must have unique names: {skill_path.name}"
            )
        seen_skill_names.add(skill_name)
        if not (skill_path / "SKILL.md").is_file():
            raise ValueError(f"skills[{index}] does not contain SKILL.md: {value}")
        for item in skill_path.rglob("*"):
            if item.is_symlink():
                raise ValueError(
                    f"skills[{index}] contains a symlink: {item.relative_to(skill_path)}"
                )
            if not item.is_file():
                continue
    repetitions = payload.get("minimum_repetitions")
    if (
        isinstance(repetitions, bool)
        or not isinstance(repetitions, int)
        or repetitions < 1
    ):
        raise ValueError("minimum_repetitions must be a positive integer")
    paid = payload.get("paid_actions", {})
    if not isinstance(paid, dict):
        raise ValueError("paid_actions must be an object")
    if "enabled" in paid and paid["enabled"] is not False:
        raise ValueError("paid actions are not supported by the V0 benchmark runner")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest cases must contain at least one case")
    ids: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}] must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]*", case_id
        ):
            raise ValueError(f"cases[{index}].id must use lowercase kebab-case")
        if case_id in ids:
            raise ValueError(f"duplicate case id: {case_id}")
        ids.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"cases[{index}].prompt must be non-empty")
        provenance = case.get("truth_provenance")
        if not isinstance(provenance, str) or not provenance.strip():
            raise ValueError(f"cases[{index}].truth_provenance must be non-empty")
        checks = case.get("checks")
        if not isinstance(checks, list) or not checks:
            raise ValueError(f"cases[{index}].checks must contain at least one check")
        check_ids: set[str] = set()
        for check_index, check in enumerate(checks):
            if not isinstance(check, dict):
                raise ValueError(
                    f"cases[{index}].checks[{check_index}] must be an object"
                )
            check_id = check.get("id")
            if not isinstance(check_id, str) or not check_id:
                raise ValueError(
                    f"cases[{index}].checks[{check_index}].id must be non-empty"
                )
            if check_id in check_ids:
                raise ValueError(f"duplicate check id in {case_id}: {check_id}")
            check_ids.add(check_id)
            pattern = check.get("pattern")
            if not isinstance(pattern, str) or not pattern:
                raise ValueError(
                    f"cases[{index}].checks[{check_index}].pattern must be non-empty"
                )
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(
                    f"invalid regex for {case_id}/{check_id}: {exc}"
                ) from exc
        fixtures = case.get("fixtures", [])
        if not isinstance(fixtures, list):
            raise ValueError(f"cases[{index}].fixtures must be a list")
        fixture_paths: set[tuple[str, ...]] = set()
        for fixture_index, fixture in enumerate(fixtures):
            if (
                not isinstance(fixture, dict)
                or not isinstance(fixture.get("path"), str)
                or not isinstance(fixture.get("content"), str)
            ):
                raise ValueError(
                    f"cases[{index}].fixtures[{fixture_index}] requires path and string content"
                )
            fixture_path = relative_path(
                fixture.get("path", ""),
                f"cases[{index}].fixtures[{fixture_index}].path",
            )
            if (
                not fixture_path.parts
                or fixture_path.parts[0] != "fixtures"
                or len(fixture_path.parts) < 2
            ):
                raise ValueError(
                    f"cases[{index}].fixtures[{fixture_index}].path must be below fixtures/"
                )
            fixture_key = tuple(portable_path_key(part) for part in fixture_path.parts)
            if fixture_key in fixture_paths:
                raise ValueError(f"duplicate fixture path in {case_id}: {fixture_path}")
            if any(
                fixture_key[: len(existing)] == existing
                or existing[: len(fixture_key)] == fixture_key
                for existing in fixture_paths
            ):
                raise ValueError(f"fixture path collision in {case_id}: {fixture_path}")
            fixture_paths.add(fixture_key)
    return payload


def load_manifest(path: pathlib.Path, repo_root: pathlib.Path = ROOT) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be an object")
    return validate_manifest(payload, repo_root)


def canonical_digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def skill_sources_digest(manifest: dict, sources: dict[str, pathlib.Path]) -> str:
    digest = hashlib.sha256()
    for skill_value in sorted(manifest["skills"]):
        skill_path = sources[skill_value]
        for path in skill_execution_files(skill_path):
            logical_path = pathlib.Path(skill_value) / path.relative_to(skill_path)
            digest.update(logical_path.as_posix().encode())
            digest.update(b"\0")
            digest.update(b"x" if path.stat().st_mode & 0o111 else b"-")
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def skill_tree_digest(manifest: dict, repo_root: pathlib.Path = ROOT) -> str:
    sources = {
        value: repo_root / relative_path(value, "skill") for value in manifest["skills"]
    }
    return skill_sources_digest(manifest, sources)


def skill_execution_files(skill_path: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        path
        for path in skill_path.rglob("*")
        if path.is_file()
        and path != skill_path / "README.md"
        and skill_path / "benchmarks" not in path.parents
    )


def copy_skill_execution_tree(source: pathlib.Path, destination: pathlib.Path) -> None:
    def ignore(path: str, names: list[str]) -> set[str]:
        return {
            name
            for name in ("README.md", "benchmarks")
            if pathlib.Path(path) == source and name in names
        }

    shutil.copytree(source, destination, ignore=ignore)


def snapshot_skill_sources(
    manifest: dict, destination: pathlib.Path, repo_root: pathlib.Path = ROOT
) -> tuple[dict[str, pathlib.Path], str]:
    expected_digest = skill_tree_digest(manifest, repo_root)
    sources: dict[str, pathlib.Path] = {}
    for value in manifest["skills"]:
        source = repo_root / relative_path(value, "skill")
        snapshot = destination / source.name
        copy_skill_execution_tree(source, snapshot)
        sources[value] = snapshot
    if skill_sources_digest(manifest, sources) != expected_digest:
        raise ValueError("skill files changed while the benchmark snapshot was created")
    return sources, expected_digest


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "value"


def portable_path_key(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def install_clean_room(
    room: pathlib.Path,
    manifest: dict,
    case: dict,
    arm: str,
    skill_sources: dict[str, pathlib.Path],
) -> list[pathlib.Path]:
    for fixture in case.get("fixtures", []):
        destination = room / relative_path(fixture["path"], "fixture path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(fixture["content"], encoding="utf-8")
    installed: list[pathlib.Path] = []
    if arm == "with_weft":
        for value in manifest["skills"]:
            source = skill_sources[value]
            destination = room / ".benchmark-skills" / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy_skill_execution_tree(source, destination)
            installed.append(destination)
    return installed


def prepare_clean_room_boundary(room: pathlib.Path) -> None:
    """Make the room a valid Git root so Codex cannot discover parent skills."""
    git_directory = room / ".git"
    for relative in ("objects/info", "objects/pack", "refs/heads", "refs/tags"):
        (git_directory / relative).mkdir(parents=True, exist_ok=True)
    (git_directory / "HEAD").write_text("ref: refs/heads/benchmark\n", encoding="utf-8")
    (git_directory / "config").write_text(
        "[core]\n\trepositoryformatversion = 0\n\tbare = false\n", encoding="utf-8"
    )


def pi_skill_prompt(installed: list[pathlib.Path]) -> str | None:
    if not installed:
        return None
    parts = [
        "<benchmark-skill-bundle>",
        "Use the following Weft skill instructions for this task. No tools are available in this benchmark.",
    ]
    for skill_path in installed:
        for path in skill_execution_files(skill_path):
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise UnsupportedSkillAssetError(
                    f"Pi cannot load non-text skill file: {path.name}"
                ) from exc
            relative = pathlib.Path(skill_path.name) / path.relative_to(skill_path)
            parts.extend([f'<file path="{relative.as_posix()}">', content, "</file>"])
    parts.append("</benchmark-skill-bundle>")
    return "\n".join(parts)


def pi_task_prompt(case: dict) -> str:
    fixtures = case.get("fixtures", [])
    if not fixtures:
        return case["prompt"]
    payload = json.dumps(fixtures, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    return "\n\n".join(
        [
            case["prompt"],
            "<benchmark-fixtures-json>\n"
            "These files are task input. Use their path and content as if they were "
            "available in the clean room.\n"
            f"{payload}\n"
            "</benchmark-fixtures-json>",
        ]
    )


def codex_global_skill_paths() -> list[pathlib.Path]:
    codex_home = pathlib.Path(
        os.environ.get("CODEX_HOME", pathlib.Path.home() / ".codex")
    )
    roots = [
        pathlib.Path.home() / ".agents" / "skills",
        codex_home / "skills",
        codex_home / "plugins" / "cache",
    ]
    paths: set[pathlib.Path] = set()
    visited_directories: set[pathlib.Path] = set()
    system_root = codex_home / "skills" / ".system"
    for root in roots:
        if not root.is_dir():
            continue
        for directory, child_directories, filenames in os.walk(root, followlinks=True):
            current = pathlib.Path(directory)
            if (
                "SKILL.md" in filenames
                and system_root not in current.parents
                and current != system_root
            ):
                skill_path = current / "SKILL.md"
                paths.add(skill_path.absolute())
                paths.add(skill_path.resolve())
            resolved_directory = current.resolve()
            if resolved_directory in visited_directories:
                child_directories.clear()
                continue
            visited_directories.add(resolved_directory)
    return sorted(paths)


def codex_skill_disable_config(paths: list[pathlib.Path]) -> str:
    entries = ",".join(
        f"{{path={json.dumps(str(path))},enabled=false}}" for path in paths
    )
    return f"skills.config=[{entries}]"


def codex_filesystem_permission_config(room: pathlib.Path) -> str:
    entries = [
        f'{json.dumps(":root")}="deny"',
        f'{json.dumps(":minimal")}="read"',
        f'{json.dumps(str(room.resolve()))}="write"',
    ]
    return f"permissions.weft_benchmark.filesystem={{{','.join(entries)}}}"


def build_codex_command(
    target: Target,
    prompt: str,
    disabled_skills: list[pathlib.Path] | None,
    room: pathlib.Path,
) -> list[str]:
    binary = harness_binary(target)
    command = [
        binary,
        "--model",
        target.model,
        "--ask-for-approval",
        "never",
        "--strict-config",
    ]
    if disabled_skills:
        command.extend(["--config", codex_skill_disable_config(disabled_skills)])
    for feature in CODEX_DISABLED_FEATURES:
        command.extend(["--disable", feature])
    for config in (
        'default_permissions="weft_benchmark"',
        codex_filesystem_permission_config(room),
        "permissions.weft_benchmark.network.enabled=false",
        'web_search="disabled"',
        'shell_environment_policy.inherit="none"',
        "allow_login_shell=false",
    ):
        command.extend(["--config", config])
    command.extend(
        [
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--json",
            "--color",
            "never",
            "--",
            prompt,
        ]
    )
    return command


def build_pi_command(
    target: Target,
    prompt: str,
    installed: list[pathlib.Path],
    skill_prompt: str | None = None,
) -> list[str]:
    binary = harness_binary(target)
    append_prompt = PI_COMMON_APPEND_PROMPT
    if skill_prompt:
        append_prompt = f"{append_prompt}\n\n{skill_prompt}"
    command = [
        binary,
        "--print",
        "--mode",
        "json",
        "--model",
        target.model,
        "--no-session",
        "--no-context-files",
        "--no-extensions",
        "--no-prompt-templates",
        "--no-skills",
        "--no-tools",
        "--system-prompt",
        PI_SYSTEM_PROMPT,
        "--append-system-prompt",
        append_prompt,
    ]
    command.extend(["--", f"{PI_TASK_ARGUMENT_PREFIX}{prompt}"])
    return command


def build_command(
    target: Target,
    prompt: str,
    installed: list[pathlib.Path],
    disabled_codex_skills: list[pathlib.Path] | None = None,
    pi_instructions: str | None = None,
    room: pathlib.Path | None = None,
) -> list[str]:
    if target.harness == "codex":
        if room is None:
            raise ValueError("Codex benchmark command requires a clean-room path")
        return build_codex_command(target, prompt, disabled_codex_skills, room)
    return build_pi_command(target, prompt, installed, pi_instructions)


def harness_binary(target: Target) -> str:
    variable = (
        "WEFT_BENCHMARK_CODEX_BIN"
        if target.harness == "codex"
        else "WEFT_BENCHMARK_PI_BIN"
    )
    override = os.environ.get(variable)
    if override:
        fixture_root = (ROOT / "tests" / "fixtures" / "benchmark").resolve()
        override_path = pathlib.Path(override).resolve()
        if os.environ.get("WEFT_BENCHMARK_TEST_MODE") != "1":
            raise ValueError(f"{variable} is available only in benchmark test mode")
        try:
            override_path.relative_to(fixture_root)
        except ValueError as exc:
            raise ValueError(
                f"{variable} must point inside the test fixture directory"
            ) from exc
        return str(override_path)
    return shutil.which(target.harness) or target.harness


def harness_environment(target: Target) -> dict[str, str]:
    override_variable = (
        "WEFT_BENCHMARK_CODEX_BIN"
        if target.harness == "codex"
        else "WEFT_BENCHMARK_PI_BIN"
    )
    test_harness = (
        os.environ.get("WEFT_BENCHMARK_TEST_MODE") == "1"
        and override_variable in os.environ
    )
    resolved_binary = pathlib.Path(harness_binary(target))
    names = COMMON_HARNESS_ENVIRONMENT_NAMES
    if not test_harness:
        names += (
            CODEX_ENVIRONMENT_NAMES
            if target.harness == "codex"
            else PI_ENVIRONMENT_NAMES
        )
    environment = {key: os.environ[key] for key in names if key in os.environ}
    if target.harness == "pi":
        environment["PI_TELEMETRY"] = "0"
        environment["PI_SKIP_VERSION_CHECK"] = "1"
    if (
        test_harness
        and resolved_binary.name == "fake_harness.py"
        and "WEFT_BENCHMARK_FAKE_MODE" in os.environ
    ):
        environment["WEFT_BENCHMARK_FAKE_MODE"] = os.environ["WEFT_BENCHMARK_FAKE_MODE"]
    return environment


def isolated_harness_environment(target: Target, room: pathlib.Path) -> dict[str, str]:
    environment = harness_environment(target)
    temporary_directory = room / ".tmp"
    temporary_directory.mkdir()
    environment["TMPDIR"] = str(temporary_directory)
    return environment


def harness_version(target: Target) -> str | None:
    try:
        result = subprocess.run(
            [harness_binary(target), "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            env=harness_environment(target),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip().splitlines()
    return value[-1] if value else None


def prepare_codex_skills(room: pathlib.Path, installed: list[pathlib.Path]) -> None:
    if not installed:
        return
    target_root = room / ".agents" / "skills"
    target_root.mkdir(parents=True, exist_ok=True)
    for source in installed:
        shutil.copytree(source, target_root / source.name)


def prepare_pi_agent_directory(room: pathlib.Path) -> pathlib.Path:
    destination = room / ".pi-agent"
    destination.mkdir(parents=True)
    source = pathlib.Path(
        os.environ.get("PI_CODING_AGENT_DIR", pathlib.Path.home() / ".pi" / "agent")
    )
    auth = source / "auth.json"
    if os.environ.get("WEFT_BENCHMARK_TEST_MODE") != "1" and auth.is_file():
        shutil.copy2(auth, destination / "auth.json")
    (destination / "settings.json").write_text("{}\n", encoding="utf-8")
    return destination


def valid_token_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def usage_total(usage: object) -> int | None:
    if not isinstance(usage, dict):
        return None
    input_value = next(
        (
            usage.get(key)
            for key in ("input_tokens", "inputTokens", "input")
            if valid_token_count(usage.get(key))
        ),
        None,
    )
    output_value = next(
        (
            usage.get(key)
            for key in ("output_tokens", "outputTokens", "output")
            if valid_token_count(usage.get(key))
        ),
        None,
    )
    if input_value is None or output_value is None:
        components = None
    else:
        components = input_value + output_value
    for key in ("total_tokens", "totalTokens"):
        value = usage.get(key)
        if valid_token_count(value):
            return value
    return components


def pi_usage_total(usage: object) -> int | None:
    if not isinstance(usage, dict):
        return None
    for key in ("totalTokens", "total_tokens"):
        value = usage.get(key)
        if valid_token_count(value):
            return value
    required = [usage.get("input"), usage.get("output")]
    if not all(valid_token_count(value) for value in required):
        return None
    cache_values = []
    for key in ("cacheRead", "cacheWrite"):
        value = usage.get(key, 0)
        if not valid_token_count(value):
            return None
        cache_values.append(value)
    return sum(required + cache_values)


def text_content(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") in ("text", "output_text"):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def json_events(raw: str):
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MalformedHarnessOutputError("malformed harness JSON output") from exc
        if not isinstance(event, dict):
            raise MalformedHarnessOutputError("harness JSON records must be objects")
        yield event


def parse_codex_output(raw: str) -> tuple[str | None, int | None]:
    answer = None
    tokens = None
    for event in json_events(raw):
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message":
            candidate = text_content(item.get("text") or item.get("content"))
            answer = candidate
        candidate_tokens = usage_total(event.get("usage"))
        if candidate_tokens is not None:
            tokens = candidate_tokens
    return answer, tokens


def parse_codex_failure(raw: str) -> str | None:
    for event in json_events(raw):
        item = event.get("item")
        is_error = event.get("type") == "error" or (
            isinstance(item, dict) and item.get("type") == "error"
        )
        if not is_error:
            continue
        payload = json.dumps(event, ensure_ascii=False)
        if re.search(r"\bmodel\s+rerouted\b", payload, re.IGNORECASE):
            return "model_rerouted"
        return classify_failure_text(payload) or "codex_error"
    return None


def parse_pi_output(raw: str) -> tuple[str | None, int | None]:
    answer = None
    token_total = 0
    saw_assistant_message = False
    complete_usage = True
    for event in json_events(raw):
        if event.get("type") != "message_end":
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        saw_assistant_message = True
        answer = text_content(message.get("content"))
        value = pi_usage_total(message.get("usage"))
        if value is None:
            complete_usage = False
        else:
            token_total += value
    return (
        answer,
        token_total if saw_assistant_message and complete_usage else None,
    )


def parse_pi_failure(raw: str) -> str | None:
    outcome = None
    for event in json_events(raw):
        if event.get("type") != "message_end":
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        if message.get("stopReason") in ("error", "aborted"):
            error_message = message.get("errorMessage", "")
            outcome = classify_failure_text(error_message) or "assistant_error"
        else:
            outcome = None
    return outcome


def parse_pi_model_identity(raw: str) -> str | None:
    identity = None
    saw_assistant_message = False
    for event in json_events(raw):
        if event.get("type") != "message_end":
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        saw_assistant_message = True
        provider = message.get("provider")
        model = message.get("model")
        if not (
            isinstance(provider, str) and provider and isinstance(model, str) and model
        ):
            return None
        response_model = message.get("responseModel")
        if response_model is not None and not (
            isinstance(response_model, str) and response_model
        ):
            return None
        if response_model is None:
            candidate = f"{provider}/{model}"
        else:
            candidate = (
                response_model
                if "/" in response_model
                else f"{provider}/{response_model}"
            )
        if identity is not None and candidate != identity:
            return None
        identity = candidate
    return identity if saw_assistant_message else None


def parse_pi_output_limit(raw: str) -> bool:
    limited = False
    for event in json_events(raw):
        if event.get("type") != "message_end":
            continue
        message = event.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        limited = message.get("stopReason") in ("length", "max_tokens")
    return limited


def classify_failure_text(value: str) -> str | None:
    text = value.lower()
    if re.search(r"insufficient (balance|credits?)|creditserror", text):
        return "insufficient_provider_balance"
    if re.search(
        r"not logged in|authentication required|unauthori[sz]ed|invalid api key|missing api key",
        text,
    ):
        return "authentication_failure"
    if re.search(r"model .{0,80}(not found|unavailable|unknown)|unknown model", text):
        return "model_unavailable"
    if re.search(r"rate.?limit|too many requests", text):
        return "provider_rate_limit"
    if "unexpected argument" in text:
        return "invalid_harness_arguments"
    return None


def classify_nonzero(exit_code: int, stdout: str, stderr: str) -> str:
    classified = classify_failure_text(f"{stdout}\n{stderr}")
    if classified:
        return classified
    return f"process_exit_{exit_code}"


def run_child(
    command: list[str], cwd: pathlib.Path, env: dict[str, str], timeout: int
) -> tuple[int | None, str, str, float, str | None]:
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=(os.name == "posix"),
        )
    except FileNotFoundError as exc:
        return None, "", str(exc), time.monotonic() - started, "harness_not_found"
    except OSError as exc:
        return (
            None,
            "",
            str(exc),
            time.monotonic() - started,
            f"harness_launch_error_{exc.errno or 'unknown'}",
        )

    def stop_child() -> tuple[str, str]:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            pass
        try:
            return process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            return process.communicate()

    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr, time.monotonic() - started, None
    except subprocess.TimeoutExpired:
        stdout, stderr = stop_child()
        return None, stdout, stderr, time.monotonic() - started, "timeout"
    except BaseException:
        stop_child()
        raise


def grade_answer(case: dict, answer: str) -> tuple[bool, list[dict]]:
    checks = []
    for check in case["checks"]:
        passed = re.search(check["pattern"], answer, re.DOTALL) is not None
        checks.append({"id": check["id"], "passed": passed})
    return all(check["passed"] for check in checks), checks


def execute_one(
    target: Target,
    manifest: dict,
    case: dict,
    arm: str,
    repetition: int,
    out_root: pathlib.Path,
    timeout: int,
    disabled_codex_skills: list[pathlib.Path],
    skill_sources: dict[str, pathlib.Path],
) -> RunResult:
    run_relative = (
        pathlib.Path("runs")
        / target.harness
        / slug(target.model)
        / case["id"]
        / f"run-{repetition}"
        / arm
    )
    run_path = out_root / run_relative
    run_path.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="weft-benchmark-") as temp_value:
        room = pathlib.Path(temp_value)
        prepare_clean_room_boundary(room)
        installed = install_clean_room(room, manifest, case, arm, skill_sources)
        if target.harness == "codex":
            prepare_codex_skills(room, installed)
        pi_agent_directory = (
            prepare_pi_agent_directory(room) if target.harness == "pi" else None
        )
        setup_started = time.monotonic()
        try:
            pi_instructions = (
                pi_skill_prompt(installed) if target.harness == "pi" else None
            )
            task_prompt = (
                pi_task_prompt(case) if target.harness == "pi" else case["prompt"]
            )
            command = build_command(
                target,
                task_prompt,
                installed,
                disabled_codex_skills,
                pi_instructions,
                room,
            )
            env = isolated_harness_environment(target, room)
            if pi_agent_directory is not None:
                env["PI_CODING_AGENT_DIR"] = str(pi_agent_directory)
        except UnsupportedSkillAssetError as exc:
            exit_code = None
            stdout = ""
            stderr = str(exc)
            duration = time.monotonic() - setup_started
            timeout_error = "pi_non_text_skill_asset"
        else:
            exit_code, stdout, stderr, duration, timeout_error = run_child(
                command, room, env, timeout
            )

    raw_name = "raw.jsonl" if target.harness == "codex" else "raw.json"
    (run_path / raw_name).write_text(stdout, encoding="utf-8")
    (run_path / "stderr.txt").write_text(stderr, encoding="utf-8")
    if timeout_error:
        result = RunResult(
            target.harness,
            target.model,
            case["id"],
            arm,
            repetition,
            duration,
            None,
            None,
            None,
            [],
            timeout_error,
            None,
            run_relative.as_posix(),
        )
    elif exit_code != 0:
        exclusion = classify_nonzero(exit_code or 1, stdout, stderr)
        result = RunResult(
            target.harness,
            target.model,
            case["id"],
            arm,
            repetition,
            duration,
            None,
            None,
            None,
            [],
            exclusion,
            exit_code,
            run_relative.as_posix(),
        )
    else:
        try:
            answer, tokens = (
                parse_codex_output(stdout)
                if target.harness == "codex"
                else parse_pi_output(stdout)
            )
            pi_failure = parse_pi_failure(stdout) if target.harness == "pi" else None
            codex_failure = (
                parse_codex_failure(stdout) if target.harness == "codex" else None
            )
            pi_identity = (
                parse_pi_model_identity(stdout) if target.harness == "pi" else None
            )
            pi_output_limit = (
                parse_pi_output_limit(stdout) if target.harness == "pi" else False
            )
        except MalformedHarnessOutputError:
            answer = None
            tokens = None
            pi_failure = None
            codex_failure = None
            pi_identity = None
            pi_output_limit = False
            parse_failure = "malformed_harness_output"
        else:
            parse_failure = None
            if target.harness == "pi" and pi_identity is None:
                parse_failure = "missing_model_identity"
            elif target.harness == "pi" and pi_identity != target.model:
                parse_failure = "model_identity_mismatch"
        if answer is not None:
            (run_path / "answer.md").write_text(answer, encoding="utf-8")
        if parse_failure:
            result = RunResult(
                target.harness,
                target.model,
                case["id"],
                arm,
                repetition,
                duration,
                None,
                None,
                None,
                [],
                parse_failure,
                exit_code,
                run_relative.as_posix(),
            )
        elif codex_failure or pi_failure:
            result = RunResult(
                target.harness,
                target.model,
                case["id"],
                arm,
                repetition,
                duration,
                tokens,
                None,
                answer,
                [],
                codex_failure or pi_failure,
                exit_code,
                run_relative.as_posix(),
            )
        elif answer is None:
            result = RunResult(
                target.harness,
                target.model,
                case["id"],
                arm,
                repetition,
                duration,
                tokens,
                None,
                answer,
                [],
                "missing_final_answer",
                exit_code,
                run_relative.as_posix(),
            )
        elif tokens is None:
            result = RunResult(
                target.harness,
                target.model,
                case["id"],
                arm,
                repetition,
                duration,
                None,
                None,
                answer,
                [],
                "missing_token_telemetry",
                exit_code,
                run_relative.as_posix(),
            )
        elif pi_output_limit:
            _, checks = grade_answer(case, answer)
            result = RunResult(
                target.harness,
                target.model,
                case["id"],
                arm,
                repetition,
                duration,
                tokens,
                False,
                answer,
                checks,
                None,
                exit_code,
                run_relative.as_posix(),
            )
        else:
            accomplished, checks = grade_answer(case, answer)
            result = RunResult(
                target.harness,
                target.model,
                case["id"],
                arm,
                repetition,
                duration,
                tokens,
                accomplished,
                answer,
                checks,
                None,
                exit_code,
                run_relative.as_posix(),
            )
    (run_path / "result.json").write_text(
        json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return result


def median(values: list[float | int]) -> float | int:
    value = statistics.median(values)
    return (
        int(value)
        if isinstance(value, float) and value.is_integer()
        else round(value, 3)
    )


def aggregate(
    skill: str,
    manifest_digest: str,
    skill_digest: str,
    minimum_repetitions: int,
    runs: list[RunResult],
    *,
    targets: list[Target] | None = None,
    case_ids: list[str] | None = None,
) -> dict:
    pairs: dict[tuple[str, str, str, int], dict[str, RunResult]] = defaultdict(dict)
    for run in runs:
        pairs[(run.harness, run.model, run.case_id, run.repetition)][run.arm] = run

    valid: list[RunResult] = []
    valid_pair_keys: set[tuple[str, str, str, int]] = set()
    excluded_pair_keys: set[tuple[str, str, str, int]] = set()
    exclusions = Counter()
    excluded_by_target = Counter()
    for key, arms in pairs.items():
        harness, model, _, _ = key
        reasons = []
        for arm in ARMS:
            run = arms.get(arm)
            if run is None:
                reasons.append(f"missing_{arm}")
            elif run.exclusion:
                reasons.append(run.exclusion)
        if reasons:
            reason = "+".join(sorted(set(reasons)))
            exclusions[reason] += 1
            excluded_by_target[(harness, model)] += 1
            excluded_pair_keys.add(key)
            continue
        valid.extend(arms[arm] for arm in ARMS)
        valid_pair_keys.add(key)

    grouped: dict[tuple[str, str, str], list[RunResult]] = defaultdict(list)
    for run in valid:
        grouped[(run.harness, run.model, run.arm)].append(run)
    rows = []
    arm_order = {arm: index for index, arm in enumerate(ARMS)}
    for (harness, model, arm), group in sorted(
        grouped.items(),
        key=lambda item: (item[0][0], item[0][1], arm_order[item[0][2]]),
    ):
        rows.append(
            {
                "harness": harness,
                "model": model,
                "arm": arm,
                "valid_runs": len(group),
                "excluded_pairs": excluded_by_target[(harness, model)],
                "median_time_seconds": median([run.duration_seconds for run in group]),
                "accomplishment_rate": round(
                    sum(bool(run.accomplished) for run in group) / len(group), 4
                ),
                "median_tokens": median(
                    [run.total_tokens for run in group if run.total_tokens is not None]
                ),
            }
        )
    deltas = []
    by_target: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for row in rows:
        by_target[(row["harness"], row["model"])][row["arm"]] = row
    for (harness, model), arms in sorted(by_target.items()):
        if not all(arm in arms for arm in ARMS):
            continue
        without, with_weft = arms["without_weft"], arms["with_weft"]
        deltas.append(
            {
                "harness": harness,
                "model": model,
                "time_seconds": round(
                    with_weft["median_time_seconds"] - without["median_time_seconds"], 3
                ),
                "accomplishment_percentage_points": round(
                    (with_weft["accomplishment_rate"] - without["accomplishment_rate"])
                    * 100,
                    2,
                ),
                "tokens": with_weft["median_tokens"] - without["median_tokens"],
            }
        )
    coverage = []
    if targets is not None and case_ids is not None:
        for target in targets:
            for case_id in case_ids:
                prefix = (target.harness, target.model, case_id)
                coverage.append(
                    {
                        "harness": target.harness,
                        "model": target.model,
                        "case_id": case_id,
                        "valid_pairs": sum(
                            key[:3] == prefix for key in valid_pair_keys
                        ),
                        "excluded_pairs": sum(
                            key[:3] == prefix for key in excluded_pair_keys
                        ),
                    }
                )
    return {
        "version": 1,
        "skill": skill,
        "generated_at": utc_now(),
        "manifest_digest": manifest_digest,
        "skill_digest": skill_digest,
        "minimum_repetitions": minimum_repetitions,
        "results": rows,
        "deltas": deltas,
        "case_coverage": coverage,
        "exclusions": {
            "pairs": sum(exclusions.values()),
            "reasons": dict(sorted(exclusions.items())),
            "by_target": {
                f"{harness}:{model}": count
                for (harness, model), count in sorted(excluded_by_target.items())
            },
        },
    }


def validate_run_telemetry(run: RunResult) -> None:
    duration = run.duration_seconds
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration < 0
    ):
        raise ValueError("raw evidence requires a finite nonnegative duration")
    if run.total_tokens is not None and (
        isinstance(run.total_tokens, bool)
        or not isinstance(run.total_tokens, int)
        or run.total_tokens < 0
    ):
        raise ValueError("raw evidence requires a nonnegative token count")
    if run.exclusion is None:
        if run.exit_code != 0:
            raise ValueError("valid raw evidence requires exit_code 0")
        if run.total_tokens is None:
            raise ValueError("valid raw evidence requires token telemetry")
        if not isinstance(run.accomplished, bool):
            raise ValueError("valid raw evidence requires a boolean accomplishment")
        if not isinstance(run.answer, str):
            raise ValueError("valid raw evidence requires a final answer")
        if not isinstance(run.checks, list):
            raise ValueError("valid raw evidence requires grading checks")
    else:
        if not isinstance(run.exclusion, str) or not run.exclusion:
            raise ValueError("excluded raw evidence requires an exclusion reason")
        if run.accomplished is not None or run.checks:
            raise ValueError(
                "excluded raw evidence cannot contain accomplishment grading"
            )


def verify_publication(
    summary: dict,
    raw: dict,
    manifest: dict,
    repo_root: pathlib.Path,
    evidence_root: pathlib.Path,
) -> None:
    if (
        raw.get("test_evidence") is not False
        or summary.get("test_evidence") is not False
    ):
        raise ValueError("test-harness evidence cannot be published")
    for field in ("skill", "manifest_digest", "skill_digest", "generated_at"):
        if summary.get(field) != raw.get(field):
            raise ValueError(f"summary and raw evidence have different {field}")
    validate_generated_at(summary.get("generated_at"))
    if summary.get("skill") != manifest.get("skill"):
        raise ValueError("benchmark manifest and evidence have different skill names")
    current_manifest_digest = canonical_digest(manifest)
    if summary.get("manifest_digest") != current_manifest_digest:
        raise ValueError("benchmark evidence does not match the current manifest")
    current_skill_digest = skill_tree_digest(manifest, repo_root)
    if summary.get("skill_digest") != current_skill_digest:
        raise ValueError("benchmark evidence does not match the current skill files")
    if summary.get("case_ids") != summary.get("manifest_case_ids"):
        raise ValueError("partial --only results cannot be published")
    if summary.get("case_ids") != raw.get("case_ids") or raw.get("case_ids") != raw.get(
        "manifest_case_ids"
    ):
        raise ValueError("summary and raw evidence have different benchmark cases")
    manifest_case_ids = [case["id"] for case in manifest["cases"]]
    if raw.get("case_ids") != manifest_case_ids:
        raise ValueError(
            "benchmark evidence does not contain every current manifest case"
        )
    minimum = summary.get("minimum_repetitions")
    if (
        isinstance(minimum, bool)
        or not isinstance(minimum, int)
        or minimum < 1
        or minimum != raw.get("minimum_repetitions")
        or minimum != manifest.get("minimum_repetitions")
    ):
        raise ValueError("summary and raw evidence have different minimum repetitions")
    repetitions_run = summary.get("repetitions_run")
    if (
        isinstance(repetitions_run, bool)
        or not isinstance(repetitions_run, int)
        or repetitions_run < minimum
        or repetitions_run != raw.get("repetitions_run")
    ):
        raise ValueError("summary and raw evidence have different repetitions_run")
    if summary.get("targets") != raw.get("targets"):
        raise ValueError("summary and raw evidence have different targets")
    try:
        targets = [
            parse_target(f"{value['harness']}:{value['model']}")
            for value in raw["targets"]
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"raw evidence has invalid targets: {exc}") from exc
    if not targets or len({target.label for target in targets}) != len(targets):
        raise ValueError("raw evidence must contain unique benchmark targets")
    for value in raw["targets"]:
        version = value.get("harness_version")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("raw evidence requires a non-empty harness version")
    target_path_keys = {
        (target.harness, portable_path_key(slug(target.model))) for target in targets
    }
    if len(target_path_keys) != len(targets):
        raise ValueError("raw evidence targets have colliding filesystem slugs")
    try:
        runs = [RunResult(**value) for value in raw["runs"]]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"raw evidence has invalid runs: {exc}") from exc
    cases_by_id = {case["id"]: case for case in manifest["cases"]}
    target_keys = {(target.harness, target.model) for target in targets}
    identities: set[tuple[str, str, str, str, int]] = set()
    for run in runs:
        validate_run_telemetry(run)
        identity = (run.harness, run.model, run.case_id, run.arm, run.repetition)
        if identity in identities:
            raise ValueError("raw evidence contains a duplicate benchmark run")
        identities.add(identity)
        if (
            (run.harness, run.model) not in target_keys
            or run.case_id not in cases_by_id
            or run.arm not in ARMS
        ):
            raise ValueError("raw evidence contains a run outside the manifest matrix")
        if (
            isinstance(run.repetition, bool)
            or not isinstance(run.repetition, int)
            or run.repetition < 1
        ):
            raise ValueError("raw evidence contains an invalid repetition")
        expected_run_path = (
            pathlib.Path("runs")
            / run.harness
            / slug(run.model)
            / run.case_id
            / f"run-{run.repetition}"
            / run.arm
        ).as_posix()
        if run.run_path != expected_run_path:
            raise ValueError("raw evidence contains an unexpected run path")
        if run.exclusion is not None:
            continue
        if not isinstance(run.answer, str):
            raise ValueError("raw evidence is missing a final answer")
        answer_path = (
            evidence_root / relative_path(run.run_path, "run_path") / "answer.md"
        )
        try:
            answer_path.resolve().relative_to(evidence_root.resolve())
        except ValueError as exc:
            raise ValueError(
                "raw evidence answer path escapes the evidence directory"
            ) from exc
        try:
            answer = answer_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read benchmark answer evidence: {exc}") from exc
        if answer != run.answer:
            raise ValueError("raw evidence final answer does not match answer.md")
        accomplished, checks = grade_answer(cases_by_id[run.case_id], answer)
        if run.accomplished != accomplished or run.checks != checks:
            raise ValueError(
                "raw evidence grading does not match the current manifest checks"
            )
    expected_identities = {
        (target.harness, target.model, case_id, arm, repetition)
        for target in targets
        for case_id in manifest_case_ids
        for repetition in range(1, repetitions_run + 1)
        for arm in ARMS
    }
    if identities != expected_identities:
        raise ValueError("raw evidence does not contain the exact repetition matrix")
    recomputed = aggregate(
        summary["skill"],
        summary["manifest_digest"],
        summary["skill_digest"],
        minimum,
        runs,
        targets=targets,
        case_ids=manifest_case_ids,
    )
    for field in ("results", "deltas", "case_coverage", "exclusions"):
        if summary.get(field) != recomputed.get(field):
            raise ValueError(f"summary {field} do not match raw evidence")


def verify_case_minimums(summary: dict) -> None:
    minimum = summary["minimum_repetitions"]
    coverage = summary.get("case_coverage")
    if not isinstance(coverage, list) or not coverage:
        raise ValueError("summary has no per-case coverage")
    for row in coverage:
        if row.get("valid_pairs", 0) < minimum:
            raise ValueError(
                f"{row.get('harness')}:{row.get('model')} {row.get('case_id')} has "
                f"{row.get('valid_pairs', 0)} valid pairs; {minimum} required"
            )


def harness_title(value: str) -> str:
    return {"codex": "Codex", "pi": "Pi"}.get(value, value)


def percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def signed(value: float | int, suffix: str = "") -> str:
    return f"{value:+g}{suffix}"


def render_benchmark_block(summary: dict, raw_path: str) -> str:
    lines = [
        "## Benchmark",
        "",
        "The same clean-room tasks run without Weft and with Weft. Headline metrics are end-to-end time, full-task accomplishment rate, and total agent tokens.",
        "",
        "| Harness / model | Arm | Time, median | Accomplishment rate | Tokens, median | Valid / excluded pairs |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary["results"]:
        lines.append(
            f"| {harness_title(row['harness'])} / `{row['model']}` | {row['arm'].replace('_', ' ')} | {row['median_time_seconds']}s | {percentage(row['accomplishment_rate'])} | {row['median_tokens']} | {row['valid_runs']} / {row['excluded_pairs']} |"
        )
    for row in summary["deltas"]:
        lines.append(
            f"| {harness_title(row['harness'])} / `{row['model']}` | Weft impact | {signed(row['time_seconds'], 's')} | {signed(row['accomplishment_percentage_points'], ' pp')} | {signed(row['tokens'])} | — |"
        )
    lines.extend(
        [
            "",
            f"Actual repetitions per case: {summary['repetitions_run']}. Required valid pairs per target and case: {summary['minimum_repetitions']}. Excluded matched pairs: {summary.get('exclusions', {}).get('pairs', 0)}.",
            f"Measured: {summary['generated_at']}. Skill digest: `{summary['skill_digest']}`. Manifest digest: `{summary['manifest_digest']}`.",
            f"[Raw benchmark evidence]({raw_path})",
        ]
    )
    return "\n".join(lines)


def replace_benchmark_block(readme: str, block: str) -> str:
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise ValueError(
            "README must contain exactly one benchmark start and end marker"
        )
    if readme.index(START_MARKER) > readme.index(END_MARKER):
        raise ValueError("README benchmark markers are reversed")
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL
    )
    replacement = f"{START_MARKER}\n{block}\n{END_MARKER}"
    return pattern.sub(replacement, readme, count=1)


def unmeasured_block() -> str:
    return "\n".join(
        [
            START_MARKER,
            "## Benchmark",
            "",
            "**Status: Unmeasured.** No reproducible with-Weft versus without-Weft result has been published for this skill yet.",
            END_MARKER,
        ]
    )


def dry_run(
    manifest: dict,
    targets: list[Target],
    cases: list[dict],
    repetitions: int,
    disabled_codex_skills: list[pathlib.Path],
) -> None:
    placeholder = pathlib.Path("<clean-room>")
    for target in targets:
        for case in cases:
            for repetition in range(1, repetitions + 1):
                for arm in ARMS:
                    installed = (
                        []
                        if arm == "without_weft"
                        else [
                            placeholder / ".benchmark-skills" / pathlib.Path(value).name
                            for value in manifest["skills"]
                        ]
                    )
                    pi_instructions = (
                        "<benchmark-skill-bundle>skill snapshot</benchmark-skill-bundle>"
                        if target.harness == "pi" and installed
                        else None
                    )
                    task_prompt = (
                        pi_task_prompt(case)
                        if target.harness == "pi"
                        else case["prompt"]
                    )
                    command = build_command(
                        target,
                        task_prompt,
                        installed,
                        disabled_codex_skills,
                        pi_instructions,
                        placeholder,
                    )
                    print(
                        f"{target.label} {case['id']} run-{repetition} {arm}: {shlex.join(command)}"
                    )


def command_run(args: argparse.Namespace) -> int:
    require_supported_platform(args.dry_run)
    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    manifest_hash = canonical_digest(manifest)
    targets = [parse_target(value) for value in args.target]
    if len({target.label for target in targets}) != len(targets):
        raise ValueError("duplicate --target values are not allowed")
    if len(
        {(target.harness, portable_path_key(slug(target.model))) for target in targets}
    ) != len(targets):
        raise ValueError(
            "target model identifiers must have distinct filesystem slugs per harness"
        )
    wanted = set(args.only.split(",")) if args.only else None
    cases = [
        case for case in manifest["cases"] if wanted is None or case["id"] in wanted
    ]
    if wanted and wanted - {case["id"] for case in cases}:
        raise ValueError(
            f"unknown case ids: {', '.join(sorted(wanted - {case['id'] for case in cases}))}"
        )
    repetitions = (
        manifest["minimum_repetitions"]
        if args.repetitions is None
        else args.repetitions
    )
    if repetitions < manifest["minimum_repetitions"]:
        raise ValueError("--repetitions cannot be lower than the manifest minimum")
    if args.timeout < 1:
        raise ValueError("--timeout must be a positive integer")
    disabled_codex_skills = (
        codex_global_skill_paths()
        if any(target.harness == "codex" for target in targets)
        else []
    )
    if args.dry_run:
        dry_run(manifest, targets, cases, repetitions, disabled_codex_skills)
        return 0

    out_root = pathlib.Path(args.out).resolve()
    if out_root.exists() and (not out_root.is_dir() or any(out_root.iterdir())):
        raise ValueError("--out must be a new or empty directory")
    out_root.mkdir(parents=True, exist_ok=True)
    runs = []
    target_versions = [
        {**dataclasses.asdict(target), "harness_version": harness_version(target)}
        for target in targets
    ]
    test_evidence = os.environ.get("WEFT_BENCHMARK_TEST_MODE") == "1"
    with tempfile.TemporaryDirectory(
        prefix="weft-benchmark-snapshot-"
    ) as snapshot_value:
        skill_sources, skills_hash = snapshot_skill_sources(
            manifest, pathlib.Path(snapshot_value)
        )
        for target in targets:
            for case in cases:
                for repetition in range(1, repetitions + 1):
                    arm_order = ARMS if repetition % 2 else tuple(reversed(ARMS))
                    for arm in arm_order:
                        print(
                            f"running {target.label} {case['id']} run-{repetition} {arm}",
                            file=sys.stderr,
                        )
                        runs.append(
                            execute_one(
                                target,
                                manifest,
                                case,
                                arm,
                                repetition,
                                out_root,
                                args.timeout,
                                disabled_codex_skills,
                                skill_sources,
                            )
                        )
        current_manifest = load_manifest(manifest_path)
        if canonical_digest(current_manifest) != manifest_hash:
            raise ValueError("manifest changed while the benchmark was running")
        if skill_tree_digest(manifest) != skills_hash:
            raise ValueError("skill files changed while the benchmark was running")
    generated_at = utc_now()
    raw = {
        "version": 1,
        "skill": manifest["skill"],
        "generated_at": generated_at,
        "manifest_digest": manifest_hash,
        "skill_digest": skills_hash,
        "minimum_repetitions": manifest["minimum_repetitions"],
        "repetitions_run": repetitions,
        "case_ids": [case["id"] for case in cases],
        "manifest_case_ids": [case["id"] for case in manifest["cases"]],
        "targets": target_versions,
        "test_evidence": test_evidence,
        "codex_disabled_global_skill_count": len(disabled_codex_skills),
        "cases": [
            {"id": case["id"], "truth_provenance": case["truth_provenance"]}
            for case in cases
        ],
        "runs": [run.to_dict() for run in runs],
    }
    summary = aggregate(
        manifest["skill"],
        manifest_hash,
        skills_hash,
        manifest["minimum_repetitions"],
        runs,
        targets=targets,
        case_ids=[case["id"] for case in cases],
    )
    summary["generated_at"] = generated_at
    summary["repetitions_run"] = repetitions
    summary["targets"] = target_versions
    summary["test_evidence"] = test_evidence
    summary["case_ids"] = [case["id"] for case in cases]
    summary["manifest_case_ids"] = [case["id"] for case in manifest["cases"]]
    (out_root / "raw.json").write_text(
        json.dumps(raw, indent=2) + "\n", encoding="utf-8"
    )
    (out_root / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    for target in targets:
        rows = [
            row
            for row in summary["results"]
            if row["harness"] == target.harness and row["model"] == target.model
        ]
        if not rows:
            excluded = summary["exclusions"]["by_target"].get(target.label, 0)
            print(f"{target.label}: unmeasurable ({excluded} excluded pairs)")
            continue
        for row in rows:
            print(
                f"{target.label} {row['arm']}: time={row['median_time_seconds']}s accomplishment={percentage(row['accomplishment_rate'])} tokens={row['median_tokens']}"
            )
    return 0


def require_supported_platform(dry_run: bool) -> None:
    if not dry_run and os.name != "posix":
        raise ValueError(
            "real benchmark runs require POSIX process and filesystem isolation in V0"
        )


def command_publish(args: argparse.Namespace) -> int:
    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    summary_path = pathlib.Path(args.summary).resolve()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    raw_path = summary_path.with_name("raw.json")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    verify_publication(summary, raw, manifest, ROOT, summary_path.parent)
    if not summary.get("results") or not summary.get("deltas"):
        raise ValueError("summary has no complete paired benchmark result")
    verify_case_minimums(summary)
    for row in summary["results"]:
        if row.get("median_tokens") is None:
            raise ValueError("summary contains missing token telemetry")
    readme_path = pathlib.Path(args.readme).resolve()
    if readme_path.parent.name != summary.get("skill"):
        raise ValueError("README directory does not match the benchmark skill")
    expected_manifest_path = (
        readme_path.parent / "benchmarks" / "manifest.json"
    ).resolve()
    if manifest_path != expected_manifest_path:
        raise ValueError(
            "--manifest must be the benchmark manifest beside the skill README"
        )
    try:
        evidence_link = raw_path.relative_to(readme_path.parent).as_posix()
    except ValueError as exc:
        raise ValueError(
            "raw evidence must be inside the skill directory before publication"
        ) from exc
    block = render_benchmark_block(summary, evidence_link)
    readme_path.write_text(
        replace_benchmark_block(readme_path.read_text(encoding="utf-8"), block),
        encoding="utf-8",
    )
    print(readme_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run paired clean-room benchmarks")
    run.add_argument("--manifest", required=True)
    run.add_argument(
        "--target",
        action="append",
        required=True,
        help="<harness>:<model>; repeat for more targets",
    )
    run.add_argument("--out", default="benchmark-results")
    run.add_argument("--only", help="comma-separated case ids")
    run.add_argument("--repetitions", type=int)
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(handler=command_run)

    publish = subparsers.add_parser(
        "publish", help="write a verified result into a skill README"
    )
    publish.add_argument("--manifest", required=True)
    publish.add_argument("--summary", required=True)
    publish.add_argument("--readme", required=True)
    publish.set_defaults(handler=command_publish)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
