#!/usr/bin/env python3
"""How many optional checks reach the network — asked of the engine, not typed.

    python3 scripts/collect_connectors.py          # write data/connectors.json
    python3 scripts/collect_connectors.py --check  # exit 1 if the file is stale

WHY THIS EXISTS (2026-09-16). Five pages said "four optional checks also fetch
data Docket cannot produce alone" and the engine's connector registry held
FIVE: demand_topics, edge_access, knowledge, mail_delivery and psi. The number
was typed in five places across three modules, so when edge_access was added
nothing pointed at any of them.

The direction of the error is what makes it worth a collector rather than an
edit. The site UNDERSTATED what Docket fetches, on the pages that make the
privacy argument. A tool whose pitch is "nothing is uploaded" cannot be vague
about how many things it downloads, and "four" in five places is exactly the
shape of number this site refuses everywhere else — one that lives in a second
place and drifts.

It counts what `--offline` governs: every connector in `connectors.base.registry`
after the package is imported. That is the same set the flag turns off, so the
count and the sentence cannot come apart.
"""
from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "connectors.json"

sys.path.insert(0, str(ROOT / "scripts"))
import app_path  # noqa: E402


def read() -> dict:
    """The registry, imported from the app checkout. Raises if it cannot."""
    app = app_path.find()
    backend = str(app / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from seo_engine.connectors import base  # noqa: PLC0415
    import seo_engine.connectors as pkg  # noqa: PLC0415

    for module in pkgutil.iter_modules(pkg.__path__):
        if module.name != "base":
            importlib.import_module(f"seo_engine.connectors.{module.name}")

    keys = sorted(base.registry)
    if not keys:
        raise SystemExit("collect_connectors: the registry is empty — nothing "
                         "imported, so a count here would be a lie")
    return {
        "count": len(keys),
        "keys": keys,
        "source": "seo_engine.connectors.base.registry, the set --offline turns off",
        "collected_by": "scripts/collect_connectors.py",
        "note": ("Generated. Do not edit by hand. The count reaches prose only "
                 "through facts.optional_connectors()."),
    }


def main(argv: list) -> int:
    fresh = read()
    if "--check" in argv:
        if not OUT.is_file():
            print(f"CONNECTORS stale — {OUT.name} does not exist; run "
                  f"scripts/collect_connectors.py")
            return 1
        held = json.loads(OUT.read_text())
        if held.get("count") != fresh["count"] or held.get("keys") != fresh["keys"]:
            print(f"CONNECTORS stale — published {held.get('count')} "
                  f"({', '.join(held.get('keys') or [])}), the engine registers "
                  f"{fresh['count']} ({', '.join(fresh['keys'])}). Re-run "
                  f"scripts/collect_connectors.py")
            return 1
        print(f"CONNECTORS ok — {fresh['count']} optional check(s), matching the engine")
        return 0

    OUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
    print(f"CONNECTORS ok — {fresh['count']} optional check(s): "
          f"{', '.join(fresh['keys'])}")
    print(f"  written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
