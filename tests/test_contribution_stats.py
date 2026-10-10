"""Exercise the updater's JSON-input and SVG-output contract through its CLI."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class ContributionStatsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for folder in ("scripts", "assets"):
            (self.root / folder).mkdir()
        for file in ("scripts/update_contribution_stats.py", "assets/contribution-stats.svg"):
            shutil.copyfile(ROOT / file, self.root / file)
        self.card = self.root / "assets/contribution-stats.svg"

    def run_update(self, response):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/update_contribution_stats.py")],
            input=json.dumps(response), text=True, capture_output=True, check=False,
        )

    def response(self, commits, prs):
        return {"data": {"user": {
            "contributionsCollection": {"totalCommitContributions": commits},
            "pullRequests": {"totalCount": prs},
        }}}

    def test_updates_counts_and_description_without_changing_artwork(self):
        before = ET.fromstring(self.card.read_text())
        for commits, prs in ((398, 74), (0, 0), (12345, 12345)):
            result = self.run_update(self.response(commits, prs))
            self.assertEqual(result.returncode, 0, result.stderr)
            after = ET.fromstring(self.card.read_text())
            self.assertEqual(after.find('.//*[@id="commit-count"]').text, str(commits))
            self.assertEqual(after.find('.//*[@id="pr-count"]').text, str(prs))
            description = after.find('.//*[@id="stats-description"]').text
            self.assertEqual(description, f"Total commits in the last year: {commits}. Total pull requests: {prs}.")
            for old, new in zip(before.iter(), after.iter()):
                self.assertEqual(old.attrib, new.attrib)
                if old.attrib.get("id") not in ("stats-description", "commit-count", "pr-count"):
                    self.assertEqual(old.text, new.text)
            previous_mtime = self.card.stat().st_mtime_ns
            self.assertEqual(self.run_update(self.response(commits, prs)).returncode, 0)
            self.assertEqual(self.card.stat().st_mtime_ns, previous_mtime)

    def test_invalid_api_data_does_not_replace_the_card(self):
        original = self.card.read_bytes()
        for response in (
            {"errors": [{"message": "API unavailable"}], **self.response(0, 0)},
            {"data": {"user": None}},
            self.response(-1, 74), self.response(True, 74), self.response("398", 74),
        ):
            self.assertNotEqual(self.run_update(response).returncode, 0)
            self.assertEqual(self.card.read_bytes(), original)

    def test_missing_svg_marker_does_not_partially_update_the_card(self):
        self.card.write_text(self.card.read_text().replace('id="pr-count"', 'id="other"'))
        original = self.card.read_bytes()
        self.assertNotEqual(self.run_update(self.response(999, 99)).returncode, 0)
        self.assertEqual(self.card.read_bytes(), original)
