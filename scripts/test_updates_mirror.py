#!/usr/bin/env python3
"""Offline mirror regression tests. All HTTP and git remotes are local."""
from __future__ import annotations

from contextlib import contextmanager
import functools
import hashlib
import io
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.response
from unittest import mock

sys.dont_write_bytecode = True
import stage_updates_mirror as mirror
import verify_updates_mirror as verify

SCRIPTS = Path(__file__).resolve().parent
PLATFORMS = ("darwin-aarch64", "darwin-x86_64", "windows-x86_64")


class LocalHandler(SimpleHTTPRequestHandler):
    range_mode = "unsupported"
    requests = []
    stale_reads = 0
    stale_manifest = b"{}"

    def do_GET(self):
        type(self).requests.append((self.path, self.headers.get("Range")))
        if self.path.startswith("/updater.json") and type(self).stale_reads:
            type(self).stale_reads -= 1
            self.send_response(200)
            self.end_headers()
            self.wfile.write(type(self).stale_manifest)
            return
        if self.headers.get("Range") and self.range_mode == "supported":
            path = Path(self.translate_path(self.path))
            self.send_response(206)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes 0-0/{path.stat().st_size}")
            self.send_header("Content-Length", "1")
            self.end_headers()
            self.wfile.write(path.read_bytes()[:1])
            return
        super().do_GET()

    def end_headers(self):
        if self.range_mode in ("supported", "broken"):
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def log_message(self, *args):
        pass


@contextmanager
def local_server(directory: Path, range_mode="unsupported"):
    handler = type("Handler", (LocalHandler,),
                   {"range_mode": range_mode, "requests": [], "stale_reads": 0})
    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                functools.partial(handler, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", handler
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="docket-mirror-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "checkout"
        self.root.mkdir()
        self.cache = self.root / ".updates-cache"
        self.env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_AUTHOR_NAME": "Mirror test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                    "GIT_COMMITTER_NAME": "Mirror test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}
        self.app = self.base / "app"
        marker = self.app / "backend/seo_engine/registry.py"
        marker.parent.mkdir(parents=True)
        marker.touch()
        self.env["DOCKET_APP"] = str(self.app)
        self.env["NO_PROXY"] = self.env["no_proxy"] = "127.0.0.1,localhost"
        opener = mock.patch.object(urllib.request, "_opener",
                                   urllib.request.build_opener(urllib.request.ProxyHandler({})))
        opener.start()
        self.addCleanup(opener.stop)
        (self.root / "scripts").mkdir()
        for name in ("stage_updates_mirror.py", "verify_updates_mirror.py",
                     "collect_updater.py", "app_path.py"):
            shutil.copyfile(SCRIPTS / name, self.root / "scripts" / name)
        (self.root / "site").mkdir()
        shutil.copyfile(SCRIPTS.parent / ".gitignore", self.root / ".gitignore")

    def run_command(self, *command, ok=True, cwd=None, env=None):
        result = subprocess.run(command, cwd=cwd or self.root, env=env or self.env,
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def script(self, name, *args, **kwargs):
        return self.run_command(sys.executable, f"scripts/{name}.py", *args, **kwargs)

    def release(self, version):
        directory = self.base / ("release-" + version)
        directory.mkdir(exist_ok=True)
        for name in mirror.artifact_names(version):
            (directory / name).write_bytes(f"fake updater {version} {name}\n".encode())
        return directory

    def add_release(self, version):
        source = self.release(version)
        self.script("stage_updates_mirror", "--add", version, "--from-dir", str(source))
        return source

    def manifest(self, version="1.3.100", github=False):
        base = f"{mirror.RELEASE}/v{version}" if github else f"{mirror.MIRROR}/{version}"
        manifest = {"version": version, "notes": "Test release notes", "pub_date": "2026-11-09T00:00:00Z",
                    "platforms": {platform: {"url": f"{base}/{name}", "signature": f"sig-{platform}"}
                                  for platform, name in zip(PLATFORMS, mirror.artifact_names(version))}}
        (self.root / "site/updater.json").write_text(json.dumps(manifest))
        return manifest

    def test_numeric_retention_and_plan(self):
        for version in ("1.3.100", "1.3.99", "1.3.101"):
            self.add_release(version)
        self.assertEqual(mirror.cached_versions(self.cache), ["1.3.101", "1.3.100"])
        self.assertFalse((self.cache / "1.3.99").exists())
        # Put an older release back to exercise the explicit prune command.
        restored = self.cache / "1.3.99"
        shutil.copytree(self.base / "release-1.3.99", restored)
        for path in restored.iterdir():
            path.with_name(path.name + ".sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest())
        self.script("stage_updates_mirror", "--prune")
        self.assertEqual(mirror.cached_versions(self.cache), ["1.3.101", "1.3.100"])
        manifest = self.manifest("1.3.101")
        output = self.script("stage_updates_mirror", "--plan").stdout
        self.assertEqual(len(output.splitlines()), 6)
        for version in ("1.3.100", "1.3.101"):
            for name in mirror.artifact_names(version):
                path = self.cache / version / name
                self.assertEqual(path.read_bytes(), (self.base / ("release-" + version) / name).read_bytes())
                self.assertEqual((path.with_name(name + ".sha256")).read_text().strip(),
                                 hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertIn(f"updates/{version}/{name}", output)
        self.assertEqual(len(mirror.publish_plan(manifest, self.cache)), 6)

    def test_bad_files_refused_without_partial_release(self):
        for kind in ("missing", "empty", "limit"):
            with self.subTest(kind=kind):
                source = self.release("1.3.100")
                path = source / mirror.artifact_names("1.3.100")[-1]
                if kind == "missing":
                    path.unlink()
                elif kind == "empty":
                    path.write_bytes(b"")
                else:
                    with path.open("wb") as payload:
                        payload.truncate(100_000_000)
                result = self.script("stage_updates_mirror", "--add", "1.3.100", "--from-dir", str(source), ok=False)
                self.assertIn(path.name, result.stderr)
                self.assertFalse((self.cache / "1.3.100").exists())
                self.assertEqual(list(self.cache.glob(".stage-*")), [])

    def test_stage_retry_is_immutable(self):
        source = self.add_release("1.3.100")
        before = (self.cache / "1.3.100/Docket.app.tar.gz").read_bytes()
        self.script("stage_updates_mirror", "--add", "1.3.100", "--from-dir", str(source))
        (source / "Docket.app.tar.gz").write_bytes(b"changed")
        self.script("stage_updates_mirror", "--add", "1.3.100", "--from-dir", str(source), ok=False)
        self.assertEqual((self.cache / "1.3.100/Docket.app.tar.gz").read_bytes(), before)

    def test_collect_urls_signatures_and_optional_platforms(self):
        version = "1.3.100"
        source = self.release(version)
        dist = self.app / "dist"
        shutil.copytree(source, dist)
        for platform, name in zip(PLATFORMS, mirror.artifact_names(version)):
            (dist / (name + ".sig")).write_text(f"  file-signature-{platform}\n")
        arguments = ("--version", version, "--notes", "Actual release notes")
        self.script("collect_updater", *arguments, "--source", "mirror")
        manifest = json.loads((self.root / "site/updater.json").read_text())
        self.assertEqual(set(manifest), {"version", "notes", "pub_date", "platforms"})
        self.assertEqual(set(manifest["platforms"]), set(PLATFORMS))
        self.assertEqual(manifest["version"], version)
        self.assertEqual(manifest["notes"], "Actual release notes")
        for platform, name in zip(PLATFORMS, mirror.artifact_names(version)):
            self.assertEqual(manifest["platforms"][platform],
                             {"signature": f"file-signature-{platform}", "url": f"{mirror.MIRROR}/{version}/{name}"})
            self.assertEqual((self.cache / version / name).read_bytes(), (dist / name).read_bytes())
        shutil.rmtree(self.cache)
        self.script("collect_updater", *arguments, "--source", "github", "--tag", "custom-tag")
        rollback = json.loads((self.root / "site/updater.json").read_text())
        for platform, name in zip(PLATFORMS, mirror.artifact_names(version)):
            self.assertEqual(rollback["platforms"][platform],
                             {"signature": f"file-signature-{platform}", "url": f"{mirror.RELEASE}/custom-tag/{name}"})
        self.assertFalse(self.cache.exists())
        # The default is the release assets: Pages carries no update binaries (10 Nov 2026: the mirror's 157 MB
        # artifacts timed out the Pages deploy twice), and nothing is staged.
        self.script("collect_updater", *arguments)
        default = json.loads((self.root / "site/updater.json").read_text())
        for platform, name in zip(PLATFORMS, mirror.artifact_names(version)):
            self.assertEqual(default["platforms"][platform]["url"], f"{mirror.RELEASE}/v{version}/{name}")
        self.assertFalse(self.cache.exists())
        self.script("collect_updater", *arguments, "--source", "mirror", "--no-intel")
        optional = json.loads((self.root / "site/updater.json").read_text())
        self.assertEqual(set(optional["platforms"]), {"darwin-aarch64", "windows-x86_64"})
        self.assertFalse((self.cache / version / "Docket-x86_64.app.tar.gz").exists())

    def test_collect_failure_keeps_manifest_and_reads_sig_file(self):
        dist = self.app / "dist"
        shutil.copytree(self.release("1.3.100"), dist)
        old = self.manifest(github=True)
        for name in mirror.artifact_names("1.3.100"):
            (dist / (name + ".sig")).write_text("signature-" + name)
        (dist / "Docket-x86_64.app.tar.gz.sig").write_text("")
        self.script("collect_updater", "--version", "1.3.100", "--notes", "Notes", ok=False)
        self.assertEqual(json.loads((self.root / "site/updater.json").read_text()), old)
        (dist / "Docket-x86_64.app.tar.gz.sig").write_text("intel-sig")
        (dist / "Docket-1.3.100-x64-setup.exe").write_bytes(b"")
        self.script("collect_updater", "--version", "1.3.100", "--notes", "Notes", ok=False)
        self.assertEqual(json.loads((self.root / "site/updater.json").read_text()), old)
        self.assertFalse((self.cache / "1.3.100").exists())

    def test_from_release_uses_gh_and_checks_digests(self):
        source = self.release("1.3.100")
        bindir = self.base / "bin"
        bindir.mkdir()
        gh = bindir / "gh"
        # This stub only reads the fake local release. It makes no requests.
        gh.write_text(f"#!{sys.executable}\n" + '''import hashlib, json, os, pathlib, shutil, sys
source = pathlib.Path(os.environ["FAKE_RELEASE"])
args = sys.argv[1:]
with open(os.environ["GH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
if args[:2] == ["release", "view"]:
    assets = []
    for path in source.iterdir():
        digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        if os.environ.get("BAD_DIGEST"):
            digest = "sha256:" + "0" * 64
        if os.environ.get("NO_DIGEST"):
            digest = None
        assets.append({"name": path.name, "digest": digest})
    print(json.dumps({"assets": assets}))
elif args[:2] == ["release", "download"]:
    target = pathlib.Path(args[args.index("--dir") + 1])
    for i, arg in enumerate(args):
        if arg == "--pattern":
            shutil.copyfile(source / args[i + 1], target / args[i + 1])
else:
    sys.exit(8)
''')
        gh.chmod(0o755)
        env = {**self.env, "PATH": str(bindir) + os.pathsep + self.env["PATH"],
               "FAKE_RELEASE": str(source), "GH_LOG": str(self.base / "gh.log")}
        args = ("--add", "1.3.100", "--from-release", "v1.3.100")
        result = self.script("stage_updates_mirror", *args, env={**env, "BAD_DIGEST": "1"}, ok=False)
        self.assertIn("sha256 differs", result.stderr)
        self.assertFalse((self.cache / "1.3.100").exists())
        self.script("stage_updates_mirror", *args, env=env)
        for name in mirror.artifact_names("1.3.100"):
            self.assertEqual((self.cache / "1.3.100" / name).read_bytes(), (source / name).read_bytes())
        calls = [json.loads(line) for line in (self.base / "gh.log").read_text().splitlines()]
        download = calls[-1]
        self.assertEqual(download[:3], ["release", "download", "v1.3.100"])
        self.assertEqual([download[i + 1] for i, arg in enumerate(download) if arg == "--pattern"],
                         list(mirror.artifact_names("1.3.100")))
        shutil.rmtree(self.cache)
        self.script("stage_updates_mirror", *args, env={**env, "NO_DIGEST": "1"})
        self.assertEqual(len(list((self.cache / "1.3.100").glob("*.sha256"))), 3)

    def init_repo(self):
        origin = self.base / "origin.git"
        self.run_command("git", "init", "--bare", "--initial-branch=main", str(origin))
        # Clone the local origin into a fresh path, then move the fixture into it.
        clone = self.base / "clone"
        self.run_command("git", "clone", str(origin), str(clone))
        for path in self.root.iterdir():
            shutil.move(str(path), clone / path.name)
        self.root = clone
        self.cache = clone / ".updates-cache"
        self.run_command("git", "add", "--", "scripts", "site", ".gitignore")
        self.run_command("git", "commit", "-qm", "Fixture site")
        self.run_command("git", "push", "-q", "origin", "main")
        return origin

    def publish_block(self):
        # Execute the actual publish section against a LOCAL bare origin.
        # Never run deploy.sh or any of its production gates.
        deploy = (SCRIPTS / "deploy.sh").read_text()
        start = deploy.index('echo "==> updater mirror cache gate"')
        end = deploy.index('\n\necho "==> live updater mirror gate"', start)
        return 'set -euo pipefail\nPY="' + sys.executable + '"\n' + deploy[start:end]

    def test_publish_tip_only_main_clean_and_two_versions(self):
        for version in ("1.3.99", "1.3.100", "1.3.101"):
            self.add_release(version)
        self.manifest("1.3.101")
        origin = self.init_repo()
        self.run_command("bash", "-c", self.publish_block())
        tree = self.run_command("git", "--git-dir", str(origin), "ls-tree", "-r", "--name-only", "gh-pages").stdout.splitlines()
        expected = {f"updates/{version}/{name}" for version in ("1.3.100", "1.3.101")
                    for name in mirror.artifact_names(version)}
        self.assertEqual({path for path in tree if path.startswith("updates/")}, expected)
        for relative in expected:
            served = self.run_command("git", "--git-dir", str(origin), "show", f"gh-pages:{relative}").stdout.encode()
            version, name = relative.split("/")[1:]
            self.assertEqual(served, (self.cache / version / name).read_bytes())
        main_tree = self.run_command("git", "--git-dir", str(origin), "ls-tree", "-r", "--name-only", "main").stdout
        self.assertFalse(any(path.startswith(("updates/", ".updates-cache/", "site/updates/")) for path in main_tree.splitlines()))
        parent_tree = self.run_command("git", "--git-dir", str(origin), "ls-tree", "-r", "--name-only", "gh-pages^").stdout
        self.assertNotIn("updates/", parent_tree)
        self.assertEqual(self.run_command("git", "status", "--porcelain").stdout, "")
        self.assertEqual(self.run_command("git", "worktree", "list", "--porcelain").stdout.count("worktree "), 1)
        first_tip = self.run_command("git", "--git-dir", str(origin), "rev-parse", "gh-pages").stdout.strip()
        self.run_command("bash", "-c", self.publish_block())
        ancestors = self.run_command("git", "--git-dir", str(origin), "rev-list", "gh-pages^").stdout.splitlines()
        self.assertNotIn(first_tip, ancestors)

    def test_publish_failure_removes_worktree_and_can_retry(self):
        self.add_release("1.3.100")
        self.manifest()
        origin = self.init_repo()
        self.run_command("git", "subtree", "split", "--prefix", "site", "-b", "gh-pages-tmp")
        before = self.run_command("git", "--git-dir", str(origin), "show-ref").stdout
        bindir = self.base / "fail-commit"
        bindir.mkdir()
        git = bindir / "git"
        git.write_text('#!/bin/sh\nif [ "$1" = commit ]; then exit 23; fi\nexec '
                       + shutil.which("git") + ' "$@"\n')
        git.chmod(0o755)
        env = {**self.env, "PATH": str(bindir) + os.pathsep + self.env["PATH"]}
        self.script("stage_updates_mirror", "--publish", "gh-pages-tmp", env=env, ok=False)
        self.assertEqual(self.run_command("git", "worktree", "list", "--porcelain").stdout.count("worktree "), 1)
        self.assertEqual(self.run_command("git", "status", "--porcelain").stdout, "")
        self.assertEqual(self.run_command("git", "--git-dir", str(origin), "show-ref").stdout, before)
        self.script("stage_updates_mirror", "--publish", "gh-pages-tmp")
        tree = self.run_command("git", "ls-tree", "-r", "--name-only", "gh-pages-tmp").stdout
        self.assertIn("updates/1.3.100/Docket.app.tar.gz", tree)

    def test_bad_cache_stops_before_every_push(self):
        self.add_release("1.3.100")
        self.manifest()
        origin = self.init_repo()
        for kind in ("missing", "hash", "limit", "record"):
            with self.subTest(kind=kind):
                path = self.cache / "1.3.100/Docket.app.tar.gz"
                record = path.with_name(path.name + ".sha256")
                path.write_bytes((self.base / "release-1.3.100" / path.name).read_bytes())
                record.write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "\n")
                if kind == "missing":
                    path.unlink()
                elif kind == "hash":
                    path.write_bytes(b"flipped bytes")
                elif kind == "record":
                    record.unlink()
                else:
                    with path.open("wb") as payload:
                        payload.truncate(100_000_000)
                # A distinct local main commit makes an accidental first push visible.
                marker = self.root / "site/change.txt"
                marker.write_text(kind)
                self.run_command("git", "add", "--", "site/change.txt")
                self.run_command("git", "commit", "-qm", "Local unpushed change")
                before = self.run_command("git", "--git-dir", str(origin), "show-ref").stdout
                result = self.run_command("bash", "-c", self.publish_block(), ok=False)
                self.assertIn("Docket.app.tar.gz", result.stderr)
                self.assertEqual(self.run_command("git", "--git-dir", str(origin), "show-ref").stdout, before)

    def test_github_rollback_publishes_without_cache(self):
        self.manifest(github=True)
        origin = self.init_repo()
        self.run_command("bash", "-c", self.publish_block())
        tree = self.run_command("git", "--git-dir", str(origin), "ls-tree", "-r", "--name-only", "gh-pages").stdout
        self.assertIn("updater.json", tree)
        self.assertNotIn("updates/", tree)
        self.assertFalse(self.cache.exists())
        self.script("verify_updates_mirror", "--offline")

    def test_offline_byte_flip_and_records(self):
        self.add_release("1.3.99")
        self.add_release("1.3.100")
        self.manifest()
        self.script("verify_updates_mirror", "--offline")
        previous = self.cache / "1.3.99/Docket.app.tar.gz"
        old_bytes = previous.read_bytes()
        previous.write_bytes(b"bad previous version")
        result = self.script("verify_updates_mirror", "--offline", ok=False)
        self.assertIn("1.3.99/Docket.app.tar.gz", result.stderr)
        previous.write_bytes(old_bytes)
        path = self.cache / "1.3.100/Docket.app.tar.gz"
        original = path.read_bytes()
        path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        result = self.script("verify_updates_mirror", "--offline", ok=False)
        self.assertIn("sha256 differs", result.stderr)
        path.write_bytes(original)
        record = path.with_name(path.name + ".sha256")
        record.unlink()
        self.script("verify_updates_mirror", "--offline", ok=False)

    def test_live_checks_with_fake_responses(self):
        # These checks also run in sandboxes that cannot bind loopback ports.
        # The socket-based http.server tests below remain required by the gate.
        self.add_release("1.3.100")
        manifest = self.manifest()
        replies = []
        bad_payload = False
        stale_reads = 0
        range_mode = "supported"

        def respond(request, timeout):
            nonlocal stale_reads
            self.assertGreater(timeout, 0)
            url = request.full_url
            range_header = request.get_header("Range")
            replies.append((url, range_header))
            if "/updater.json" in url:
                payload = json.dumps(manifest if not stale_reads else {}).encode()
                stale_reads = max(0, stale_reads - 1)
                return urllib.response.addinfourl(io.BytesIO(payload), {}, url, 200)
            path = self.cache / manifest["version"] / url.rsplit("/", 1)[-1]
            payload = path.read_bytes()
            if bad_payload:
                payload = bytes([payload[0] ^ 1]) + payload[1:]
            headers = {"Content-Type": "application/octet-stream"}
            status = 200
            if range_mode in ("supported", "broken"):
                headers["Accept-Ranges"] = "bytes"
            if range_header and range_mode == "supported":
                headers["Content-Range"] = f"bytes 0-0/{len(payload)}"
                payload = payload[:1]
                status = 206
            return urllib.response.addinfourl(io.BytesIO(payload), headers, url, status)

        with mock.patch.object(verify.urllib.request, "urlopen", side_effect=respond):
            verify.verify_live(manifest, self.cache, verify.MANIFEST_URL, 0)
            self.assertEqual(len([value for _, value in replies if value == "bytes=0-0"]), 3)
            bad_payload = True
            with self.assertRaisesRegex(ValueError, "Served sha256 or size differs"):
                verify.verify_live(manifest, self.cache, verify.MANIFEST_URL, 0)
            bad_payload = False
            range_mode = "broken"
            with self.assertRaisesRegex(ValueError, "Range request returned 200"):
                verify.verify_live(manifest, self.cache, verify.MANIFEST_URL, 0)
            range_mode = "unsupported"
            verify.verify_live(manifest, self.cache, verify.MANIFEST_URL, 0)
            stale_reads = 1
            with self.assertRaisesRegex(ValueError, "Live updater manifest differs"):
                verify.verify_live(manifest, self.cache, verify.MANIFEST_URL, 0)
            stale_reads = 1
            with mock.patch.object(verify.time, "sleep") as sleep:
                verify.verify_live(manifest, self.cache, verify.MANIFEST_URL, 1)
            sleep.assert_called_once()
            self.assertEqual(stale_reads, 0)

    def test_live_bytes_range_and_stale_manifest(self):
        self.add_release("1.3.100")
        manifest = self.manifest()
        published = self.root / "site"
        shutil.copytree(self.cache / "1.3.100", published / "updates/1.3.100")
        for mode in ("unsupported", "supported", "broken"):
            with self.subTest(range_mode=mode), local_server(published, mode) as (base, handler):
                live = json.loads(json.dumps(manifest))
                for entry in live["platforms"].values():
                    entry["url"] = entry["url"].replace("https://docketseo.app", base)
                (published / "updater.json").write_text(json.dumps(live))
                # Only replace the host in the parser for this loopback test.
                with mock.patch.object(mirror, "MIRROR", base + "/updates"):
                    if mode == "broken":
                        with self.assertRaisesRegex(ValueError, "Range request returned 200"):
                            verify.verify_live(live, self.cache, base + "/updater.json", 0)
                        continue
                    verify.verify_live(live, self.cache, base + "/updater.json", 0)
                    ranges = [path for path, value in handler.requests if value == "bytes=0-0"]
                    self.assertEqual(len(ranges), 3)
                    path = published / "updates/1.3.100/Docket.app.tar.gz"
                    original = path.read_bytes()
                    path.write_bytes(b"x" + original[1:])
                    with self.assertRaisesRegex(ValueError, "Served sha256 or size differs"):
                        verify.verify_live(live, self.cache, base + "/updater.json", 0)
                    path.write_bytes(original)
                    handler.stale_reads = 1
                    with self.assertRaisesRegex(ValueError, "Live updater manifest differs"):
                        verify.verify_live(live, self.cache, base + "/updater.json", 0)
                    handler.stale_reads = 1
                    with mock.patch.object(verify.time, "sleep") as sleep:
                        verify.verify_live(live, self.cache, base + "/updater.json", 1)
                    sleep.assert_called_once()
                    self.assertEqual(handler.stale_reads, 0)

    def test_live_cli_with_local_server(self):
        self.add_release("1.3.100")
        manifest = self.manifest()
        published = self.root / "site"
        shutil.copytree(self.cache / "1.3.100", published / "updates/1.3.100")
        with local_server(published) as (base, handler):
            for entry in manifest["platforms"].values():
                entry["url"] = entry["url"].replace("https://docketseo.app", base)
            (published / "updater.json").write_text(json.dumps(manifest))
            # The throwaway script uses the loopback host as its mirror origin.
            path = self.root / "scripts/stage_updates_mirror.py"
            path.write_text(path.read_text().replace('MIRROR = "https://docketseo.app/updates"',
                                                    f'MIRROR = "{base}/updates"'))
            result = self.script("verify_updates_mirror", "--live", "--manifest-url", base + "/updater.json", "--wait", "0")
            self.assertIn("Range not supported", result.stdout)
            self.assertEqual(len([value for _, value in handler.requests if value]), 3)
            (published / "updates/1.3.100/Docket.app.tar.gz").unlink()
            self.script("verify_updates_mirror", "--live", "--manifest-url", base + "/updater.json", "--wait", "0", ok=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
