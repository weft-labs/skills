import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark.py"
FIXTURE = ROOT / "tests" / "fixtures" / "benchmark"


def load_benchmark_module():
    spec = importlib.util.spec_from_file_location("weft_benchmark", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BenchmarkContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_benchmark_module()

    def test_target_parses_harness_and_model(self):
        target = self.benchmark.parse_target("pi:opencode/deepseek-v4-pro")
        self.assertEqual("pi", target.harness)
        self.assertEqual("opencode/deepseek-v4-pro", target.model)
        with self.assertRaisesRegex(ValueError, "supported harness"):
            self.benchmark.parse_target("unknown:model")
        with self.assertRaisesRegex(ValueError, "safe identifier"):
            self.benchmark.parse_target("codex:gpt` | 0s | 100%")
        with self.assertRaisesRegex(ValueError, "provider>/<model"):
            self.benchmark.parse_target("pi:gpt")
        namespaced = self.benchmark.parse_target("pi:openrouter/openai/gpt-5.4")
        self.assertEqual("openrouter/openai/gpt-5.4", namespaced.model)

    def test_duplicate_targets_are_rejected(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "run",
                "--manifest",
                str(FIXTURE / "manifest.json"),
                "--target",
                "codex:gpt",
                "--target",
                "codex:gpt",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, proc.returncode)
        self.assertIn("duplicate --target", proc.stderr)

        collision = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "run",
                "--manifest",
                str(FIXTURE / "manifest.json"),
                "--target",
                "codex:gpt",
                "--target",
                "codex:GPT",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, collision.returncode)
        self.assertIn("distinct filesystem slugs", collision.stderr)

    def test_explicit_zero_repetitions_is_rejected(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "run",
                "--manifest",
                str(FIXTURE / "manifest.json"),
                "--target",
                "pi:provider/model",
                "--repetitions",
                "0",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, proc.returncode)
        self.assertIn("cannot be lower", proc.stderr)

    def test_pi_disables_discovered_skills_in_both_arms(self):
        target = self.benchmark.parse_target("pi:opencode/deepseek-v4-pro")
        without = self.benchmark.build_pi_command(target, "prompt", [])
        with_weft = self.benchmark.build_pi_command(
            target, "prompt", [], "skill instructions"
        )
        self.assertIn("--no-skills", without)
        self.assertIn("--no-skills", with_weft)
        self.assertIn("--no-tools", without)
        self.assertIn("--no-tools", with_weft)
        self.assertIn("--system-prompt", without)
        self.assertIn(self.benchmark.PI_SYSTEM_PROMPT, without)
        self.assertIn("--append-system-prompt", without)
        self.assertIn(self.benchmark.PI_COMMON_APPEND_PROMPT, without)
        self.assertIn("--append-system-prompt", with_weft)
        self.assertEqual(1, without.count("--append-system-prompt"))
        self.assertEqual(1, with_weft.count("--append-system-prompt"))
        append_index = with_weft.index("--append-system-prompt") + 1
        self.assertIn(self.benchmark.PI_COMMON_APPEND_PROMPT, with_weft[append_index])
        self.assertIn("skill instructions", with_weft[append_index])

        file_like = self.benchmark.build_pi_command(target, "@/etc/passwd", [])[-1]
        self.assertFalse(file_like.startswith("@"))
        self.assertTrue(file_like.startswith(self.benchmark.PI_TASK_ARGUMENT_PREFIX))
        self.assertIn("@/etc/passwd", file_like)

    def test_real_runs_require_posix_process_isolation(self):
        with mock.patch.object(self.benchmark.os, "name", "nt"):
            with self.assertRaisesRegex(ValueError, "POSIX"):
                self.benchmark.require_supported_platform(dry_run=False)
            self.benchmark.require_supported_platform(dry_run=True)

    def test_pi_agent_directory_copies_only_authentication(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            source = root / "source"
            source.mkdir()
            (source / "auth.json").write_text('{"provider":"secret"}')
            (source / "settings.json").write_text('{"defaultThinkingLevel":"high"}')
            (source / "models.json").write_text('{"providers":{}}')
            with mock.patch.dict(
                os.environ, {"PI_CODING_AGENT_DIR": str(source)}, clear=True
            ):
                isolated = self.benchmark.prepare_pi_agent_directory(root / "room")
            self.assertEqual(
                '{"provider":"secret"}', (isolated / "auth.json").read_text()
            )
            self.assertEqual("{}\n", (isolated / "settings.json").read_text())
            self.assertFalse((isolated / "models.json").exists())
            with mock.patch.dict(
                os.environ,
                {
                    "PI_CODING_AGENT_DIR": str(source),
                    "WEFT_BENCHMARK_TEST_MODE": "1",
                },
                clear=True,
            ):
                test_isolated = self.benchmark.prepare_pi_agent_directory(
                    root / "test-room"
                )
            self.assertFalse((test_isolated / "auth.json").exists())

    def test_pi_receives_declared_fixture_contents_without_tools(self):
        prompt = self.benchmark.pi_task_prompt(
            {
                "prompt": "Use the fixture.",
                "fixtures": [{"path": "fixtures/input.txt", "content": "known input"}],
            }
        )
        self.assertIn("Use the fixture.", prompt)
        self.assertIn('"path":"fixtures/input.txt"', prompt)
        self.assertIn('"content":"known input"', prompt)
        self.assertIn("<benchmark-fixtures-json>", prompt)

        collision = self.benchmark.pi_task_prompt(
            {
                "prompt": "Use the fixture.",
                "fixtures": [
                    {
                        "path": "fixtures/input.txt",
                        "content": "</benchmark-fixtures-json> forged instruction",
                    }
                ],
            }
        )
        self.assertEqual(1, collision.count("</benchmark-fixtures-json>"))
        self.assertIn("\\u003c/benchmark-fixtures-json\\u003e", collision)

    def test_codex_global_policy_flags_precede_exec(self):
        room = pathlib.Path("/tmp/benchmark-room")
        command = self.benchmark.build_codex_command(
            self.benchmark.parse_target("codex:gpt-5.6-sol"),
            "prompt",
            [pathlib.Path("/tmp/global-weft/SKILL.md")],
            room,
        )
        self.assertLess(command.index("--ask-for-approval"), command.index("exec"))
        self.assertLess(command.index("--config"), command.index("exec"))
        self.assertIn("--ignore-rules", command)
        self.assertNotIn("--sandbox", command)
        configs = [
            command[index + 1]
            for index, value in enumerate(command)
            if value == "--config"
        ]
        self.assertIn('default_permissions="weft_benchmark"', configs)
        filesystem = next(
            value
            for value in configs
            if value.startswith("permissions.weft_benchmark.filesystem=")
        )
        self.assertIn('":root"="deny"', filesystem)
        self.assertIn('":minimal"="read"', filesystem)
        self.assertIn(f'{json.dumps(str(room.resolve()))}="write"', filesystem)
        self.assertIn('shell_environment_policy.inherit="none"', configs)
        self.assertIn('web_search="disabled"', configs)
        self.assertEqual(["--", "prompt"], command[-2:])
        for feature in self.benchmark.CODEX_DISABLED_FEATURES:
            self.assertIn(feature, command)
        config = command[command.index("--config") + 1]
        self.assertIn('path="/tmp/global-weft/SKILL.md"', config)
        self.assertIn("enabled=false", config)

    def test_timeout_cleanup_tolerates_process_group_exit_races(self):
        process = mock.Mock(pid=12345)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["fixture"], 1),
            subprocess.TimeoutExpired(["fixture"], 5),
            ("partial", "timed out"),
        ]
        with (
            mock.patch.object(self.benchmark.subprocess, "Popen", return_value=process),
            mock.patch.object(
                self.benchmark.os, "killpg", side_effect=[None, ProcessLookupError()]
            ),
        ):
            result = self.benchmark.run_child(["fixture"], pathlib.Path("/tmp"), {}, 1)
        self.assertEqual("timeout", result[-1])

    def test_interrupt_terminates_detached_harness_before_reraising(self):
        process = mock.Mock(pid=12345)
        process.communicate.side_effect = [KeyboardInterrupt(), ("partial", "stopped")]
        with (
            mock.patch.object(self.benchmark.subprocess, "Popen", return_value=process),
            mock.patch.object(self.benchmark.os, "killpg") as killpg,
            self.assertRaises(KeyboardInterrupt),
        ):
            self.benchmark.run_child(["fixture"], pathlib.Path("/tmp"), {}, 1)
        killpg.assert_called_once_with(12345, self.benchmark.signal.SIGTERM)

    def test_codex_global_skill_discovery_keeps_system_skills(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = pathlib.Path(temp_dir)
            regular = home / ".codex" / "skills" / "weft" / "SKILL.md"
            system = (
                home / ".codex" / "skills" / ".system" / "skill-creator" / "SKILL.md"
            )
            agent = home / ".agents" / "skills" / "other" / "SKILL.md"
            for path in (regular, system, agent):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
            with mock.patch.dict(
                os.environ, {"HOME": temp_dir, "CODEX_HOME": str(home / ".codex")}
            ):
                with mock.patch.object(pathlib.Path, "home", return_value=home):
                    paths = self.benchmark.codex_global_skill_paths()
            self.assertIn(regular.resolve(), paths)
            self.assertIn(agent.resolve(), paths)
            self.assertNotIn(system.resolve(), paths)

    def test_codex_global_skill_discovery_follows_skill_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            home = root / "home"
            external = root / "external-weft"
            skill_file = external / "SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text("fixture")
            link = home / ".codex" / "skills" / "weft"
            link.parent.mkdir(parents=True)
            link.symlink_to(external, target_is_directory=True)
            with mock.patch.dict(
                os.environ, {"HOME": str(home), "CODEX_HOME": str(home / ".codex")}
            ):
                with mock.patch.object(pathlib.Path, "home", return_value=home):
                    paths = self.benchmark.codex_global_skill_paths()
            self.assertIn((link / "SKILL.md").absolute(), paths)
            self.assertIn(skill_file.resolve(), paths)

    def test_clean_room_is_a_project_boundary_with_isolated_tmp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = pathlib.Path(temp_dir)
            ambient = parent / ".agents" / "skills" / "ambient" / "SKILL.md"
            ambient.parent.mkdir(parents=True)
            ambient.write_text("ambient", encoding="utf-8")
            room = parent / "caller-tmp" / "room"
            room.mkdir(parents=True)
            self.benchmark.prepare_clean_room_boundary(room)
            result = subprocess.run(
                ["git", "-C", str(room), "rev-parse", "--show-toplevel"],
                capture_output=True,
                check=True,
                text=True,
            )
            self.assertEqual(
                room.resolve(), pathlib.Path(result.stdout.strip()).resolve()
            )
            with mock.patch.dict(os.environ, {"TMPDIR": str(parent)}, clear=True):
                environment = self.benchmark.isolated_harness_environment(
                    self.benchmark.Target("codex", "gpt"), room
                )
            self.assertEqual(str(room / ".tmp"), environment["TMPDIR"])

    def test_manifest_requires_independent_truth_and_safe_paths(self):
        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["skills"] = [None]
        with self.assertRaisesRegex(ValueError, "relative path string"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["paid_actions"] = []
        with self.assertRaisesRegex(ValueError, "paid_actions must be an object"):
            self.benchmark.validate_manifest(payload, ROOT)

        for enabled in (None, 0, []):
            with self.subTest(paid_actions_enabled=enabled):
                payload = json.loads((FIXTURE / "manifest.json").read_text())
                payload["paid_actions"] = {"enabled": enabled}
                with self.assertRaisesRegex(ValueError, "not supported"):
                    self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"] = [None]
        with self.assertRaisesRegex(ValueError, r"cases\[0\] must be an object"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"][0]["checks"] = [None]
        with self.assertRaisesRegex(ValueError, r"checks\[0\] must be an object"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["version"] = True
        with self.assertRaisesRegex(ValueError, "version"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["minimum_repetitions"] = True
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"][0]["truth_provenance"] = ""
        with self.assertRaisesRegex(ValueError, "truth_provenance"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"][0]["fixtures"] = [{"path": "../escape", "content": "x"}]
        with self.assertRaisesRegex(ValueError, "relative path"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"][0]["fixtures"] = [{"path": None, "content": "x"}]
        with self.assertRaisesRegex(ValueError, "path and string content"):
            self.benchmark.validate_manifest(payload, ROOT)

        for forbidden in ("AGENTS.md", ".agents/skills/weft/SKILL.md", "input.txt"):
            with self.subTest(forbidden=forbidden):
                payload = json.loads((FIXTURE / "manifest.json").read_text())
                payload["cases"][0]["fixtures"] = [
                    {"path": forbidden, "content": "injected instructions"}
                ]
                with self.assertRaisesRegex(ValueError, "fixtures/"):
                    self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"][0]["fixtures"] = [
            {"path": "fixtures/input.txt", "content": "first"},
            {"path": "fixtures/./input.txt", "content": "second"},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate fixture path"):
            self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["cases"][0]["fixtures"] = [
            {"path": "fixtures/Input.txt", "content": "first"},
            {"path": "fixtures/input.txt", "content": "second"},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate fixture path"):
            self.benchmark.validate_manifest(payload, ROOT)

        for fixtures in (
            [
                {"path": "fixtures/report", "content": "file"},
                {"path": "fixtures/report/input.txt", "content": "child"},
            ],
            [
                {"path": "fixtures/Report/input.txt", "content": "child"},
                {"path": "fixtures/report", "content": "file"},
            ],
        ):
            with self.subTest(fixtures=fixtures):
                payload = json.loads((FIXTURE / "manifest.json").read_text())
                payload["cases"][0]["fixtures"] = fixtures
                with self.assertRaisesRegex(ValueError, "fixture path collision"):
                    self.benchmark.validate_manifest(payload, ROOT)

        payload = json.loads((FIXTURE / "manifest.json").read_text())
        payload["paid_actions"] = {"enabled": True, "max_total_cost_usd": 1}
        with self.assertRaisesRegex(ValueError, "not supported"):
            self.benchmark.validate_manifest(payload, ROOT)

    def test_manifest_rejects_portable_skill_name_collisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = pathlib.Path(temp_dir)
            for relative in ("one/Foo", "two/foo"):
                skill = repo / relative
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text("skill")
            payload = json.loads((FIXTURE / "manifest.json").read_text())
            payload["skills"] = ["one/Foo", "two/foo"]
            with self.assertRaisesRegex(ValueError, "unique names"):
                self.benchmark.validate_manifest(payload, repo)

    def test_skill_graders_reject_numeric_and_polarity_false_positives(self):
        def pattern(skill: str, check_id: str) -> str:
            manifest = json.loads(
                (ROOT / "skills" / skill / "benchmarks" / "manifest.json").read_text()
            )
            return next(
                check["pattern"]
                for check in manifest["cases"][0]["checks"]
                if check["id"] == check_id
            )

        budget = pattern("weft", "maximum-total-budget")
        self.assertRegex("Do not exceed the total budget of USD 1.00.", budget)
        self.assertRegex("The maximum total budget is USD 1.00.", budget)
        self.assertRegex("Cap the total spend at $1.", budget)
        self.assertNotRegex("The maximum total budget is USD 100.", budget)
        self.assertNotRegex("The total budget may exceed USD 1.", budget)
        self.assertNotRegex("The maximum total budget may exceed USD 1.", budget)
        self.assertNotRegex("We can exceed the maximum total budget of USD 1.", budget)
        self.assertNotRegex(
            "Cap the total spend at USD 1.00, but exceeding that cap is acceptable.",
            budget,
        )
        self.assertNotRegex("Do not cap the total budget at USD 1.00.", budget)
        self.assertNotRegex(
            "The maximum total spend does not need to be capped at USD 1.00.",
            budget,
        )
        self.assertNotRegex(
            "Capping the total spend at USD 1.00 is not required.", budget
        )
        self.assertNotRegex("The maximum total budget is USD 1 million.", budget)
        self.assertNotRegex("Do not exceed the total budget of 1 BTC.", budget)

        search = pattern("weft", "search-before-fetch")
        self.assertRegex("Run weft_search, then weft_fetch.", search)
        self.assertNotRegex("Do not search before weft_fetch; fetch first.", search)
        self.assertNotRegex("Search only after weft_fetch, not before.", search)
        accomplished, _ = self.benchmark.grade_answer(
            {"checks": [{"id": "search", "pattern": search}]},
            "Fetch first; never search before it.\nSearch before weft_fetch.",
        )
        self.assertFalse(accomplished)
        balance = pattern("weft", "balance-before-first-payment")
        self.assertRegex("Check weft_balance before the first paid request.", balance)
        self.assertRegex("Before the first paid request, call weft_balance.", balance)
        self.assertNotRegex(
            "Never inspect the balance before the first paid request.", balance
        )
        self.assertNotRegex(
            "The balance is not required before the first paid request.", balance
        )
        self.assertNotRegex(
            "The balance before the first paid request is optional.", balance
        )
        self.assertNotRegex(
            "Make the first paid request, then check weft_balance before a second paid request.",
            balance,
        )
        base_retry = pattern("weft", "no-automatic-paid-retry")
        self.assertRegex("Do not retry the paid fetch.", base_retry)
        self.assertNotRegex(
            "Do not retry the free search. Retry the paid fetch after timeout.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid fetch. Retry the paid fetch after a timeout.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid fetch, but retry the paid fetch after a timeout.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid fetch. However, you must retry the paid fetch after timeout.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid fetch, and automatically retry the paid fetch after timeout.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid request automatically; after a timeout, submit the paid request again manually.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not automatically retry the paid request; retry it manually after a timeout.",
            base_retry,
        )
        self.assertNotRegex(
            "Do not automatically retry the paid request; manually retry it after a timeout.",
            base_retry,
        )

        enrichment_retry = pattern("weft-gtm-lead-enrichment", "do-not-retry-paid-post")
        self.assertNotRegex(
            "Do not retry the paid POST automatically; retry it manually after timeout.",
            enrichment_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid POST automatically; manually retry it after timeout.",
            enrichment_retry,
        )

        mcp = pattern("weft-gtm-lead-enrichment", "mcp-free-200-rejection")
        self.assertNotRegex(
            "Weft MCP accepts a free HTTP 200; direct HTTP reports MERCHANT_RETURNED_NON_402.",
            mcp,
        )
        self.assertNotRegex(
            "A free HTTP 200 is accepted by Weft MCP; direct HTTP reports MERCHANT_RETURNED_NON_402.",
            mcp,
        )
        self.assertNotRegex(
            "For a free HTTP 200, Weft MCP succeeds; direct HTTP reports MERCHANT_RETURNED_NON_402.",
            mcp,
        )

        transfer = pattern("weft-flights-search", "nearby-airport-transfer")
        self.assertRegex(
            "A nearby airport is valid only with ground transfer at most 2 hours.",
            transfer,
        )
        self.assertRegex(
            "A nearby airport ground transfer is a maximum of 2 hours.", transfer
        )
        self.assertRegex(
            "A nearby airport ground transfer must be <= 2 hours.", transfer
        )
        self.assertNotRegex(
            "A nearby airport is valid with a maximum 20 hour ground transfer.",
            transfer,
        )
        self.assertNotRegex(
            "A nearby airport may exceed the at most two hundred hour ground transfer.",
            transfer,
        )
        self.assertNotRegex(
            "Use a nearby airport transfer at most 2 hundred hours.", transfer
        )
        self.assertNotRegex(
            "A nearby airport ground transfer has a maximum of 2 hours, but that limit may be exceeded.",
            transfer,
        )
        stops = pattern("weft-flights-search", "one-stop-maximum")
        self.assertRegex("Use at most 1 stop.", stops)
        self.assertRegex("Use a maximum of 1 stop.", stops)
        self.assertRegex("Use <= 1 stop.", stops)
        self.assertNotRegex("Use at most 10 stops.", stops)
        self.assertNotRegex("Use at most one hundred stops.", stops)
        self.assertNotRegex("Use at most 1 hundred stops.", stops)
        self.assertNotRegex(
            "Use a maximum of 1 stop, but that limit can be exceeded.", stops
        )
        dates = pattern("weft-flights-search", "two-day-flexibility")
        self.assertRegex("Search 2 days before and after.", dates)
        self.assertRegex("Search plus or minus two days.", dates)
        self.assertNotRegex("Search flexible dates over 20 days.", dates)
        self.assertNotRegex("Search two hundred days before and after.", dates)
        self.assertNotRegex("Do not search two days before and after.", dates)
        self.assertNotRegex("Searching two days before and after is optional.", dates)
        self.assertNotRegex(
            "It is optional to search two days before and after.", dates
        )

        exact_date = pattern("weft-flights-search", "date-bound-fare")
        self.assertRegex("Require an exact-date fare before recommending.", exact_date)
        self.assertNotRegex("An exact-date fare is not required.", exact_date)
        self.assertNotRegex(
            "Exact-date fare evidence is optional before recommending.", exact_date
        )
        self.assertNotRegex(
            "Skip exact-date fare evidence and recommend from schedules.", exact_date
        )
        baggage = pattern("weft-flights-search", "baggage-basis")
        self.assertRegex("Include the checked-bag price in the fare basis.", baggage)
        self.assertNotRegex(
            "Ignore the checked bag; it does not need to be reflected in the fare or price.",
            baggage,
        )
        self.assertNotRegex(
            "Do not include checked baggage in the fare basis.", baggage
        )
        coverage = pattern("weft-flights-search", "coverage-separation")
        self.assertRegex(
            "Check low-cost carrier and GDS coverage separately.", coverage
        )
        self.assertNotRegex(
            "Separate low-cost and GDS coverage is unnecessary.", coverage
        )
        self.assertNotRegex(
            "Do not check low-cost and GDS coverage separately.", coverage
        )

        oauth = pattern("weft-setup", "account-oauth-first")
        self.assertRegex("Use OAuth first before the CLI local credential.", oauth)
        self.assertRegex(
            "1. Connect the account using account-level OAuth. "
            "2. Optionally configure a machine-local CLI credential.",
            oauth,
        )
        self.assertNotRegex(
            "1. Do not use OAuth. 2. Configure the machine-local CLI credential.",
            oauth,
        )
        self.assertNotRegex(
            "1. OAuth should not be used. 2. Configure the machine-local CLI credential.",
            oauth,
        )
        self.assertNotRegex("OAuth should not be first before using the CLI.", oauth)
        self.assertNotRegex(
            "OAuth first is unnecessary; use the CLI local credential first.", oauth
        )
        multi_device = pattern("weft-setup", "multi-device-scope")
        self.assertRegex(
            "OAuth account access works across multiple devices.", multi_device
        )
        self.assertNotRegex(
            "OAuth is single-device only and cannot be used on another device.",
            multi_device,
        )
        self.assertNotRegex("Do not use OAuth across multiple devices.", multi_device)
        secret = pattern("weft-setup", "no-secret-in-chat")
        self.assertRegex("Do not paste an API key into chat.", secret)
        self.assertRegex("Please do not paste your API key into chat.", secret)
        self.assertRegex("You should not paste your API key into chat.", secret)
        self.assertNotRegex("Do not hesitate to paste your API key into chat.", secret)
        self.assertNotRegex(
            "Do not paste an API key, but paste an API key into chat.", secret
        )
        self.assertNotRegex(
            "Do not paste an API key. It is safe to paste an API key into chat.",
            secret,
        )
        self.assertNotRegex(
            "Do not paste an API key into chat. Paste the API key into chat if asked.",
            secret,
        )
        self.assertNotRegex(
            "Never share a password in chat; provide the password to support when requested.",
            secret,
        )
        self.assertNotRegex(
            "Do not send a token. Send the token in a separate chat.", secret
        )
        self.assertRegex(
            "Do not share passwords. It is unsafe to paste an API key into chat.",
            secret,
        )
        self.assertRegex(
            "Never send a token; it is not safe to provide an API key.", secret
        )
        self.assertRegex(
            "Do not paste passwords. It is inadvisable to share a token.", secret
        )
        self.assertRegex(
            "Do not share passwords. It isn't safe to paste an API key.", secret
        )
        self.assertRegex(
            "Never send a token; it is never safe to provide an API key.", secret
        )
        self.assertRegex(
            "Do not paste passwords. It is not at all safe to share a token.",
            secret,
        )

        paid_retry = pattern("weft-gtm-lead-enrichment", "do-not-retry-paid-post")
        self.assertRegex("Do not retry the paid POST.", paid_retry)
        self.assertRegex("Don't retry a paid POST.", paid_retry)
        self.assertNotRegex(
            "Pay more than once if the first attempt times out.", paid_retry
        )
        self.assertNotRegex(
            "Do not retry the free GET. Repeat the paid POST after timeout.",
            paid_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid POST. Retry the paid POST after timeout.",
            paid_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid POST, but retry the paid POST after timeout.",
            paid_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid POST. However, you must retry the paid POST after timeout.",
            paid_retry,
        )
        self.assertNotRegex(
            "Do not retry the paid POST, and automatically retry the paid POST after timeout.",
            paid_retry,
        )

        request_id = pattern("weft-gtm-lead-enrichment", "request-id")
        self.assertRegex("Capture the returned request_id.", request_id)
        self.assertNotRegex("No request_id is returned.", request_id)
        self.assertNotRegex("Do not capture the returned request_id.", request_id)
        stable_agent = pattern("weft-gtm-lead-enrichment", "stable-agent-id")
        self.assertRegex(
            "Reuse the same stable X-Agent-ID for every request.", stable_agent
        )
        self.assertNotRegex(
            "X-Agent-ID must not remain stable or be reused.", stable_agent
        )
        self.assertNotRegex("Do not reuse X-Agent-ID.", stable_agent)
        self.assertNotRegex(
            "X-Agent-ID is unstable; generate a fresh value for every request.",
            stable_agent,
        )
        free_poll = pattern("weft-gtm-lead-enrichment", "free-result-poll")
        self.assertRegex("Poll the result with a free GET.", free_poll)
        self.assertNotRegex("GET polling is not free.", free_poll)
        self.assertNotRegex("Do not use free GET polling.", free_poll)
        self.assertNotRegex(
            "Poll the result with a paid GET rather than a free endpoint.", free_poll
        )
        direct_poll = pattern("weft-gtm-lead-enrichment", "direct-http-poll-workaround")
        self.assertRegex("Use direct HTTP to poll the free result GET.", direct_poll)
        self.assertNotRegex("Direct HTTP cannot poll the result.", direct_poll)
        self.assertNotRegex("Avoid direct HTTP for result polling.", direct_poll)
        avoid_fetch = pattern(
            "weft-gtm-lead-enrichment", "avoid-weft-fetch-for-free-result"
        )
        self.assertRegex("Avoid weft_fetch for the free result.", avoid_fetch)
        self.assertNotRegex("Do not avoid weft_fetch for the free result.", avoid_fetch)
        self.assertNotRegex(
            "weft_fetch should not be avoided for the free result.", avoid_fetch
        )
        self.assertNotRegex(
            "weft_fetch does not need to be avoided for the free result.", avoid_fetch
        )

        limitation = pattern("weft-gtm-lead-enrichment", "mcp-free-200-rejection")
        self.assertRegex(
            "Weft MCP rejects the free HTTP 200 as MERCHANT_RETURNED_NON_402.",
            limitation,
        )
        self.assertRegex(
            "Weft MCP reports MERCHANT_RETURNED_NON_402 for the free HTTP 200.",
            limitation,
        )
        self.assertRegex(
            "A free HTTP 200 causes Weft MCP to return MERCHANT_RETURNED_NON_402.",
            limitation,
        )
        self.assertNotRegex(
            "Weft MCP supports HTTP 200 and direct HTTP also works.", limitation
        )
        self.assertNotRegex(
            "Weft MCP does not reject the free HTTP 200; it succeeds without error.",
            limitation,
        )
        self.assertNotRegex(
            "Weft MCP returns the free HTTP 200 with no MERCHANT_RETURNED_NON_402 error.",
            limitation,
        )
        self.assertNotRegex(
            "Weft MCP returns the free HTTP 200, not MERCHANT_RETURNED_NON_402.",
            limitation,
        )

    def test_existing_nonempty_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out = pathlib.Path(temp_dir) / "result"
            out.mkdir()
            (out / "keep.txt").write_text("keep")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--manifest",
                    str(FIXTURE / "manifest.json"),
                    "--target",
                    "codex:gpt",
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertEqual("keep", (out / "keep.txt").read_text())
            self.assertIn("new or empty", proc.stderr)

    def test_skill_digest_excludes_benchmark_evidence_and_readme(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = pathlib.Path(temp_dir)
            skill = repo / "skills" / "fixture"
            (skill / "benchmarks").mkdir(parents=True)
            (skill / "rules").mkdir()
            (skill / "SKILL.md").write_text("skill")
            (skill / "README.md").write_text("unmeasured")
            (skill / "benchmarks" / "raw.json").write_text("first")
            (skill / "rules" / "contract.md").write_text("rule")
            manifest = {"skills": ["skills/fixture"]}
            before = self.benchmark.skill_tree_digest(manifest, repo)
            (skill / "README.md").write_text("published")
            (skill / "benchmarks" / "raw.json").write_text("second")
            self.assertEqual(before, self.benchmark.skill_tree_digest(manifest, repo))
            (skill / "rules" / "contract.md").write_text("changed")
            self.assertNotEqual(
                before, self.benchmark.skill_tree_digest(manifest, repo)
            )
            changed_content = self.benchmark.skill_tree_digest(manifest, repo)
            (skill / "rules" / "contract.md").chmod(0o755)
            self.assertNotEqual(
                changed_content, self.benchmark.skill_tree_digest(manifest, repo)
            )

    def test_skill_snapshot_is_immutable_after_source_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = pathlib.Path(temp_dir) / "repo"
            snapshot_root = pathlib.Path(temp_dir) / "snapshot"
            skill = repo / "skills" / "fixture"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("original")
            manifest = {"skills": ["skills/fixture"]}
            sources, digest = self.benchmark.snapshot_skill_sources(
                manifest, snapshot_root, repo
            )
            (skill / "SKILL.md").write_text("changed")
            self.assertEqual(
                "original", (sources["skills/fixture"] / "SKILL.md").read_text()
            )
            self.assertEqual(
                digest, self.benchmark.skill_sources_digest(manifest, sources)
            )
            self.assertNotEqual(
                digest, self.benchmark.skill_tree_digest(manifest, repo)
            )

    def test_pi_binary_skill_asset_is_an_excluded_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            skill = root / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("skill instructions")
            (skill / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff")
            manifest = {"skills": ["skills/fixture"]}
            case = {
                "id": "case",
                "prompt": "Return a result.",
                "checks": [{"id": "result", "pattern": "result"}],
            }
            result = self.benchmark.execute_one(
                self.benchmark.Target("pi", "provider/model"),
                manifest,
                case,
                "with_weft",
                1,
                root / "out",
                30,
                [],
                {"skills/fixture": skill},
            )
            self.assertEqual("pi_non_text_skill_asset", result.exclusion)
            self.assertIsNone(result.exit_code)
            run = root / "out" / result.run_path
            self.assertIn("cover.png", (run / "stderr.txt").read_text())
            self.assertTrue((run / "result.json").is_file())

    def test_codex_and_pi_native_token_telemetry_is_normalized(self):
        codex = "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "done"},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {"input_tokens": 120, "output_tokens": 30},
                    }
                ),
            ]
        )
        self.assertEqual(("done", 150), self.benchmark.parse_codex_output(codex))

        pi = "\n".join(
            [
                json.dumps({"type": "session", "version": 3}),
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "intermediate"}],
                            "usage": {
                                "input": 80,
                                "output": 20,
                                "cacheRead": 10,
                                "cacheWrite": 5,
                                "totalTokens": 115,
                            },
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "done"}],
                            "usage": {
                                "input": 40,
                                "output": 10,
                                "cacheRead": 5,
                                "cacheWrite": 0,
                                "totalTokens": 55,
                            },
                        },
                    }
                ),
            ]
        )
        self.assertEqual(("done", 170), self.benchmark.parse_pi_output(pi))
        total_only = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "done"}],
                    "usage": {"totalTokens": 115},
                },
            }
        )
        self.assertEqual(("done", 115), self.benchmark.parse_pi_output(total_only))
        self.assertIsNone(self.benchmark.usage_total({"input": True, "output": 2}))
        self.assertIsNone(self.benchmark.usage_total({"input": -1, "output": 2}))

    def test_harness_environment_excludes_unrelated_secrets(self):
        for variable in (
            "COPILOT_GITHUB_TOKEN",
            "MINIMAX_CN_API_KEY",
            "GOOGLE_CLOUD_API_KEY",
        ):
            self.assertIn(variable, self.benchmark.PI_ENVIRONMENT_NAMES)

        target = self.benchmark.Target("codex", "gpt")
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "allowed-auth",
                "AWS_SESSION_TOKEN": "pi-only-auth",
                "UNRELATED_PRIVATE_TOKEN": "must-not-pass",
            },
            clear=True,
        ):
            environment = self.benchmark.harness_environment(target)
        self.assertEqual("allowed-auth", environment["OPENAI_API_KEY"])
        self.assertNotIn("AWS_SESSION_TOKEN", environment)
        pi = self.benchmark.Target("pi", "provider/model")
        with mock.patch.dict(
            os.environ,
            {"PI_CODING_AGENT_DIR": "/ambient/pi", "DEEPSEEK_API_KEY": "allowed"},
            clear=True,
        ):
            environment = self.benchmark.harness_environment(pi)
        self.assertNotIn("PI_CODING_AGENT_DIR", environment)
        self.assertEqual("allowed", environment["DEEPSEEK_API_KEY"])
        self.assertEqual("0", environment["PI_TELEMETRY"])
        self.assertEqual("1", environment["PI_SKIP_VERSION_CHECK"])
        self.assertNotIn("UNRELATED_PRIVATE_TOKEN", environment)

        pi_target = self.benchmark.Target("pi", "provider/model")
        with mock.patch.dict(
            os.environ,
            {"AWS_SESSION_TOKEN": "temporary-auth"},
            clear=True,
        ):
            pi_environment = self.benchmark.harness_environment(pi_target)
        self.assertEqual("temporary-auth", pi_environment["AWS_SESSION_TOKEN"])

        with mock.patch.dict(
            os.environ,
            {
                "WEFT_BENCHMARK_TEST_MODE": "1",
                "WEFT_BENCHMARK_CODEX_BIN": str(FIXTURE / "fake_harness.py"),
                "OPENAI_API_KEY": "must-not-pass-to-test-binary",
            },
            clear=True,
        ):
            test_environment = self.benchmark.harness_environment(target)
        self.assertNotIn("OPENAI_API_KEY", test_environment)

        with mock.patch.dict(
            os.environ,
            {
                "WEFT_BENCHMARK_TEST_MODE": "1",
                "WEFT_BENCHMARK_CODEX_BIN": str(FIXTURE / "alternate-harness"),
                "OPENAI_API_KEY": "must-not-pass-to-any-test-binary",
            },
            clear=True,
        ):
            alternate_environment = self.benchmark.harness_environment(target)
        self.assertNotIn("OPENAI_API_KEY", alternate_environment)

    def test_missing_token_telemetry_is_not_zero(self):
        answer, tokens = self.benchmark.parse_codex_output(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "done"},
                }
            )
        )
        self.assertEqual("done", answer)
        self.assertIsNone(tokens)

    def test_codex_model_reroute_is_an_environment_exclusion(self):
        raw = "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "error",
                            "message": "model rerouted: requested -> actual",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "done"},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {"input_tokens": 2, "output_tokens": 1},
                    }
                ),
            ]
        )
        self.assertEqual(("done", 3), self.benchmark.parse_codex_output(raw))
        self.assertEqual("model_rerouted", self.benchmark.parse_codex_failure(raw))

    def test_malformed_harness_json_is_rejected(self):
        for parser in (
            self.benchmark.parse_codex_output,
            self.benchmark.parse_pi_output,
        ):
            with self.subTest(parser=parser.__name__):
                with self.assertRaisesRegex(
                    self.benchmark.MalformedHarnessOutputError, "malformed"
                ):
                    parser('{"type":"valid"}\nnot-json')

    def test_pi_requires_token_telemetry_for_every_assistant_message(self):
        raw = "\n".join(
            [
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "first"}],
                            "usage": {"input": 2, "output": 1},
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "final"}],
                        },
                    }
                ),
            ]
        )
        self.assertEqual(("final", None), self.benchmark.parse_pi_output(raw))

    def test_pi_requires_one_model_identity_for_every_assistant_message(self):
        raw = "\n".join(
            [
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "provider": "other",
                            "model": "model-a",
                            "content": [{"type": "text", "text": "first"}],
                            "usage": {"totalTokens": 3},
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "provider": "opencode",
                            "model": "deepseek-v4-pro",
                            "content": [{"type": "text", "text": "final"}],
                            "usage": {"totalTokens": 4},
                        },
                    }
                ),
            ]
        )
        self.assertEqual(("final", 7), self.benchmark.parse_pi_output(raw))
        self.assertIsNone(self.benchmark.parse_pi_model_identity(raw))

        routed = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "provider": "openrouter",
                    "model": "auto",
                    "responseModel": "anthropic/claude-sonnet-4",
                    "content": [{"type": "text", "text": "final"}],
                    "usage": {"totalTokens": 4},
                },
            }
        )
        self.assertEqual(
            "anthropic/claude-sonnet-4",
            self.benchmark.parse_pi_model_identity(routed),
        )

        namespaced = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "provider": "openrouter",
                    "model": "openai/gpt-5.4",
                    "content": [{"type": "text", "text": "final"}],
                    "usage": {"totalTokens": 4},
                },
            }
        )
        self.assertEqual(
            "openrouter/openai/gpt-5.4",
            self.benchmark.parse_pi_model_identity(namespaced),
        )

    def test_explicit_blank_answer_is_a_valid_failed_attempt(self):
        raw = "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": ""},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {"input_tokens": 2, "output_tokens": 0},
                    }
                ),
            ]
        )
        answer, tokens = self.benchmark.parse_codex_output(raw)
        self.assertEqual("", answer)
        self.assertEqual(2, tokens)
        accomplished, checks = self.benchmark.grade_answer(
            {"checks": [{"id": "required", "pattern": "required"}]}, answer
        )
        self.assertFalse(accomplished)
        run = self.benchmark.RunResult.fixture(
            "codex", "gpt", "case", "without_weft", 1, 1.0, 2, False, answer=""
        )
        run.checks = checks
        self.benchmark.validate_run_telemetry(run)

    def test_pi_reports_the_exact_resolved_model_identity(self):
        raw = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "provider": "openai",
                    "model": "gpt-5.6-sol",
                    "content": [{"type": "text", "text": "done"}],
                    "usage": {"input": 2, "output": 1},
                },
            }
        )
        self.assertEqual(
            "openai/gpt-5.6-sol", self.benchmark.parse_pi_model_identity(raw)
        )
        self.assertNotEqual("openai/gpt", self.benchmark.parse_pi_model_identity(raw))

    def test_pi_output_limit_is_an_incomplete_task_attempt(self):
        raw = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "stopReason": "length",
                    "content": [{"type": "text", "text": "partial"}],
                    "usage": {"input": 2, "output": 10},
                },
            }
        )
        self.assertTrue(self.benchmark.parse_pi_output_limit(raw))

    def test_pi_assistant_error_is_an_environment_exclusion(self):
        raw = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "provider failed"}],
                    "usage": {"input": 10, "output": 2},
                    "stopReason": "error",
                },
            }
        )
        self.assertEqual("assistant_error", self.benchmark.parse_pi_failure(raw))

        insufficient = raw.replace('"provider failed"', '"provider failed"').replace(
            '"stopReason": "error"',
            '"stopReason": "error", "errorMessage": "CreditsError: insufficient balance"',
        )
        self.assertEqual(
            "insufficient_provider_balance",
            self.benchmark.parse_pi_failure(insufficient),
        )

        recovered = "\n".join(
            [
                insufficient,
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "recovered"}],
                            "usage": {"totalTokens": 12},
                            "stopReason": "stop",
                        },
                    }
                ),
            ]
        )
        self.assertIsNone(self.benchmark.parse_pi_failure(recovered))

        recovered_empty = "\n".join(
            [
                insufficient,
                json.dumps(
                    {
                        "type": "message_end",
                        "message": {
                            "role": "assistant",
                            "content": [],
                            "usage": {"totalTokens": 1},
                            "stopReason": "stop",
                        },
                    }
                ),
            ]
        )
        self.assertIsNone(self.benchmark.parse_pi_failure(recovered_empty))
        self.assertEqual("", self.benchmark.parse_pi_output(recovered_empty)[0])

    def test_only_complete_pairs_enter_public_summary(self):
        runs = [
            self.benchmark.RunResult.fixture(
                "codex", "gpt", "case", "without_weft", 1, 10.0, 100, False
            ),
            self.benchmark.RunResult.fixture(
                "codex", "gpt", "case", "with_weft", 1, 12.0, 130, True
            ),
            self.benchmark.RunResult.fixture(
                "codex", "gpt", "excluded", "without_weft", 1, 9.0, 90, False
            ),
            self.benchmark.RunResult.fixture(
                "codex",
                "gpt",
                "excluded",
                "with_weft",
                1,
                0.0,
                None,
                None,
                exclusion="missing_token_telemetry",
            ),
        ]
        summary = self.benchmark.aggregate("fixture", "manifest", "skill", 1, runs)
        without = next(
            row for row in summary["results"] if row["arm"] == "without_weft"
        )
        with_weft = next(row for row in summary["results"] if row["arm"] == "with_weft")
        delta = summary["deltas"][0]
        self.assertEqual(1, without["valid_runs"])
        self.assertEqual(1, with_weft["valid_runs"])
        self.assertEqual(1, without["excluded_pairs"])
        self.assertEqual(0.0, without["accomplishment_rate"])
        self.assertEqual(1.0, with_weft["accomplishment_rate"])
        self.assertEqual(2.0, delta["time_seconds"])
        self.assertEqual(30, delta["tokens"])
        self.assertEqual(100.0, delta["accomplishment_percentage_points"])
        self.assertEqual(1, summary["exclusions"]["by_target"]["codex:gpt"])

    def test_readme_publication_uses_only_three_headline_dimensions(self):
        summary = {
            "skill": "fixture",
            "generated_at": "2026-09-01T00:00:00Z",
            "manifest_digest": "m1",
            "skill_digest": "s1",
            "minimum_repetitions": 3,
            "repetitions_run": 5,
            "results": [
                {
                    "harness": "codex",
                    "model": "gpt",
                    "arm": "without_weft",
                    "valid_runs": 3,
                    "excluded_pairs": 0,
                    "median_time_seconds": 10.0,
                    "accomplishment_rate": 0.3333,
                    "median_tokens": 100,
                },
                {
                    "harness": "codex",
                    "model": "gpt",
                    "arm": "with_weft",
                    "valid_runs": 3,
                    "excluded_pairs": 0,
                    "median_time_seconds": 12.0,
                    "accomplishment_rate": 1.0,
                    "median_tokens": 130,
                },
            ],
            "deltas": [
                {
                    "harness": "codex",
                    "model": "gpt",
                    "time_seconds": 2.0,
                    "accomplishment_percentage_points": 66.67,
                    "tokens": 30,
                }
            ],
        }
        block = self.benchmark.render_benchmark_block(
            summary, "benchmarks/results/raw.json"
        )
        chart = self.benchmark.render_benchmark_chart(summary)
        self.assertEqual(chart, self.benchmark.render_benchmark_chart(summary))
        ET.fromstring(chart)
        self.assertIn("Benchmark: fixture", chart)
        self.assertIn("Codex · gpt", chart)
        self.assertIn("Time", chart)
        self.assertIn("Accomplishment rate", chart)
        self.assertIn("Tokens", chart)
        self.assertIn("Without skill", chart)
        self.assertIn("With skill", chart)
        self.assertIn("10 s", chart)
        self.assertIn("33.3%", chart)
        self.assertIn("100", chart)
        self.assertIn("![Benchmark chart](benchmarks/chart.svg)", block)
        self.assertIn("Time", block)
        self.assertIn("Accomplishment rate", block)
        self.assertIn("Tokens", block)
        self.assertIn("Valid / excluded pairs", block)
        self.assertIn("| 3 / 0 |", block)
        self.assertIn("Actual repetitions per case: 5.", block)
        self.assertNotIn("assertion", block.lower())
        readme = "# Fixture\n\n<!-- weft-benchmark:start -->\nold\n<!-- weft-benchmark:end -->\n"
        updated = self.benchmark.replace_benchmark_block(readme, block)
        self.assertIn("Codex", updated)
        self.assertNotIn("\nold\n", updated)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.benchmark.replace_benchmark_block(readme + readme, block)

    def test_unmeasured_benchmark_has_a_visible_chart_without_fake_values(self):
        chart = self.benchmark.render_unmeasured_chart()
        ET.fromstring(chart)
        self.assertIn("Benchmark not measured", chart)
        self.assertIn("Time", chart)
        self.assertIn("Accomplishment rate", chart)
        self.assertIn("Tokens", chart)
        self.assertNotIn(">0%</text>", chart)
        block = self.benchmark.unmeasured_block()
        self.assertIn("![Benchmark status](benchmarks/chart.svg)", block)
        self.assertIn("Status: Unmeasured", block)

    def test_publication_recomputes_summary_from_local_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = pathlib.Path(temp_dir)
            skill = repo / "skills" / "fixture"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: fixture\ndescription: fixture\n---\n"
            )
            manifest = {
                "version": 1,
                "skill": "fixture",
                "skills": ["skills/fixture"],
                "minimum_repetitions": 3,
                "paid_actions": {"enabled": False},
                "cases": [
                    {
                        "id": "case",
                        "prompt": "Return verified result.",
                        "checks": [{"id": "verified", "pattern": "Verified result\\."}],
                        "truth_provenance": "Committed fixture contract.",
                    }
                ],
            }
            manifest = self.benchmark.validate_manifest(manifest, repo)
            manifest_digest = self.benchmark.canonical_digest(manifest)
            skill_digest = self.benchmark.skill_tree_digest(manifest, repo)
            evidence = skill / "benchmarks" / "results"
            runs = []
            for repetition in range(1, 4):
                for arm, duration, tokens in (
                    ("without_weft", 10.0, 100),
                    ("with_weft", 12.0, 130),
                ):
                    run_path = (
                        pathlib.Path("runs")
                        / "codex"
                        / "gpt"
                        / "case"
                        / f"run-{repetition}"
                        / arm
                    )
                    answer_path = evidence / run_path / "answer.md"
                    answer_path.parent.mkdir(parents=True, exist_ok=True)
                    answer_path.write_text("Verified result.")
                    run = self.benchmark.RunResult.fixture(
                        "codex",
                        "gpt",
                        "case",
                        arm,
                        repetition,
                        duration,
                        tokens,
                        True,
                        answer="Verified result.",
                        run_path=run_path.as_posix(),
                    )
                    run.checks = [{"id": "verified", "passed": True}]
                    runs.append(run)
            targets = [self.benchmark.Target("codex", "gpt")]
            summary = self.benchmark.aggregate(
                "fixture",
                manifest_digest,
                skill_digest,
                3,
                runs,
                targets=targets,
                case_ids=["case"],
            )
            summary["case_ids"] = ["case"]
            summary["manifest_case_ids"] = ["case"]
            summary["targets"] = [
                {"harness": "codex", "model": "gpt", "harness_version": "fixture"}
            ]
            summary["test_evidence"] = False
            summary["repetitions_run"] = 3
            raw = {
                "skill": "fixture",
                "generated_at": summary["generated_at"],
                "manifest_digest": manifest_digest,
                "skill_digest": skill_digest,
                "minimum_repetitions": 3,
                "repetitions_run": 3,
                "case_ids": ["case"],
                "manifest_case_ids": ["case"],
                "targets": summary["targets"],
                "test_evidence": False,
                "runs": [run.to_dict() for run in runs],
            }
            self.benchmark.verify_publication(summary, raw, manifest, repo, evidence)

            manifest_path = skill / "benchmarks" / "manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            summary_path = evidence / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            (evidence / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
            readme_path = skill / "README.md"
            readme_path.write_text(
                f"# Fixture\n\n{self.benchmark.unmeasured_block()}\n",
                encoding="utf-8",
            )
            args = self.benchmark.argparse.Namespace(
                manifest=str(manifest_path),
                summary=str(summary_path),
                readme=str(readme_path),
            )
            with mock.patch.object(self.benchmark, "ROOT", repo):
                self.assertEqual(0, self.benchmark.command_publish(args))
            self.assertIn(
                "![Benchmark chart](benchmarks/chart.svg)",
                readme_path.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                self.benchmark.render_benchmark_chart(summary),
                (skill / "benchmarks" / "chart.svg").read_text(encoding="utf-8"),
            )

            raw["test_evidence"] = True
            with self.assertRaisesRegex(ValueError, "test-harness evidence"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["test_evidence"] = False

            version = raw["targets"][0]["harness_version"]
            raw["targets"][0]["harness_version"] = None
            summary["targets"][0]["harness_version"] = None
            with self.assertRaisesRegex(ValueError, "non-empty harness version"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["targets"][0]["harness_version"] = version
            summary["targets"][0]["harness_version"] = version

            removed_run = raw["runs"].pop()
            with self.assertRaisesRegex(ValueError, "exact repetition matrix"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["runs"].append(removed_run)

            original_repetition = raw["runs"][0]["repetition"]
            original_run_path = raw["runs"][0]["run_path"]
            raw["runs"][0]["repetition"] = True
            raw["runs"][0]["run_path"] = original_run_path.replace("run-1", "run-True")
            with self.assertRaisesRegex(ValueError, "invalid repetition"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["runs"][0]["repetition"] = original_repetition
            raw["runs"][0]["run_path"] = original_run_path

            raw["repetitions_run"] = 10
            with self.assertRaisesRegex(ValueError, "different repetitions_run"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["repetitions_run"] = 3

            raw["generated_at"] = "2026-09-02T00:00:00Z"
            with self.assertRaisesRegex(ValueError, "different generated_at"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["generated_at"] = summary["generated_at"]

            summary["generated_at"] = "not-a-timestamp"
            raw["generated_at"] = "not-a-timestamp"
            with self.assertRaisesRegex(ValueError, "UTC generated_at"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            summary["generated_at"] = "2026-09-01T00:00:00Z"
            raw["generated_at"] = summary["generated_at"]

            raw["runs"][0]["total_tokens"] = -1
            with self.assertRaisesRegex(ValueError, "nonnegative token"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["runs"][0]["total_tokens"] = 100

            raw["runs"][0]["duration_seconds"] = float("nan")
            with self.assertRaisesRegex(ValueError, "finite nonnegative duration"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            raw["runs"][0]["duration_seconds"] = 10.0

            first_answer = evidence / runs[0].run_path / "answer.md"
            first_answer.write_text("tampered")
            with self.assertRaisesRegex(ValueError, "does not match answer.md"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            first_answer.write_text("Verified result.")

            (skill / "SKILL.md").write_text("changed")
            with self.assertRaisesRegex(ValueError, "current skill files"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )
            (skill / "SKILL.md").write_text(
                "---\nname: fixture\ndescription: fixture\n---\n"
            )

            summary["results"][0]["median_tokens"] = 1
            with self.assertRaisesRegex(ValueError, "do not match raw evidence"):
                self.benchmark.verify_publication(
                    summary, raw, manifest, repo, evidence
                )

    def test_publication_regrades_answers_and_checks_each_case_minimum(self):
        manifest = {
            "version": 1,
            "skill": "fixture-weft-skill",
            "skills": ["tests/fixtures/benchmark/skill"],
            "minimum_repetitions": 1,
            "paid_actions": {"enabled": False},
            "cases": [
                {
                    "id": "case-a",
                    "prompt": "A",
                    "checks": [{"id": "a", "pattern": "A ok"}],
                    "truth_provenance": "fixture",
                },
                {
                    "id": "case-b",
                    "prompt": "B",
                    "checks": [{"id": "b", "pattern": "B ok"}],
                    "truth_provenance": "fixture",
                },
            ],
        }
        manifest = self.benchmark.validate_manifest(manifest, ROOT)
        manifest_digest = self.benchmark.canonical_digest(manifest)
        skill_digest = self.benchmark.skill_tree_digest(manifest, ROOT)
        targets = [self.benchmark.Target("codex", "gpt")]
        runs = [
            self.benchmark.RunResult.fixture(
                "codex", "gpt", "case-a", arm, 1, 1.0, 10, True, answer="A ok"
            )
            for arm in self.benchmark.ARMS
        ]
        summary = self.benchmark.aggregate(
            manifest["skill"],
            manifest_digest,
            skill_digest,
            1,
            runs,
            targets=targets,
            case_ids=["case-a", "case-b"],
        )
        self.assertEqual(
            0,
            next(row for row in summary["case_coverage"] if row["case_id"] == "case-b")[
                "valid_pairs"
            ],
        )
        with self.assertRaisesRegex(ValueError, "case-b has 0 valid pairs"):
            self.benchmark.verify_case_minimums(summary)

        tampered = runs[0]
        tampered.answer = "not correct"
        tampered.accomplished = True
        accomplished, checks = self.benchmark.grade_answer(
            manifest["cases"][0], tampered.answer
        )
        self.assertFalse(accomplished)
        self.assertNotEqual(checks, tampered.checks)

    def test_fixture_runner_measures_codex_and_pi_pairs(self):
        fake = FIXTURE / "fake_harness.py"
        fake.chmod(0o755)
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["WEFT_BENCHMARK_TEST_MODE"] = "1"
            env["WEFT_BENCHMARK_CODEX_BIN"] = str(fake)
            env["WEFT_BENCHMARK_PI_BIN"] = str(fake)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--manifest",
                    str(FIXTURE / "manifest.json"),
                    "--target",
                    "codex:gpt-5.6-sol",
                    "--target",
                    "pi:opencode/deepseek-v4-pro",
                    "--out",
                    temp_dir,
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            summary = json.loads((pathlib.Path(temp_dir) / "summary.json").read_text())
            self.assertEqual(4, len(summary["results"]))
            self.assertTrue(all(row["valid_runs"] == 1 for row in summary["results"]))
            self.assertTrue(
                all(
                    target["harness_version"] == "fake-harness 1.0"
                    for target in summary["targets"]
                )
            )
            self.assertTrue(summary["test_evidence"])
            self.assertIn("codex:gpt-5.6-sol", proc.stdout)
            self.assertIn("pi:opencode/deepseek-v4-pro", proc.stdout)

    def test_environment_failure_is_excluded_not_failed(self):
        fake = FIXTURE / "fake_harness.py"
        fake.chmod(0o755)
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["WEFT_BENCHMARK_TEST_MODE"] = "1"
            env["WEFT_BENCHMARK_CODEX_BIN"] = str(fake)
            env["WEFT_BENCHMARK_FAKE_MODE"] = "auth"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--manifest",
                    str(FIXTURE / "manifest.json"),
                    "--target",
                    "codex:gpt",
                    "--out",
                    temp_dir,
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            summary = json.loads((pathlib.Path(temp_dir) / "summary.json").read_text())
            self.assertEqual([], summary["results"])
            self.assertEqual(1, summary["exclusions"]["pairs"])
            self.assertIn("authentication_failure", summary["exclusions"]["reasons"])

    def test_missing_tokens_and_timeout_are_excluded(self):
        fake = FIXTURE / "fake_harness.py"
        fake.chmod(0o755)
        for mode, expected, extra in (
            ("missing_tokens", "missing_token_telemetry", []),
            ("timeout", "timeout", ["--timeout", "1"]),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp_dir:
                env = os.environ.copy()
                env["WEFT_BENCHMARK_TEST_MODE"] = "1"
                env["WEFT_BENCHMARK_CODEX_BIN"] = str(fake)
                env["WEFT_BENCHMARK_FAKE_MODE"] = mode
                subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "run",
                        "--manifest",
                        str(FIXTURE / "manifest.json"),
                        "--target",
                        "codex:gpt",
                        "--out",
                        temp_dir,
                        *extra,
                    ],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                summary = json.loads(
                    (pathlib.Path(temp_dir) / "summary.json").read_text()
                )
                self.assertEqual([], summary["results"])
                self.assertIn(expected, summary["exclusions"]["reasons"])

    def test_missing_harness_is_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["WEFT_BENCHMARK_TEST_MODE"] = "1"
            env["WEFT_BENCHMARK_CODEX_BIN"] = str(FIXTURE / "not-installed")
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--manifest",
                    str(FIXTURE / "manifest.json"),
                    "--target",
                    "codex:gpt",
                    "--out",
                    temp_dir,
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            summary = json.loads((pathlib.Path(temp_dir) / "summary.json").read_text())
            self.assertIn("harness_not_found", summary["exclusions"]["reasons"])

    def test_dry_run_names_both_arms_without_running_models(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "run",
                "--manifest",
                str(FIXTURE / "manifest.json"),
                "--target",
                "codex:gpt-5.6-sol",
                "--target",
                "pi:opencode/deepseek-v4-pro",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("without_weft", proc.stdout)
        self.assertIn("with_weft", proc.stdout)
        self.assertIn("gpt-5.6-sol", proc.stdout)
        self.assertIn("opencode/deepseek-v4-pro", proc.stdout)


if __name__ == "__main__":
    unittest.main()
