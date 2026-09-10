"""Local structure and decision-consistency checks for the competition draft.

Not a deployment check, full HTML validator, or verification of external links.
"""

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.sections = {}
        self.active_section = None
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "section":
            if self.active_section is not None:
                raise ValueError("Unexpected nested section")
            self.active_section = attrs["id"]
            self.sections[self.active_section] = []

    def handle_endtag(self, tag):
        if tag == "section":
            if self.active_section is None:
                raise ValueError("Unmatched section close")
            self.active_section = None

    def handle_data(self, data):
        if self.active_section is not None:
            self.sections[self.active_section].append(data)

    def section_text(self, section):
        return " ".join("".join(self.sections[section]).split())


class WebsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.page = Page(cls.source)

    def test_sections_and_anchors(self):
        self.assertIsNone(self.page.active_section)
        self.assertTrue(self.page.sections)
        self.assertEqual([key for key, count in Counter(self.page.ids).items() if count > 1], [])
        for href in self.page.links:
            if href.startswith("#"):
                self.assertIn(unquote(href[1:]), self.page.ids)

    def test_linked_repo_documents_exist(self):
        prefix = "/nconsigny/leansphincs/blob/main/"
        checked = 0
        for href in self.page.links:
            url = urlsplit(href)
            if url.netloc == "github.com" and url.path.startswith(prefix):
                path = ROOT / unquote(url.path[len(prefix):])
                self.assertTrue(path.is_file(), href)
                checked += 1
        self.assertGreater(checked, 0)

    def test_version_and_shared_objective(self):
        self.assertIn("DRAFT v0.16", self.source)
        self.assertIn("draft rules v0.16", self.source)
        self.assertIn('<span class="formula-big">minimize&nbsp;&nbsp;|σ| × V</span>', self.source)
        self.assertIn("Stage 1 is academic research; Stage 2 is the Ethereum selection.", self.source)
        objective = self.page.section_text("objective")
        self.assertIn("both stages", objective)
        self.assertIn("|σ| * V", objective)
        self.assertIn("fixes signing work and keygen work as hard budgets", objective)
        self.assertIn("1.5 s signing, 1 minute keygen", objective)
        self.assertIn("worst-case cap", objective)
        self.assertIn("not directly comparable", objective)
        self.assertIn("Fixed-budget search is now the objective itself", objective)
        self.assertIn("Hash chains are not assumed optimal", objective)

    def test_publication_mechanics_stay_out_of_the_rules(self):
        self.assertIn('<link rel="canonical" href="https://nconsigny.github.io/leansphincs/">', self.source)
        self.assertNotIn("GitHub is canonical", self.source)
        self.assertNotIn("Claude artifact", self.source)
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("GitHub is canonical", agents)
        self.assertIn("frozen legacy copy", agents)
        self.assertIn("Never republish it", agents)

    def test_current_oracle_meter(self):
        cost = self.page.section_text("costmodels")
        self.assertIn("32-byte output", cost)
        self.assertIn("ceil(inputBytes / 64)", cost)
        self.assertIn("including domain separation", cost)
        self.assertIn("rom256-input64-ceil-v1", cost)
        self.assertIn("v0.16 changes the ranking only and leaves this meter unchanged", cost)
        self.assertIn("Sum the per-call ceilings", cost)
        self.assertIn("empty-input case follows the literal ceiling", cost)
        self.assertNotIn("ceil(inputBytes / 32)", self.source)

    def test_no_false_launch_or_budget_certificate_claim(self):
        self.assertIn("submissions not open", self.source)
        mvp = self.page.section_text("mvp")
        self.assertIn("explicitly unranked", mvp)
        self.assertIn("does not yet bind the signing and keygen budget certificates", mvp)
        self.assertIn("Spacetime", mvp)
        self.assertIn("Pareto", mvp)
        self.assertIn("Stage 1 is the academic research track", mvp)
        self.assertIn("Stage 2 is the Ethereum selection track", mvp)
        self.assertIn("sigma.txt", mvp)
        self.assertIn("hverify.txt", mvp)
        self.assertIn("bound.txt", mvp)
        self.assertIn("No cryptographic baseline yet", mvp)

    def test_coding_cost_and_availability_boundaries(self):
        rules = self.page.section_text("rules")
        self.assertIn("Reed–Solomon coding are permitted", rules)
        self.assertIn("key generation ≤ 1 minute and signing ≤ 1.5 s", rules)
        self.assertIn("key generation moves from 45 s to 1 minute", rules)
        self.assertIn("Worst-case failure analysis is separate", rules)
        self.assertIn("not an adaptive lifetime-availability guarantee", rules)
        self.assertIn("not enforced by the current legacy MVP harness", rules)
        cost = self.page.section_text("costmodels")
        self.assertIn("not a concrete compression block or an instruction", cost)
        self.assertIn("would not alone prove a worst-case bound", cost)


if __name__ == "__main__":
    unittest.main()
