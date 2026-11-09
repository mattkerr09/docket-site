#!/usr/bin/env python3
"""Stage updater files locally and add them to the Pages publish branch."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".updates-cache"
MIRROR = "https://docketseo.app/updates"
RELEASE = "https://github.com/mattkerr09/docket-site/releases/download"
MAX_BYTES = 100_000_000


def version_key(version: str) -> tuple[int, ...]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid version {version!r}. Use three numeric parts.")
    return tuple(int(part) for part in version.split("."))


def artifact_names(version: str) -> tuple[str, ...]:
    version_key(version)
    return ("Docket.app.tar.gz", "Docket-x86_64.app.tar.gz",
            f"Docket-{version}-x64-setup.exe")


def file_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing regular updater file {path}")
    size = path.stat().st_size
    if not 0 < size < MAX_BYTES:
        raise ValueError(f"{path} has {size} bytes. Updater files must be nonempty and under 100 MB.")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_digest(path: Path) -> str:
    digest = file_digest(path)
    record = path.with_name(path.name + ".sha256")
    if record.is_symlink() or not record.is_file():
        raise ValueError(f"Missing sha256 record {record}")
    if record.read_text().strip() != digest:
        raise ValueError(f"sha256 differs from the record for {path}")
    return digest


@contextmanager
def cache_lock(cache: Path):
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def cached_versions(cache: Path) -> list[str]:
    if not cache.exists():
        return []
    versions = [p.name for p in cache.iterdir()
                if p.is_dir() and not p.name.startswith(".")]
    for version in versions:
        version_key(version)
        if (cache / version).is_symlink():
            raise ValueError(f"Cache version must be a regular directory {cache / version}")
    return sorted(versions, key=version_key, reverse=True)


def prune(cache: Path) -> None:
    for version in cached_versions(cache)[2:]:
        shutil.rmtree(cache / version)
        print(f"Removed cached version {version}")


def stage(version: str, source: Path, cache: Path = CACHE,
          names: tuple[str, ...] | None = None,
          release_digests: dict[str, str] | None = None) -> None:
    allowed = artifact_names(version)
    names = allowed if names is None else names
    if not names or any(name not in allowed for name in names):
        raise ValueError(f"Unexpected updater file list for {version}")
    with cache_lock(cache):
        # Copy and check everything before changing a usable cached release.
        with tempfile.TemporaryDirectory(prefix=".stage-", dir=cache) as tmp:
            prepared = Path(tmp)
            for name in names:
                original = source / name
                digest = file_digest(original)
                expected = (release_digests or {}).get(name)
                if expected and expected.lower() != f"sha256:{digest}":
                    raise ValueError(f"Release sha256 differs for {name}")
                shutil.copyfile(original, prepared / name)
                if file_digest(prepared / name) != digest:
                    raise ValueError(f"File changed while staging {name}")
                (prepared / (name + ".sha256")).write_text(digest + "\n")
            target = cache / version
            if target.is_symlink():
                raise ValueError(f"Cache version must be a regular directory {target}")
            if target.exists():
                # A release URL is immutable. A retry may repeat the same bytes.
                existing = {p.name for p in target.iterdir()}
                if existing != {p.name for p in prepared.iterdir()}:
                    raise ValueError(f"Cached file list differs for {version}. Remove that cached version before replacing it.")
                for name in names:
                    if checked_digest(target / name) != checked_digest(prepared / name):
                        raise ValueError(f"Cached bytes differ for {version}/{name}")
            else:
                prepared.rename(target)
            prune(cache)


def stage_release(version: str, tag: str, cache: Path = CACHE) -> None:
    names = artifact_names(version)
    metadata = subprocess.run(
        ["gh", "release", "view", tag, "--repo", "mattkerr09/docket-site",
         "--json", "assets"], check=True, capture_output=True, text=True)
    assets = json.loads(metadata.stdout)["assets"]
    digests = {asset["name"]: asset.get("digest") for asset in assets}
    for name in names:
        if name not in digests:
            raise ValueError(f"Release {tag} has no {name}")
    with tempfile.TemporaryDirectory(prefix="docket-release-") as tmp:
        command = ["gh", "release", "download", tag, "--repo", "mattkerr09/docket-site",
                   "--dir", tmp]
        for name in names:
            command.extend(["--pattern", name])
        subprocess.run(command, check=True)
        stage(version, Path(tmp), cache, release_digests=digests)


def mirror_entries(manifest: dict) -> list[tuple[str, str]]:
    version = manifest["version"]
    names = dict(zip(("darwin-aarch64", "darwin-x86_64", "windows-x86_64"),
                     artifact_names(version)))
    entries = []
    if not manifest["platforms"]:
        raise ValueError("Manifest has no platforms")
    for platform, entry in manifest["platforms"].items():
        name = names.get(platform)
        url = entry["url"]
        if name and url == f"{MIRROR}/{version}/{name}":
            entries.append((version, name))
        elif name and url.startswith(RELEASE + "/"):
            parts = urlsplit(url)
            if parts.path.rsplit("/", 1)[-1] != name or parts.query or parts.fragment:
                raise ValueError(f"Unexpected updater URL {url}")
        else:
            raise ValueError(f"Unexpected updater URL {url}")
    return entries


def publish_plan(manifest: dict, cache: Path = CACHE) -> list[tuple[str, Path, str]]:
    cited = mirror_entries(manifest)
    if not cited:
        return []
    versions = cached_versions(cache)[:2]
    for version, name in cited:
        if version not in versions:
            raise ValueError(f"{version}/{name} is not in the two published cache versions")
        checked_digest(cache / version / name)
    plan = []
    for version in versions:
        directory = cache / version
        files = sorted(directory.iterdir())
        payloads = [p for p in files if not p.name.endswith(".sha256")]
        if not payloads:
            raise ValueError(f"No updater files cached for {version}")
        allowed = artifact_names(version)
        for path in files:
            name = path.name.removesuffix(".sha256")
            if name not in allowed or not (directory / name).is_file():
                raise ValueError(f"Unexpected cache file {path}")
        for path in payloads:
            plan.append((f"updates/{version}/{path.name}", path, checked_digest(path)))
    return plan


def publish(branch: str, manifest: dict, root: Path = ROOT) -> None:
    cache = root / ".updates-cache"
    if not mirror_entries(manifest):
        return
    with cache_lock(cache):
        plan = publish_plan(manifest, cache)
        with tempfile.TemporaryDirectory(prefix="docket-pages-") as tmp:
            worktree = Path(tmp) / "publish"
            subprocess.run(["git", "worktree", "add", "--quiet", str(worktree), branch],
                           cwd=root, check=True)
            try:
                subprocess.run(["git", "rm", "-qr", "--ignore-unmatch", "--", "updates"],
                               cwd=worktree, check=True)
                for relative, source, digest in plan:
                    destination = worktree / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, destination)
                    if file_digest(destination) != digest:
                        raise ValueError(f"File changed while publishing {source}")
                subprocess.run(["git", "add", "--", "updates"], cwd=worktree, check=True)
                subprocess.run(["git", "commit", "-qm", "Publish cached updater files"],
                               cwd=worktree, check=True)
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                               cwd=root, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--add", metavar="VERSION")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--from-dir", type=Path)
    source.add_argument("--from-release", metavar="TAG")
    parser.add_argument("--prune", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--publish", metavar="BRANCH", help="add the mirror commit to a split publish branch")
    args = parser.parse_args()
    if bool(args.add) != bool(args.from_dir or args.from_release):
        parser.error("--add needs --from-dir or --from-release")
    if not any((args.add, args.prune, args.plan, args.publish)):
        parser.error("choose --add, --prune, --plan or --publish")
    try:
        if args.add:
            if args.from_dir:
                stage(args.add, args.from_dir)
            else:
                stage_release(args.add, args.from_release)
        if args.prune:
            with cache_lock(CACHE):
                prune(CACHE)
        if args.plan or args.publish:
            manifest = json.loads((ROOT / "site" / "updater.json").read_text())
            if args.plan:
                for relative, path, digest in publish_plan(manifest):
                    print(f"{relative}  {path.stat().st_size} bytes  sha256 {digest}")
                if not mirror_entries(manifest):
                    print("GitHub updater URLs. Publish plan is empty.")
            if args.publish:
                publish(args.publish, manifest)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"UPDATES MIRROR FAIL - {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
