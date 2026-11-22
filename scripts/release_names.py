"""Release filenames shared by old tags and Check Engine SEO releases."""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlsplit

PREFIXES = ("Check-Engine-SEO", "Docket")
APP_NAMES = ("Check Engine SEO.app", "Docket.app")


def arm64_dmg(version: str) -> tuple[str, ...]:
    return tuple(f"{prefix}-{version}-arm64.dmg" for prefix in PREFIXES)


def intel_dmg(version: str) -> tuple[str, ...]:
    return tuple(f"{prefix}-{version}-x86_64.dmg" for prefix in PREFIXES)


def windows_setup(version: str) -> tuple[str, ...]:
    return tuple(f"{prefix}-{version}-x64-setup.exe" for prefix in PREFIXES)


def apple_updater(signature: bool = False) -> tuple[str, ...]:
    return tuple(f"{prefix}.app.tar.gz" + (".sig" if signature else "")
                 for prefix in PREFIXES)


def intel_updater(signature: bool = False) -> tuple[str, ...]:
    return tuple(f"{prefix}-x86_64.app.tar.gz" + (".sig" if signature else "")
                 for prefix in PREFIXES)


def bundle_files(relative: str) -> tuple[str, ...]:
    return tuple(f"{name}/{relative}" for name in APP_NAMES)


def select_name(available, candidates) -> str:
    """Select from a release listing without hiding a missing asset."""
    candidates = tuple(candidates)
    for name in candidates:
        if name in available:
            return name
    raise FileNotFoundError(f"No matching release file. Tried: {', '.join(candidates)}")


def resolve(dist_dir: Path, candidates) -> Path:
    """Prefer the new name, and report every candidate when none exists."""
    candidates = tuple(candidates)
    try:
        name = select_name({name for name in candidates if (dist_dir / name).exists()}, candidates)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{dist_dir}: {exc}") from exc
    path = dist_dir / name
    if not path.is_file():
        raise ValueError(f"Expected a regular release file at {path}. Candidates: {', '.join(candidates)}")
    return path


def signed_asset(dist_dir: Path, candidates) -> tuple[Path, Path]:
    """The signature must belong to the selected file, never to its old alias."""
    candidates = tuple(candidates)
    asset = resolve(dist_dir, candidates)
    signature = asset.with_name(asset.name + ".sig")
    if not signature.is_file():
        tried = ', '.join(name + '.sig' for name in candidates)
        raise FileNotFoundError(f"Missing {signature.name} for {asset.name}. Signature candidates: {tried}")
    return asset, signature


def classify(value: str) -> tuple[str, str] | None:
    """Return the prefix and architecture of an exact release filename or URL."""
    name = Path(urlsplit(str(value)).path).name
    for index, prefix in enumerate(PREFIXES):
        for arch, candidates in (("arm64", apple_updater()), ("x86_64", intel_updater())):
            filename = candidates[index]
            if name in (filename, filename + ".sig"):
                return prefix, arch
        match = re.fullmatch(re.escape(prefix) + r"-\d+\.\d+\.\d+-(arm64\.dmg|x86_64\.dmg|x64-setup\.exe)(?:\.sig)?", name)
        if match:
            return prefix, match.group(1).split(".")[0].removesuffix("-setup")
    return None
