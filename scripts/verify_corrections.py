#!/usr/bin/env python3
"""Every entry on /learn/what-docket-got-wrong/ names a release that exists, the day it was published, and tests that exist.

    python3 scripts/verify_corrections.py [--self-test] [--offline]

WHY. The page says "fixed in 1.3.107 on 13 October" and shows the tests that hold the fix. A page like that is
only worth reading if each such line can be checked, and a hand-written record drifts: a release renumbered, a day
copied from the wrong entry, a test file renamed in the app repo. data/corrections.json is that record, so it is
checked against the three places the claim can be tested.

WHAT IT REFUSES, for each entry:
  * a release that is not a published release of this site's GitHub repo (`gh release view`), or whose published
    day (UTC) is not the entry's date;
  * a release with no commit in the app repo whose subject begins with that version, or one committed more than a
    day from the entry's date;
  * a test file that is not tracked in the app repo's tests/ folder, or that was added after the release's commit
    (a test cannot hold a fix that had not shipped);
  * an entry that is missing its title, what was wrong, how it was found, what changed or its tests; two entries
    for one release; entries not newest first;
  * a built page (site/learn/what-docket-got-wrong/index.html) that lacks any entry's anchor or its published day.

--offline skips the GitHub check and says so. Without it a GitHub failure is a failure, after one retry, so a
gate that cannot reach the thing it checks never reads as a pass.

--self-test plants a good entry and one fault at a time and requires every fault to be refused, then runs the real
data.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "corrections.json"
APP = ROOT.parent / "docket-app"
PAGE = ROOT / "site" / "learn" / "what-docket-got-wrong" / "index.html"
REPO = "mattkerr09/docket-site"
FIELDS = ("title", "wrong", "found", "fixed")


def _version(text: str):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(text))
    return tuple(int(x) for x in m.groups()) if m else None


def _run(cmd: list, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)


class Lookups:
    """The three places an entry is checked. Replaced by a fake in the self-test."""

    def published(self, release: str):
        """The UTC day GitHub says the release was published; None if there is no such release.
        Raises RuntimeError when GitHub could not be asked."""
        last = ""
        for _ in range(2):
            p = _run(["gh", "release", "view", f"v{release}", "--repo", REPO, "--json", "publishedAt",
                      "-q", ".publishedAt"])
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()[:10]
            last = (p.stderr or p.stdout).strip()
            if "not found" in last.lower():
                return None
        raise RuntimeError(f"gh release view v{release}: {last or 'no answer'}")

    def commit(self, release: str):
        """(sha, committed day) of the first commit in the app repo whose subject begins with the version."""
        p = _run(["git", "log", "--reverse", "--format=%h %cd", "--date=short", "-E",
                  f"--grep=^{re.escape(release)}([^0-9.]|$)"], cwd=APP)
        lines = p.stdout.strip().splitlines()
        return tuple(lines[0].split()) if lines else None

    def test_added(self, name: str):
        """sha of the commit that added tests/<name>; None when the file is not tracked."""
        if _run(["git", "ls-files", "--error-unmatch", f"tests/{name}"], cwd=APP).returncode != 0:
            return None
        p = _run(["git", "log", "--diff-filter=A", "--format=%h", "--", f"tests/{name}"], cwd=APP)
        shas = p.stdout.split()
        return shas[-1] if shas else None

    def is_ancestor(self, older: str, newer: str) -> bool:
        return _run(["git", "merge-base", "--is-ancestor", older, newer], cwd=APP).returncode == 0


def problems(entries: list, look, offline: bool = False) -> list:
    out = []
    seen = set()
    previous = None
    for e in entries:
        rel = str(e.get("release"))
        tag = f"{rel}"
        v = _version(rel)
        if v is None:
            out.append(f"{tag}: not a version")
            continue
        if rel in seen:
            out.append(f"{tag}: two entries for one release")
        seen.add(rel)
        if previous is not None and v >= previous:
            out.append(f"{tag}: entries must be newest first")
        previous = v
        try:
            day = dt.date.fromisoformat(str(e.get("date")))
        except ValueError:
            out.append(f"{tag}: date {e.get('date')!r} is not a day")
            continue
        for f in FIELDS:
            if not str(e.get(f, "")).strip():
                out.append(f"{tag}: no {f}")
        tests = e.get("tests") or []
        if not tests:
            out.append(f"{tag}: no tests named")
        if not offline:
            pub = look.published(rel)
            if pub is None:
                out.append(f"{tag}: no published release v{rel} in {REPO}")
            elif pub != day.isoformat():
                out.append(f"{tag}: published {pub} on GitHub, the entry says {day.isoformat()}")
        commit = look.commit(rel)
        if commit is None:
            out.append(f"{tag}: no commit in the app repo whose subject begins with {rel}")
            continue
        sha, cday = commit
        if abs((dt.date.fromisoformat(cday) - day).days) > 1:
            out.append(f"{tag}: the release commit {sha} is dated {cday}, the entry says {day.isoformat()}")
        for t in tests:
            added = look.test_added(t)
            if added is None:
                out.append(f"{tag}: tests/{t} is not tracked in the app repo")
            elif added != sha and not look.is_ancestor(added, sha):
                out.append(f"{tag}: tests/{t} was added after the release commit {sha}")
    return out


def page_problems(entries: list, page_text: str) -> list:
    out = []
    for e in entries:
        anchor = 'id="v' + e["release"].replace(".", "-") + '"'
        d = dt.date.fromisoformat(e["date"])
        human = f"{d.day} {d.strftime('%B %Y')}"
        if anchor not in page_text:
            out.append(f"{e['release']}: the built page has no {anchor}")
        if human not in page_text:
            out.append(f"{e['release']}: the built page does not say {human}")
    return out


class _Fake:
    """Releases 1.3.2 (2026-01-02) and 1.3.1 (2026-01-01) exist; one test is tracked, added with 1.3.1."""

    PUBLISHED = {"1.3.2": "2026-01-02", "1.3.1": "2026-01-01"}
    COMMITS = {"1.3.2": ("bbb", "2026-01-02"), "1.3.1": ("aaa", "2026-01-01")}
    TESTS = {"test_ok.py": "aaa", "test_later.py": "ccc"}

    def published(self, release):
        return self.PUBLISHED.get(release)

    def commit(self, release):
        return self.COMMITS.get(release)

    def test_added(self, name):
        return self.TESTS.get(name)

    def is_ancestor(self, older, newer):
        return (older, newer) in {("aaa", "bbb")}


def self_test() -> int:
    good = [
        {"release": "1.3.2", "date": "2026-01-02", "title": "t", "wrong": "w", "found": "f", "fixed": "x",
         "tests": ["test_ok.py"]},
        {"release": "1.3.1", "date": "2026-01-01", "title": "t", "wrong": "w", "found": "f", "fixed": "x",
         "tests": ["test_ok.py"]},
    ]
    if problems(good, _Fake()):
        print("FAIL  self-test: a good pair was refused:", problems(good, _Fake()))
        return 1
    faults = {
        "a release that was never published": (0, {"release": "1.3.9", "date": "2026-01-02"}),
        "a date that is not the published day": (0, {"date": "2026-01-05"}),
        "a test that is not tracked": (0, {"tests": ["test_missing.py"]}),
        "a test added after the release": (0, {"tests": ["test_later.py"]}),
        "an entry with nothing wrong in it": (0, {"wrong": " "}),
        "an entry with no tests": (0, {"tests": []}),
    }
    for name, (idx, change) in faults.items():
        planted = [dict(e) for e in good]
        planted[idx].update(change)
        if not problems(planted, _Fake()):
            print(f"FAIL  self-test: {name} was not refused")
            return 1
    flipped = [dict(good[1]), dict(good[0])]
    if not problems(flipped, _Fake()):
        print("FAIL  self-test: entries oldest first were not refused")
        return 1
    dup = [dict(good[0]), dict(good[0])]
    if not problems(dup, _Fake()):
        print("FAIL  self-test: two entries for one release were not refused")
        return 1
    if not page_problems(good, "<html>nothing</html>"):
        print("FAIL  self-test: a page without the entries passed")
        return 1
    if page_problems(good, 'id="v1-3-2" 2 January 2026 id="v1-3-1" 1 January 2026'):
        print("FAIL  self-test: a page with the entries was refused")
        return 1
    return 0


def main() -> int:
    if "--self-test" in sys.argv and self_test():
        return 1
    offline = "--offline" in sys.argv
    try:
        entries = json.loads(DATA.read_text(encoding="utf-8"))["entries"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL  data/corrections.json could not be read: {exc}")
        return 1
    if not APP.is_dir():
        print(f"FAIL  the app repo is not at {APP}, so the releases and tests cannot be checked")
        return 1
    try:
        found = problems(entries, Lookups(), offline=offline)
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL  could not check the corrections: {exc}")
        return 1
    if not PAGE.is_file():
        found.append(f"the built page {PAGE.relative_to(ROOT)} does not exist: run scripts/build.py first")
    else:
        found += page_problems(entries, PAGE.read_text(encoding="utf-8"))
    if found:
        print("FAIL  the corrections page does not match the releases it describes:")
        for line in found:
            print("   ", line)
        return 1
    note = "GitHub not asked (--offline)" if offline else "each release found on GitHub"
    print(f"  ok: {len(entries)} corrections; {note}; every release commit and test file found in the app repo"
          + (" (self-test passed)" if "--self-test" in sys.argv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
