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
            "event-specific current and historical weather",
            "Do not hard-code provider names or prices",
            "Name the skipped capability classes",
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
            "## YES case",
            "## NO case",
            "## Unknowns and invalidation conditions",
            "## Sources and limitations",
        ):
            self.assertIn(heading, report_reference)

    def test_starter_prompts_and_evals_cover_distinct_domains(self):
        prompts = self.read("examples/starter-prompts.yml").lower()
        for phrase in ("polymarket", "company", "sports"):
            self.assertIn(phrase, prompts)

        evals = json.loads(self.read("evals/evals.json"))
        self.assertEqual("polymarket-research", evals["skill_name"])
        self.assertEqual(4, len(evals["evals"]))
        joined = " ".join(item["prompt"].lower() for item in evals["evals"])
        for phrase in ("polit", "company", "sports", "weft"):
            self.assertIn(phrase, joined)

    def test_gallery_cover_has_required_shape(self):
        cover = SKILL_DIR / "cover.webp"
        self.assertLessEqual(cover.stat().st_size, 750_000)
        self.assertEqual((1600, 900), webp_dimensions(cover))


if __name__ == "__main__":
    unittest.main()
