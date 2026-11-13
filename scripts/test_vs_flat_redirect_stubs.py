#!/usr/bin/env python3
"""Offline flat comparison redirect gate. All builds stay in scratch copies."""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET

from test_rename_brand import Page, build

ROOT = Path(__file__).resolve().parent.parent


def check_site(site, base):
    targets = set(site.glob("vs/*/index.html"))
    assert targets, "no comparison pages built"
    stubs = set(site.glob("vs-*/index.html"))
    expected = {site / f"vs-{page.parent.name}" / "index.html" for page in targets}
    assert stubs == expected, (stubs - expected, expected - stubs)
    assert len(stubs) == len(targets)
    assert (site / "vs/index.html").is_file()
    assert not (site / "vs-").exists(), "the comparison index has a flat stub"
    sitemap = ET.parse(site / "sitemap.xml")
    urls = {element.text for element in sitemap.findall(".//{*}loc")}
    for target_page in sorted(targets):
        slug = target_page.parent.name
        target = f"/vs/{slug}/"
        stub = site / f"vs-{slug}" / "index.html"
        raw = stub.read_text(encoding="utf-8")
        tags = Page(raw).tags
        assert target_page.is_file(), target
        assert [attrs.get("href") for tag, attrs in tags
                if tag == "link" and attrs.get("rel") == "canonical"] == [base + target], stub
        assert [attrs.get("content") for tag, attrs in tags
                if tag == "meta" and attrs.get("name") == "robots"] == ["noindex,follow"], stub
        assert [attrs.get("content") for tag, attrs in tags
                if tag == "meta" and attrs.get("http-equiv") == "refresh"] == [f"0; url={target}"], stub
        assert ("a", {"href": target}) in tags, stub
        verification = [attrs for tag, attrs in tags
                        if tag == "meta" and attrs.get("name") == "msvalidate.01"]
        target_verification = [attrs for tag, attrs in Page(target_page.read_text()).tags
                               if tag == "meta" and attrs.get("name") == "msvalidate.01"]
        assert len(verification) == 1 and verification == target_verification, stub
        assert f"<title>Moved: {slug.replace('-', ' ')}</title>" in raw, stub
        assert "<footer>" in raw and "Kerr &amp; Company" in raw, stub
        assert base + f"/vs-{slug}/" not in urls, stub
        assert base + target in urls, target
    return len(stubs)


def main():
    anchor = (ROOT / "data/build-id.txt").read_bytes()
    with tempfile.TemporaryDirectory(prefix="test-vs-flat-redirects-") as temporary:
        destination = Path(temporary)
        for directory in ("scripts", "data", "site", "workers"):
            shutil.copytree(ROOT / directory, destination / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.env"))
        for mode, host in (("docket", "docketseo.app"), ("checkengine", "checkengineseo.com")):
            # Each brand must generate its stubs without help from a previous build.
            for stub in (destination / "site").glob("vs-*/index.html"):
                shutil.rmtree(stub.parent)
            build(destination, mode)
            count = check_site(destination / "site", "https://" + host)
            print(f"PASS {mode}: {count} flat comparison stubs and sitemap exclusions")
    assert (ROOT / "data/build-id.txt").read_bytes() == anchor
    print("SKIP brand image rendering in scratch builds: DOCKET_SKIP_BRAND_ASSETS=1")
    print("OK")


if __name__ == "__main__":
    main()
