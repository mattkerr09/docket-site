#!/usr/bin/env python3
"""Offline rename checks. All files, commands and fake releases live in temp dirs."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest

sys.dont_write_bytecode = True
import release_names as names
import stage_updates_mirror as mirror

SCRIPTS = Path(__file__).resolve().parent
BASE = "5038048e93f7e7ee313bb861bd8c4268be8ac796"
PLATFORMS = ("darwin-aarch64", "darwin-x86_64", "windows-x86_64")
FILES = ("collect_updater", "stage_updates_mirror", "verify_updater", "verify_release_assets",
         "verify_action", "collect_ci_timing", "visual_check", "verify_live", "verify_vendor_match")

# Stub only unrelated dependencies and I/O. Execute the real name-handling code.
DRIVER = '''import datetime, json, os, pathlib, runpy, shutil, sys, types
root = pathlib.Path.cwd()
sys.path.insert(0, str(root / "scripts"))
for name, attrs in (("brand", {"BASE": "https://example.invalid"}),
                    ("render", {"PRICE_STR": "fixture price"}), ("own_hosts", {})):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module
class Frozen(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 21, tzinfo=tz)
datetime.datetime = Frozen
# No crypto subprocess, network, licence probe or real application is run.
shutil.which = lambda name: None
script = sys.argv.pop(1)
ns = runpy.run_path(str(root / "scripts" / (script + ".py")))
g = ns["main"].__globals__
'''


class ReleaseNameTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="check-engine-release-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "checkout"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "site").mkdir()
        (self.root / "data").mkdir()
        (self.root / "data/checks.csv").write_text("id\nfixture\n")
        for filename in (*[name + ".py" for name in FILES], "release_names.py", "app_path.py"):
            shutil.copyfile(SCRIPTS / filename, self.root / "scripts" / filename)
        shutil.copyfile(SCRIPTS.parent / "action.yml", self.root / "action.yml")
        self.app = self.base / "app"
        self.dist = self.app / "dist"
        self.dist.mkdir(parents=True)
        marker = self.app / "backend/seo_engine/registry.py"
        marker.parent.mkdir(parents=True)
        marker.touch()
        self.env = {**os.environ, "DOCKET_APP": str(self.app), "HOME": str(self.base / "home"),
                    "PYTHONDONTWRITEBYTECODE": "1"}
        Path(self.env["HOME"]).mkdir()

    def run_script(self, name, extra="raise SystemExit(g['main']())", args=(), ok=True):
        result = subprocess.run([sys.executable, "-c", DRIVER + textwrap.dedent(extra), name, *args],
                                cwd=self.root, env=self.env, capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def archive(self, path, version, bundle, duplicate=False):
        data = plistlib.dumps({"CFBundleShortVersionString": version, "LSMinimumSystemVersion": "12.0"})
        with tarfile.open(path, "w:gz") as archive:
            for app in (bundle, "Extra.app") if duplicate else (bundle,):
                member = tarfile.TarInfo(f"{app}/Contents/Info.plist")
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    def fixture(self, mode):
        version = "1.3.166" if mode == "old" else "1.3.167"
        prefixes = {"old": ("Docket",), "new": ("Check-Engine-SEO",),
                    "both": names.PREFIXES, "neither": ()}[mode]
        for prefix in prefixes:
            bundle = "Docket.app" if prefix == "Docket" else "Check Engine SEO.app"
            for archive in (f"{prefix}.app.tar.gz", f"{prefix}-x86_64.app.tar.gz"):
                self.archive(self.dist / archive, version, bundle)
                (self.dist / (archive + ".sig")).write_text("sig-" + archive)
            for filename in (f"{prefix}-{version}-arm64.dmg", f"{prefix}-{version}-x86_64.dmg",
                             f"{prefix}-{version}-x64-setup.exe"):
                (self.dist / filename).write_bytes(b"fixture release bytes")
            (self.dist / f"{prefix}-{version}-x64-setup.exe.sig").write_text("sig-win")
        return version

    def collect(self, version, **kwargs):
        return self.run_script("collect_updater", args=("--version", version, "--notes", "Release notes"), **kwargs)

    def manifest(self):
        return json.loads((self.root / "site/updater.json").read_text())

    def candidates_in(self, result, candidates):
        output = result.stdout + result.stderr
        for name in candidates:
            self.assertIn(name, output)

    def test_each_candidate_and_classifier(self):
        for version in ("1.3.166", "1.3.167"):
            for candidates, arch in ((names.arm64_dmg(version), "arm64"),
                                     (names.intel_dmg(version), "x86_64"),
                                     (names.windows_setup(version), "x64"),
                                     (names.apple_updater(), "arm64"),
                                     (names.apple_updater(True), "arm64"),
                                     (names.intel_updater(), "x86_64"),
                                     (names.intel_updater(True), "x86_64")):
                for mode in ("old", "new", "both", "neither"):
                    with self.subTest(version=version, candidates=candidates, mode=mode):
                        folder = self.base / "lookup"
                        folder.mkdir(exist_ok=True)
                        for path in folder.iterdir():
                            path.unlink()
                        chosen = {"old": candidates[1:], "new": candidates[:1],
                                  "both": candidates, "neither": ()}[mode]
                        for filename in chosen:
                            (folder / filename).touch()
                        if chosen:
                            self.assertEqual(names.resolve(folder, candidates).name, chosen[0])
                        else:
                            with self.assertRaises(FileNotFoundError) as caught:
                                names.resolve(folder, candidates)
                            for filename in candidates:
                                self.assertIn(filename, str(caught.exception))
                        for prefix, filename in zip(names.PREFIXES, candidates):
                            self.assertEqual(names.classify(filename), (prefix, arch))
                            self.assertEqual(names.classify("https://example.invalid/v1/" + filename), (prefix, arch))
        for bad in ("Docket-1.3.167-aarch64.dmg", "Check-Engine-SEO-amd64.app.tar.gz",
                    "Check-Engine-SEO-x64.app.tar.gz", "Docket-1.3-arm64.dmg"):
            self.assertIsNone(names.classify(bad))

    def test_collector_all_schemes_and_missing_candidates(self):
        for mode in ("old", "new", "both", "neither"):
            with self.subTest(mode=mode):
                for path in self.dist.iterdir():
                    path.unlink()
                version = self.fixture(mode)
                if mode == "neither":
                    self.candidates_in(self.collect(version, ok=False), names.apple_updater())
                    continue
                self.collect(version)
                prefix = "Docket" if mode == "old" else names.PREFIXES[0]
                data = json.loads((self.root / "data/download.json").read_text())
                for key, suffix in (("dmg_name", "arm64.dmg"), ("intel_dmg_name", "x86_64.dmg"),
                                    ("win_setup_name", "x64-setup.exe")):
                    self.assertEqual(data[key], f"{prefix}-{version}-{suffix}")
                for platform, filename in zip(PLATFORMS, mirror.artifact_names(version, prefix)):
                    self.assertEqual(self.manifest()["platforms"][platform]["url"],
                                     f"{mirror.RELEASE}/v{version}/{filename}")
                self.assertEqual(set(self.manifest()), {"version", "notes", "pub_date", "platforms"})

    def test_collector_required_assets_optional_intel_and_missing_signatures(self):
        version = self.fixture("both")
        for candidates in (names.apple_updater(), names.intel_updater(), names.windows_setup(version)):
            selected_sig = self.dist / (candidates[0] + ".sig")
            saved = selected_sig.read_bytes()
            selected_sig.unlink()
            self.candidates_in(self.collect(version, ok=False), tuple(n + ".sig" for n in candidates))
            selected_sig.write_bytes(saved)
        for candidate_group in (names.arm64_dmg(version), names.windows_setup(version)):
            for filename in candidate_group:
                (self.dist / filename).rename(self.dist / (filename + ".saved"))
            self.candidates_in(self.collect(version, ok=False), candidate_group)
            for filename in candidate_group:
                (self.dist / (filename + ".saved")).rename(self.dist / filename)
        for filename in names.intel_updater() + names.intel_updater(True):
            (self.dist / filename).unlink()
        self.collect(version)
        self.assertNotIn("darwin-x86_64", self.manifest()["platforms"])
        # A partial optional build must fail, rather than vanish from the manifest.
        (self.dist / names.intel_updater(True)[0]).write_text("orphan")
        self.candidates_in(self.collect(version, ok=False), names.intel_updater())

    def test_wrong_architecture_and_version_are_not_release_assets(self):
        version = self.fixture("new")
        for bad in ("Check-Engine-SEO-1.3.167-aarch64.dmg", "Check-Engine-SEO-1.3.166-arm64.dmg"):
            dmg = self.dist / names.arm64_dmg(version)[0]
            dmg.rename(self.dist / bad)
            self.candidates_in(self.collect(version, ok=False), names.arm64_dmg(version))
            (self.dist / bad).rename(dmg)
        self.collect(version)
        download = self.root / "data/download.json"
        original = json.loads(download.read_text())
        for key, bad in (("dmg_name", "Check-Engine-SEO-1.3.166-arm64.dmg"),
                         ("intel_dmg_name", "Docket-1.3.167-arm64.dmg"),
                         ("win_setup_name", "Check-Engine-SEO-1.3.166-x64-setup.exe")):
            data = dict(original)
            data[key] = bad
            download.write_text(json.dumps(data))
            self.assertIn('Expected one of:', self.run_script('verify_updater', ok=False).stdout)
        for prefix in names.PREFIXES:
            for url in (f"{mirror.RELEASE}/v{version}/{prefix}-x64.app.tar.gz",
                        f"{mirror.RELEASE}/v{version}/{prefix}-1.3.166-x64-setup.exe"):
                manifest = {"version": version, "platforms": {"windows-x86_64": {"url": url}}}
                with self.assertRaisesRegex(ValueError, 'Unexpected updater URL'):
                    mirror.mirror_entries(manifest)

    def test_mirror_all_schemes_and_controls(self):
        for mode in ("old", "new", "both", "neither"):
            with self.subTest(mode=mode):
                for path in self.dist.iterdir():
                    path.unlink()
                version = self.fixture(mode)
                args = ("--add", version, "--from-dir", str(self.dist))
                cache = self.root / ".updates-cache"
                shutil.rmtree(cache, ignore_errors=True)
                result = self.run_script("stage_updates_mirror", args=args, ok=mode != "neither")
                if mode == "neither":
                    self.candidates_in(result, names.apple_updater())
                else:
                    prefix = "Docket" if mode == "old" else names.PREFIXES[0]
                    self.assertEqual(sorted(p.name for p in (cache / version).iterdir()
                                            if not p.name.endswith(".sha256")),
                                     sorted(mirror.artifact_names(version, prefix)))
        for filename in ("Check-Engine-SEO-1.3.166-x64-setup.exe", "Docket-x64.app.tar.gz"):
            with self.assertRaises(ValueError):
                mirror.stage("1.3.167", self.dist, self.base / "cache", names=(filename,))
        filename = names.apple_updater()[0]
        with self.assertRaises(ValueError):
            mirror.stage("1.3.167", self.dist, self.base / "cache", names=(filename, filename))

    def test_release_staging_listing_preference_missing_and_duplicate(self):
        for mode in ("old", "new", "both", "neither"):
            for path in self.dist.iterdir():
                path.unlink()
            version = self.fixture(mode)
            extra = f"""
            source = pathlib.Path(os.environ['DOCKET_APP']) / 'dist'
            assets = [{{'name': p.name}} for p in source.iterdir()]
            def local_release(command, **kwargs):
                if command[2] == 'view':
                    return types.SimpleNamespace(stdout=json.dumps({{'assets': assets}}))
                target = pathlib.Path(command[command.index('--dir') + 1])
                for i, arg in enumerate(command):
                    if arg == '--pattern':
                        filename = command[i + 1]
                        shutil.copyfile(source / filename, target / filename)
                return types.SimpleNamespace(returncode=0)
            g['subprocess'].run = local_release
            g['stage_release']({version!r}, 'v' + {version!r}, root / '.listing-cache')
            print(*sorted(p.name for p in (root / '.listing-cache' / {version!r}).iterdir()), sep=chr(10))
            """
            shutil.rmtree(self.root / '.listing-cache', ignore_errors=True)
            result = self.run_script('stage_updates_mirror', extra, ok=mode != 'neither')
            if mode == 'neither':
                self.candidates_in(result, names.apple_updater())
            else:
                prefix = 'Docket' if mode == 'old' else names.PREFIXES[0]
                self.assertEqual(set(result.stdout.splitlines()),
                                 {name + suffix for name in mirror.artifact_names(version, prefix)
                                   for suffix in ('', '.sha256')})
                duplicate = extra.replace(
                    "def local_release", "assets.append(assets[0])\n            def local_release")
                result = self.run_script('stage_updates_mirror', duplicate, ok=False)
                self.assertIn('duplicate asset names', result.stderr)

    def test_verifier_all_schemes_and_negative_controls(self):
        for mode in ("old", "new", "both", "neither"):
            with self.subTest(mode=mode):
                for path in self.dist.iterdir():
                    path.unlink()
                version = self.fixture(mode)
                if mode != "neither":
                    self.collect(version)
                    self.run_script("verify_updater")
                else:
                    self.candidates_in(self.run_script("verify_updater", ok=False), names.apple_updater())
        version = self.fixture("new")
        self.collect(version)
        original = self.manifest()
        for filename in names.apple_updater():
            data = json.loads(json.dumps(original))
            data["platforms"]["darwin-x86_64"]["url"] = f"{mirror.RELEASE}/v{version}/{filename}"
            (self.root / "site/updater.json").write_text(json.dumps(data))
            result = self.run_script("verify_updater", ok=False)
            self.assertIn("points at the Apple silicon tarball", result.stdout)
        (self.root / "site/updater.json").write_text(json.dumps(original))
        selected = self.dist / names.apple_updater()[0]
        self.archive(selected, "1.3.166", "Check Engine SEO.app")
        self.assertIn("tarball contains 1.3.166", self.run_script("verify_updater", ok=False).stdout)
        self.archive(selected, version, "Check Engine SEO.app", duplicate=True)
        self.assertIn("expected one top-level", self.run_script("verify_updater", ok=False).stdout)
        self.archive(selected, version, "Check Engine SEO.app")
        (self.dist / (selected.name + ".sig")).unlink()
        self.candidates_in(self.run_script("verify_updater", ok=False), names.apple_updater(True))

    def test_release_asset_listing_all_schemes_and_controls(self):
        version = "1.3.167"
        download = {"version": version, "tag": "v" + version,
                    "dmg_name": names.arm64_dmg(version)[0], "dmg_bytes": 21}
        (self.root / "data/download.json").write_text(json.dumps(download))
        for mode in ("old", "new", "both", "neither"):
            candidates = {"old": names.apple_updater()[1:], "new": names.apple_updater()[:1],
                          "both": names.apple_updater(), "neither": ()}[mode]
            assets = [{"name": download["dmg_name"], "size": 21}, {"name": "SHA256SUMS"}]
            for filename in candidates:
                assets.extend([{"name": filename}, {"name": filename + ".sig"}])
            self.run_listing(assets, ok=mode != "neither", candidates=names.apple_updater() if not candidates else ())
            if candidates:
                broken = [a for a in assets if a["name"] != candidates[0] + ".sig"]
                self.run_listing(broken, ok=False, candidates=names.apple_updater(True))
                self.run_listing(assets + [assets[-1]], ok=False)
                bad_size = json.loads(json.dumps(assets))
                bad_size[0]["size"] = 20
                self.run_listing(bad_size, ok=False)

    def run_listing(self, assets, ok, candidates=()):
        extra = f"g['_release'] = lambda *a: {{'assets': {assets!r}}}\ng['main']()"
        result = self.run_script("verify_release_assets", extra, ok=ok)
        self.candidates_in(result, candidates)
        return result

    def test_installed_bundle_lookups_all_schemes(self):
        for mode in ("old", "new", "both", "neither"):
            folder = self.base / "installed"
            shutil.rmtree(folder, ignore_errors=True)
            folder.mkdir()
            apps = {"old": names.APP_NAMES[1:], "new": names.APP_NAMES[:1],
                    "both": names.APP_NAMES, "neither": ()}[mode]
            for app in apps:
                for relative in ("Contents/Resources/docket/docket", "Contents/Resources/docket-render",
                                 "Contents/Resources/docket/docket-render"):
                    path = folder / app / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("fixture")
            for script in ("collect_ci_timing", "visual_check", "verify_live"):
                with self.subTest(mode=mode, script=script):
                    if script == "collect_ci_timing":
                        extra = f"print(g['find_binary'](pathlib.Path({str(folder)!r})))"
                    else:
                        extra = self.bundle_lookup_code(script, folder)
                    result = self.run_script(script, extra, ok=bool(apps))
                    if apps:
                        self.assertIn(apps[0], result.stdout)
                    else:
                        self.candidates_in(result, names.APP_NAMES)

    def bundle_lookup_code(self, script, folder):
        return textwrap.dedent(f"""
            original_is_file = pathlib.Path.is_file
            original_exists = pathlib.Path.exists
            def fixture_is_file(path):
                if str(path).startswith('/Applications/'):
                    path = pathlib.Path({str(folder)!r}) / str(path).removeprefix('/Applications/')
                return original_is_file(path)
            def fixture_exists(path):
                if str(path).startswith('/Applications/'):
                    path = pathlib.Path({str(folder)!r}) / str(path).removeprefix('/Applications/')
                return original_exists(path)
            pathlib.Path.is_file = fixture_is_file
            pathlib.Path.exists = fixture_exists
            if 'os' in g:
                g['os'].environ.pop('DOCKET_RENDER', None)
            print(g[{('find_helper' if script == 'visual_check' else '_renderer')!r}]())
        """)

    def test_vendor_dmg_glob_regex_preference_and_controls(self):
        for mode in ("old", "new", "both", "neither"):
            for path in self.dist.iterdir():
                path.unlink()
            version = self.fixture(mode)
            result = self.run_script("verify_vendor_match",
                                     "g['DIST'] = pathlib.Path(os.environ['DOCKET_APP']) / 'dist'\nprint(g['dist_version']())",
                                     ok=mode != "neither")
            if mode != "neither":
                self.assertEqual(result.stdout.strip(), version)
            else:
                self.candidates_in(result, ("Check-Engine-SEO-<ver>", "Docket-<ver>"))
        (self.dist / "Docket-1.3.166-aarch64.dmg").touch()
        self.run_script("verify_vendor_match",
                        "g['DIST'] = pathlib.Path(os.environ['DOCKET_APP']) / 'dist'\nprint(g['dist_version']())", ok=False)
        (self.dist / "Docket-1.3.166-arm64.dmg").touch()
        (self.dist / "Check-Engine-SEO-1.3.167-arm64.dmg").touch()
        self.assertEqual(self.run_script("verify_vendor_match",
                         "g['DIST'] = pathlib.Path(os.environ['DOCKET_APP']) / 'dist'\nprint(g['dist_version']())").stdout.strip(), "1.3.167")

    def action_block(self, text):
        start = text.index('        set -euo pipefail', text.index('- name: Install Docket'))
        end = text.index('\n    - name: Audit', start)
        return textwrap.dedent(text[start:end])

    def run_action(self, mode, text=None, bundle_mode=None, version=None, should_fail=False):
        text = text or (self.root / "action.yml").read_text()
        version = version or ("1.3.166" if mode == "old" else "1.3.167")
        block = self.action_block(text).replace('${{ inputs.version }}', 'v' + version)
        run = self.base / "action-run"
        shutil.rmtree(run, ignore_errors=True)
        run.mkdir()
        payloads = self.base / "action-assets"
        shutil.rmtree(payloads, ignore_errors=True)
        payloads.mkdir()
        available = {"old": names.arm64_dmg(version)[1:], "new": names.arm64_dmg(version)[:1],
                     "both": names.arm64_dmg(version), "neither": ()}[mode]
        for name in available:
            (payloads / name).write_text(name)
        apps = {"old": names.APP_NAMES[1:], "new": names.APP_NAMES[:1],
                "both": names.APP_NAMES, "neither": ()}[bundle_mode or mode]
        # Shell functions replace all download and mount commands with local file operations.
        prelude = '''
        curl() {
          name="${4##*/}"
          [ -f "$ASSETS/$name" ] || return 22
          cp "$ASSETS/$name" "$3"
        }
        hdiutil() {
          if [ "$1" = attach ]; then
            mkdir -p "$RUNNER_TEMP/docket-vol"
            for app in "Check Engine SEO.app" "Docket.app"; do
              if [ -d "$BUNDLES/$app" ]; then cp -R "$BUNDLES/$app" "$RUNNER_TEMP/docket-vol/$app"; fi
            done
          fi
        }
        '''
        bundles = self.base / "action-bundles"
        shutil.rmtree(bundles, ignore_errors=True)
        bundles.mkdir()
        for app in apps:
            (bundles / app).mkdir()
            (bundles / app / "selected").write_text(app)
        env = {**self.env, "RUNNER_TEMP": str(run), "GITHUB_PATH": str(run / "path"),
               "ASSETS": str(payloads), "BUNDLES": str(bundles)}
        result = subprocess.run(["bash", "-c", textwrap.dedent(prelude) + block], cwd=self.root,
                                env=env, capture_output=True, text=True)
        if available and apps and not should_fail:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((run / "docket.dmg").read_text(), available[0])
            self.assertEqual((run / "Docket.app/selected").read_text(), apps[0])
            self.assertEqual((run / "path").read_text(), str(run / "Docket.app/Contents/Resources/docket") + "\n")
        else:
            self.assertNotEqual(result.returncode, 0)
            if not should_fail:
                self.candidates_in(result, names.arm64_dmg(version) if not available else names.APP_NAMES)
        return result

    def test_action_old_new_both_neither_and_missing_bundle(self):
        for mode in ("old", "new", "both", "neither"):
            self.run_action(mode)
        self.run_action("new", bundle_mode="neither")
        # A tag for another version must not find the available asset.
        text = (self.root / "action.yml").read_text().replace('${TAG#v}', '9.9.9')
        self.run_action("new", text=text, should_fail=True)

    def test_action_verifier_can_fail_on_both_hardcoded_prefixes(self):
        extra = "g['_committed'] = lambda: g['ACTION'].read_text()\ng['subprocess'].run = lambda *a, **k: types.SimpleNamespace(returncode=1)\nraise SystemExit(g['main']())"
        original = (self.root / "action.yml").read_text()
        self.run_script("verify_action", extra)
        for before, after in (('Check-Engine-SEO-${TAG#v}', 'Check-Engine-SEO-1.3.167'),
                              ('Docket-${TAG#v}', 'Docket-1.3.166'),
                              ('"Check Engine SEO.app" "Docket.app"', '"Docket.app"')):
            (self.root / "action.yml").write_text(original.replace(before, after))
            self.run_script("verify_action", extra, ok=False)

    def original(self, filename):
        result = subprocess.run(["git", "show", f"{BASE}:{filename}"], cwd=SCRIPTS.parent,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_old_verifiers_and_bundle_choices_match_base(self):
        version = self.fixture("old")
        self.collect(version)
        for script in ("verify_updater", "verify_vendor_match", "visual_check", "verify_live"):
            if script == "verify_updater":
                extra = "g['main']()"
            elif script == "verify_vendor_match":
                extra = "g['DIST'] = pathlib.Path(os.environ['DOCKET_APP']) / 'dist'\nprint(g['dist_version']())"
            else:
                folder = self.base / "installed"
                for relative in ("Contents/Resources/docket-render", "Contents/Resources/docket/docket-render"):
                    path = folder / "Docket.app" / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("fixture")
                extra = self.bundle_lookup_code(script, folder)
            current = self.run_script(script, extra)
            path = self.root / "scripts" / (script + ".py")
            changed = path.read_text()
            path.write_text(self.original("scripts/" + script + ".py"))
            previous = self.run_script(script, extra)
            self.assertEqual((current.stdout, current.stderr), (previous.stdout, previous.stderr), script)
            path.write_text(changed)
        # Compare the timing JSON with fixed measurements and a legacy bundle.
        folder = self.base / "timing"
        binary = folder / "Docket.app/Contents/Resources/docket/docket"
        binary.parent.mkdir(parents=True)
        binary.touch()
        current = self.run_script("collect_ci_timing", f"print(g['find_binary'](pathlib.Path({str(folder)!r})))")
        self.assertEqual(current.stdout, str(binary) + "\n")
        timing = f"""
        g['BIN'] = pathlib.Path({str(binary)!r})
        g['find_binary'] = lambda: g['BIN']
        g['_run'] = lambda args, timeout: (0, json.dumps({{'stats': {{'pages_crawled': 25}}, 'duration': 2}}), 3)
        g['time'].strftime = lambda *args: '2026-11-21'
        g['main']()
        """
        current = self.run_script("collect_ci_timing", timing)
        payload = (self.root / "data/ci-timing.json").read_bytes()
        (self.root / "scripts/collect_ci_timing.py").write_text(self.original("scripts/collect_ci_timing.py"))
        previous = self.run_script("collect_ci_timing", timing)
        self.assertEqual(current.stdout, previous.stdout)
        self.assertEqual(payload, (self.root / "data/ci-timing.json").read_bytes())
        # Release verifier success text and advertised asset count are unchanged.
        data = json.loads((self.root / "data/download.json").read_text())
        assets = [{"name": data[key], "size": data[key.replace('_name', '_bytes')]}
                  for key in ("dmg_name", "intel_dmg_name", "win_setup_name")]
        assets += [{"name": name} for name in ("Docket.app.tar.gz", "Docket.app.tar.gz.sig", "SHA256SUMS")]
        current = self.run_listing(assets, ok=True)
        (self.root / "scripts/verify_release_assets.py").write_text(self.original("scripts/verify_release_assets.py"))
        previous = self.run_listing(assets, ok=True)
        self.assertEqual(current.stdout, previous.stdout)
        # The local Action verifier's successful output stays byte-for-byte the same.
        extra = "g['_committed'] = lambda: g['ACTION'].read_text()\ng['subprocess'].run = lambda *a, **k: types.SimpleNamespace(returncode=1)\nraise SystemExit(g['main']())"
        current = self.run_script("verify_action", extra)
        (self.root / "scripts/verify_action.py").write_text(self.original("scripts/verify_action.py"))
        (self.root / "action.yml").write_text(self.original("action.yml"))
        previous = self.run_script("verify_action", extra)
        self.assertEqual(current.stdout, previous.stdout)

    def test_old_collector_json_and_mirror_bytes_match_base(self):
        version = self.fixture("old")
        self.collect(version)
        current = [(self.root / path).read_bytes() for path in ("site/updater.json", "data/download.json")]
        original = self.original("scripts/collect_updater.py")
        (self.root / "scripts/collect_updater.py").write_text(original)
        self.collect(version)
        self.assertEqual(current, [(self.root / path).read_bytes() for path in ("site/updater.json", "data/download.json")])
        mirror.stage(version, self.dist, self.base / "current-cache")
        (self.root / "scripts/stage_updates_mirror.py").write_text(self.original("scripts/stage_updates_mirror.py"))
        self.run_script("stage_updates_mirror", args=("--add", version, "--from-dir", str(self.dist)))
        for path in (self.base / "current-cache" / version).iterdir():
            self.assertEqual(path.read_bytes(), (self.root / ".updates-cache" / version / path.name).read_bytes())
        self.run_action("old", text=self.original("action.yml"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
