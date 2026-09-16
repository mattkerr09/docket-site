#!/usr/bin/env python3
"""The AI crawlers Docket checks — asked of the engine, not typed.

    python3 scripts/collect_ai_agents.py          # write data/ai-agents.json
    python3 scripts/collect_ai_agents.py --check  # exit 1 if the file is stale

WHY THIS EXISTS (2026-09-16). The home page promises "Every AI crawler in one
pass". A page that explains what that means has to say how many and which, and
that list is the single most volatile table in the engine: OpenAI split
`OAI-SearchBot` out of `GPTBot` after launch, Anthropic retired `Claude-Web`,
Google added `Google-CloudVertexBot`. A number typed into prose beside a table
that changes every few months is the worst case this site has — it is wrong
within weeks and nothing renders differently.

It reads `robots.AI_USER_AGENTS`, which is the table the checks themselves use,
so the page and the product cannot disagree about which crawlers were examined.
The purpose split is carried through as the engine words it rather than
re-bucketed here, because "training" versus "search index" is the distinction
the whole page turns on and re-deriving it would be a second opinion.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ai-agents.json"

sys.path.insert(0, str(ROOT / "scripts"))
import app_path  # noqa: E402


def read() -> dict:
    app = app_path.find()
    backend = str(app / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from seo_engine.robots import AI_USER_AGENTS  # noqa: PLC0415

    if not AI_USER_AGENTS:
        raise SystemExit("collect_ai_agents: the table is empty — a count here "
                         "would be a lie")

    agents = {}
    for name, meta in AI_USER_AGENTS.items():
        for key in ("owner", "purpose", "impact"):
            if not meta.get(key):
                raise SystemExit(f"collect_ai_agents: {name} has no {key}; the "
                                 "page prints all three and must not print a gap")
        agents[name] = {k: meta[k] for k in ("owner", "purpose", "impact")}

    owners = Counter(m["owner"] for m in agents.values())
    purposes = Counter(m["purpose"] for m in agents.values())

    return {
        "count": len(agents),
        "owner_count": len(owners),
        "agents": dict(sorted(agents.items())),
        "by_owner": dict(sorted(owners.items())),
        "by_purpose": dict(sorted(purposes.items())),
        "source": "seo_engine.robots.AI_USER_AGENTS, the table the checks read",
        "collected_by": "scripts/collect_ai_agents.py",
        "note": "Generated. Do not edit by hand.",
    }


def main(argv: list) -> int:
    fresh = read()
    if "--check" in argv:
        if not OUT.is_file():
            print(f"AI AGENTS stale — {OUT.name} does not exist; run "
                  f"scripts/collect_ai_agents.py")
            return 1
        held = json.loads(OUT.read_text())
        if held.get("agents") != fresh["agents"]:
            was, now = set(held.get("agents") or {}), set(fresh["agents"])
            added, gone = sorted(now - was), sorted(was - now)
            bits = []
            if added:
                bits.append(f"added {', '.join(added)}")
            if gone:
                bits.append(f"removed {', '.join(gone)}")
            if not bits:
                bits.append("changed an owner, purpose or impact line")
            print(f"AI AGENTS stale — the engine {'; '.join(bits)}. Re-run "
                  f"scripts/collect_ai_agents.py")
            return 1
        print(f"AI AGENTS ok — {fresh['count']} crawler(s) from "
              f"{fresh['owner_count']} operator(s), matching the engine")
        return 0

    OUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
    print(f"AI AGENTS ok — {fresh['count']} crawler(s) from "
          f"{fresh['owner_count']} operator(s)")
    print(f"  written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
