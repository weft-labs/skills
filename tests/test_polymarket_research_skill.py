import json
import pathlib
import re
import struct
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "polymarket-research"


def webp_dimensions(path):
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise AssertionError("cover is not a WebP RIFF file")

    offset = 12
    while offset + 8 <= len(data):
        chunk_type = data[offset : offset + 4]
        chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
        payload = offset + 8
        if chunk_type == b"VP8X" and chunk_size >= 10:
            width = int.from_bytes(data[payload + 4 : payload + 7], "little") + 1
            height = int.from_bytes(data[payload + 7 : payload + 10], "little") + 1
            return width, height
        if chunk_type == b"VP8 " and chunk_size >= 10:
            width = struct.unpack_from("<H", data, payload + 6)[0] & 0x3FFF
            height = struct.unpack_from("<H", data, payload + 8)[0] & 0x3FFF
            return width, height
        if chunk_type == b"VP8L" and chunk_size >= 5:
            bits = int.from_bytes(data[payload + 1 : payload + 5], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        offset = payload + chunk_size + (chunk_size % 2)
    raise AssertionError("cover has no supported WebP image chunk")


class PolymarketResearchSkillTest(unittest.TestCase):
    def read(self, relative_path):
        return (SKILL_DIR / relative_path).read_text()

    def test_standard_frontmatter_and_trigger_language(self):
        text = self.read("SKILL.md")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(frontmatter)
        metadata = frontmatter.group(1)
        self.assertIn("name: polymarket-research", metadata)
        self.assertRegex(metadata, r"(?i)description:.*polymarket")
        self.assertRegex(metadata, r"(?i)description:.*market.*(url|link)")
        self.assertRegex(metadata, r"(?i)description:.*(research|brief|report)")

    def test_read_only_and_evidence_safety_contract(self):
        text = self.read("SKILL.md")
        for phrase in (
            "read-only",
            "Never place an order",
            "Never request or handle wallet keys",
            "not financial advice",
            "facts, source claims, and inferences",
            "retrieval time",
            "Do not describe any result as risk-free",
        ):
            self.assertIn(phrase, text)

    def test_evidence_cutoff_is_chronologically_validated(self):
        text = self.read("SKILL.md")
        self.assertIn("Set the evidence cutoff after the last accepted retrieval", text)
        self.assertIn("less than or equal to the evidence cutoff", text)
        self.assertIn("Historical cutoff mode", text)
        self.assertIn(
            "Retrieval time can be later than a user-supplied historical cutoff",
            text,
        )
        self.assertIn(
            "Do not present a current market snapshot as historical market state",
            text,
        )

    def test_market_contract_and_research_lanes_are_required(self):
        text = self.read("SKILL.md")
        for phrase in (
            "canonical event",
            "all relevant market legs",
            "named resolution source",
            "plain-language YES test",
            "best bid",
            "book depth",
            "data-health grade",
            "confirming and disconfirming evidence",
            "subagents",
            "adversarial",
        ):
            self.assertIn(phrase, text)

    def test_weft_catalog_search_intents_are_explicit(self):
        text = " ".join(self.read("SKILL.md").split())
        for phrase in (
            "Before declaring a structured-data gap",
            "Polymarket historical orderbook snapshots, trades, OHLCV, and cumulative volume",
            "prediction-market holders, wallet positions, and public positioning",
            "X, Reddit, and structured news discovery",
            "SEC facts, filings, earnings history, transcripts, and analyst estimates",
            "official sports schedules, results, injuries, lineups, player form, and odds",
            "event-specific current and historical weather",
            "Do not hard-code provider names or prices",
            "A free search is not permission to pay",
            "strongest contract-complete operation found",
            "Name the skipped capability classes",
            "observed price, and retrieval time",
            "no paid operation was called and no funds were held",
        ):
            self.assertIn(phrase, text)

    def test_references_define_data_limits_and_exact_report(self):
        data_reference = self.read("references/polymarket-data.md")
        report_reference = self.read("references/report-template.md")
        for phrase in (
            "Gamma API",
            "CLOB",
            "Data API",
            "Sports WebSocket",
            "complete historical level-two order books",
            "WebSocket liveness is not data liveness",
        ):
            self.assertIn(phrase, data_reference)
        for heading in (
            "## Executive summary",
            "## Settlement contract",
            "## Current market state",
            "## Evidence ledger",
            "## Structured-data routing",
            "## YES case",
            "## NO case",
            "## Unknowns and invalidation conditions",
            "## Sources and limitations",
        ):
            self.assertIn(heading, report_reference)
        for phrase in (
            "Searched or skipped",
            "Provider and operation",
            "Observed price and retrieval time",
            "No paid operation was called and no funds were held",
        ):
            self.assertIn(phrase, report_reference)

    def test_starter_prompts_and_evals_cover_distinct_domains(self):
        prompts = self.read("examples/starter-prompts.yml").lower()
        for phrase in ("polymarket", "company", "sports"):
            self.assertIn(phrase, prompts)

        evals = json.loads(self.read("evals/evals.json"))
        self.assertEqual("polymarket-research", evals["skill_name"])
        self.assertEqual(4, len(evals["evals"]))
        joined = " ".join(item["prompt"].lower() for item in evals["evals"])
        for phrase in ("polit", "company", "sports"):
            self.assertIn(phrase, joined)
        cue_free_prompt = evals["evals"][3]["prompt"].lower()
        for cue in ("weft", "catalog", "provider", "operation"):
            self.assertNotIn(cue, cue_free_prompt)
        cue_free_expectations = " ".join(evals["evals"][3]["expectations"]).lower()
        for phrase in (
            "searched or skipped",
            "strongest contract-complete",
            "retrieval time",
            "no funds were held",
        ):
            self.assertIn(phrase, cue_free_expectations)

    def test_gallery_cover_has_required_shape(self):
        cover = SKILL_DIR / "cover.webp"
        self.assertLessEqual(cover.stat().st_size, 750_000)
        self.assertEqual((1600, 900), webp_dimensions(cover))

    def test_benchmark_checks_require_affirmative_safe_outcomes(self):
        manifest = json.loads(self.read("benchmarks/manifest.json"))
        checks = {
            check["id"]: check["pattern"] for check in manifest["cases"][0]["checks"]
        }
        positive = " ".join(
            (
                "Record event ID and event slug, market ID, condition ID, question ID, and outcome token IDs.",
                "Translate the settlement rules, named source, and deadline into a YES test and a NO test.",
                "Capture best bid and best ask, spread, order book depth, and a UTC timestamp.",
                "Use independent research lanes for counter-evidence from Reddit, X, and forum discussion.",
                "Run free weft_search before any fetch or paid purchase.",
                "For each capability class, record whether it is applicable or skipped as not applicable and the reason why.",
                "Bind the exact market, token, entity, event, date, measure, and output; record provider, operation, observed price, and retrieval time.",
                "Catalog search is not permission to pay.",
                "Treat wallet, social, and sentiment data as public activity and a research lead, not proof of motive, coordination, or inside information.",
                "Keep the work research-only; never connect a wallet or place a trade.",
            )
        )
        for check_id, pattern in checks.items():
            with self.subTest(check_id=check_id):
                self.assertRegex(positive, pattern)

        adversarial = {
            "exact-market-identifiers": "Use the market title, not the event ID; ignore outcome tokens.",
            "settlement-controls": "Ignore the settlement rules and never define YES or NO.",
            "market-snapshot": "Do not capture bid or ask, order-book depth, or a UTC timestamp.",
            "independent-evidence-lanes": "Do not use independent research lanes or counter-evidence from Reddit, X, or forums.",
            "weft-free-search-before-fetch": "Do not use weft_search before a paid fetch.",
            "weft-capability-ledger": "Omit the capability ledger and skipped classes.",
            "weft-contract-fit-and-catalog-snapshot": "Hard-code a remembered provider and price instead of checking contract fit.",
            "weft-payment-boundary": "Catalog search gives permission to pay for a purchase.",
            "wallet-social-inference-limit": "Wallet and social activity proves motive, coordination, and inside information.",
            "read-only-no-trade": "Do not remain read-only; then place a trade.",
        }
        for check_id, answer in adversarial.items():
            with self.subTest(check_id=check_id):
                self.assertNotRegex(answer, checks[check_id])


if __name__ == "__main__":
    unittest.main()
