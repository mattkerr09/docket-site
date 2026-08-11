"""Where the Docket app checkout is — asked once, not typed fifteen times.

The app moved from `~/Downloads/SEO audit app` to `~/Projects/docket-app` on
2026-08-11 and fifteen lines across fourteen scripts still pointed at the old
place. They were written five different ways — an absolute string, `Path.home()
/ "Downloads" / …`, a `parents[2]` walk, and two more — so there was no single
thing to change and no way to grep for one.

Every one of those scripts collects a number this site publishes. A collector
that cannot find the engine does not print a wrong number; it raises, and the
deploy gate stops. That is the good outcome and it is why this was caught. It
is still fifteen copies of one fact.

Resolution order, first hit wins:

  1. `$DOCKET_APP`, so a checkout anywhere can be named without editing code.
  2. `../docket-app` beside this repo, which is the current layout.
  3. The historical locations, so an older checkout still works.

`find()` raises with the list it tried rather than returning a path that does
not exist, because a collector failing on a missing directory is legible and
one silently reading nothing is not.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Tried in order. The first that exists and looks like the app wins.
CANDIDATES = (
    Path.home() / "Projects" / "docket-app",
    Path.home() / "Downloads" / "SEO audit app",
    Path.home() / "docket-app",
)

#: A file that only the app checkout has, so a directory that merely has the
#: right name is not mistaken for it.
MARKER = Path("backend") / "seo_engine" / "registry.py"


def _looks_like_the_app(path: Path) -> bool:
    return (path / MARKER).is_file()


def find() -> Path:
    """The app checkout. Raises if it is not where any of these say."""
    tried = []

    override = os.environ.get("DOCKET_APP", "").strip()
    if override:
        path = Path(override).expanduser()
        if _looks_like_the_app(path):
            return path
        tried.append(f"$DOCKET_APP={path}")

    beside = Path(__file__).resolve().parents[2] / "docket-app"
    for path in (beside, *CANDIDATES):
        if _looks_like_the_app(path):
            return path
        tried.append(str(path))

    raise FileNotFoundError(
        "cannot find the Docket app checkout. Set $DOCKET_APP to it, or put it "
        "beside this repo as ../docket-app. Tried:\n  " + "\n  ".join(tried))


def backend() -> Path:
    """The importable engine root — what goes on `sys.path`."""
    return find() / "backend"


def engine() -> Path:
    """The `seo_engine` package itself."""
    return backend() / "seo_engine"


def on_path() -> Path:
    """Put the engine on `sys.path` and return the app root."""
    import sys

    root = find()
    entry = str(root / "backend")
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return root
