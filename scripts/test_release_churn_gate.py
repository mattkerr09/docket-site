#!/usr/bin/env python3
"""Offline checks for the release churn gate, using throwaway git repos."""
from __future__ import annotations

from brand import BASE, LASTMOD_FILE, SITE_BRAND

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class ReleaseChurnGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ)
        self.env.pop("DOCKET_SITEWIDE_REASON", None)
        self.env.pop("CHURN_BASELINE", None)
        self.env["GIT_CONFIG_GLOBAL"] = os.devnull
        self.env["GIT_CONFIG_NOSYSTEM"] = "1"
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        (self.root / "scripts").mkdir()
        (self.root / "data").mkdir()
        shutil.copyfile(HERE / "release_churn_gate.py", self.root / "scripts/release_churn_gate.py")
        shutil.copyfile(HERE / "brand.py", self.root / "scripts/brand.py")
        self.git("init", "--quiet")
        self.original = {
            f"page-{i:02}/index.html": {"date": "2026-11-07", "hash": f"old-{i}"}
            for i in range(20)
        }
        self.write(self.original)
        self.git("add", f"data/{LASTMOD_FILE}")
        self.commit()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, env=self.env,
            capture_output=True, text=True, check=True,
        )

    def commit(self):
        self.git("-c", "user.name=Gate Test", "-c", "user.email=gate@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}",
                 "commit", "--quiet", "-m", "Test baseline")

    def write(self, records):
        (self.root / "data").mkdir(exist_ok=True)
        (self.root / f"data/{LASTMOD_FILE}").write_text(json.dumps(records), encoding="utf-8")

    def run_gate(self, count=0, reason=None):
        records = {page: dict(record) for page, record in self.original.items()}
        for page in list(records)[:count]:
            records[page]["hash"] = "changed"
        self.write(records)
        if reason is not None:
            self.env["DOCKET_SITEWIDE_REASON"] = reason
        return self.invoke()

    def invoke(self):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/release_churn_gate.py")],
            cwd=self.root, env=self.env, capture_output=True, text=True,
        )

    def test_compares_with_origin_main_when_head_already_holds_the_change(self):
        # The release flow commits the build before deploy.sh runs, so HEAD holds the
        # change. The baseline is the last pushed state, origin/main.
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        records = {page: dict(record) for page, record in self.original.items()}
        for page in list(records)[:13]:
            records[page]["hash"] = "changed"
        self.write(records)
        self.git("add", f"data/{LASTMOD_FILE}")
        self.commit()
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("13 changed pages", result.stdout)

    def test_baseline_override_names_another_ref(self):
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        records = {page: dict(record) for page, record in self.original.items()}
        for page in list(records)[:13]:
            records[page]["hash"] = "changed"
        self.write(records)
        self.git("add", f"data/{LASTMOD_FILE}")
        self.commit()
        self.env["CHURN_BASELINE"] = "HEAD"
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 changed pages", result.stdout)

    def test_no_change_passes(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 changed pages", result.stdout)

    def test_twelve_changed_pass(self):
        result = self.run_gate(12)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("12 changed pages", result.stdout)

    def test_thirteen_changed_fail(self):
        result = self.run_gate(13)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("13 changed pages", result.stdout)
        self.assertIn("CHURN FAIL", result.stdout)

    def test_thirteen_with_reason_pass(self):
        reason = "We corrected the price shown across the site."
        result = self.run_gate(13, reason)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(reason, result.stdout)

    def test_empty_reason_fails(self):
        for reason in ("", " \t\n "):
            with self.subTest(reason=reason):
                self.assertEqual(self.run_gate(13, reason).returncode, 1)

    def test_new_page_counts(self):
        self.original["index.html"] = {"date": "2026-11-08", "hash": "new"}
        result = self.run_gate(12)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("13 changed pages", result.stdout)
        self.assertIn(f"{BASE}/\n", result.stdout)

    def test_date_only_changes_pass(self):
        for record in self.original.values():
            record["date"] = "2026-11-08"
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 changed pages", result.stdout)

    @unittest.skipUnless(SITE_BRAND == "checkengine", "rename baseline applies in checkengine mode")
    def test_first_rename_compares_with_deployed_docket_hashes(self):
        self.git("mv", f"data/{LASTMOD_FILE}", "data/page-lastmod.json")
        self.commit()
        result = self.run_gate(13)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("13 changed pages", result.stdout)

    def test_missing_head_file_counts_all_pages(self):
        self.git("rm", f"data/{LASTMOD_FILE}")
        self.commit()
        result = self.run_gate()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("20 changed pages", result.stdout)

    def test_prints_first_fifteen_urls_in_order(self):
        result = self.run_gate(20)
        urls = [line.strip() for line in result.stdout.splitlines() if line.startswith("  https://")]
        self.assertEqual(urls, [f"{BASE}/page-{i:02}/" for i in range(15)])

    def test_git_error_fails_even_with_reason(self):
        shutil.rmtree(self.root / ".git")
        result = self.run_gate(13, "We corrected the price shown across the site.")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Could not compare page hashes", result.stderr)

    def test_missing_working_file_fails(self):
        (self.root / f"data/{LASTMOD_FILE}").unlink()
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Could not compare page hashes", result.stderr)

    def test_invalid_json_fails(self):
        (self.root / f"data/{LASTMOD_FILE}").write_text("invalid", encoding="utf-8")
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Could not compare page hashes", result.stderr)


if __name__ == "__main__":
    unittest.main()
