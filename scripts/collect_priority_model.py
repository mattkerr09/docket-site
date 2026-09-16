#!/usr/bin/env python3
"""The numbers behind "what should I fix first" — asked of the engine, not typed.

    python3 scripts/collect_priority_model.py          # write data/priority-model.json
    python3 scripts/collect_priority_model.py --check  # exit 1 if the file is stale

WHY THIS EXISTS (2026-09-16). A page explaining how Docket ranks findings has
to state the weights it ranks with, and those weights live in two engine
modules as literals. Written into prose they become the shape of number this
site refuses everywhere else: one that lives in a second place and drifts
silently, where the drift is invisible because nothing renders wrong — the page
simply describes a formula the product no longer uses.

It reads the tables themselves, so the page and the engine cannot come apart:
`models.SEVERITY_WEIGHT` and `models.EFFORT_COST`, the phase thresholds in
`scoring.action_plan`, and the action plan's default item cap. The reach curve
is recomputed here from `Finding.priority` rather than reimplemented, so a
change to that expression shows up as a stale dataset rather than as a page
that quietly rounds differently from the product.
"""
from __future__ import annotations

import inspect
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "priority-model.json"

sys.path.insert(0, str(ROOT / "scripts"))
import app_path  # noqa: E402


def read() -> dict:
    app = app_path.find()
    backend = str(app / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from seo_engine import scoring  # noqa: PLC0415
    from seo_engine.models import (  # noqa: PLC0415
        EFFORT_COST, SEVERITY_WEIGHT, Effort, Finding, Lane, Severity,
    )

    severity = {s.value: SEVERITY_WEIGHT[s] for s in Severity}
    effort = {e.value: EFFORT_COST[e] for e in Effort}
    if not severity or not effort:
        raise SystemExit("collect_priority_model: a weight table came back "
                         "empty, so nothing here would be true")

    # The phase threshold is a literal inside action_plan. Read it rather than
    # restate it: if someone moves the Quick-wins line, this goes stale.
    src = inspect.getsource(scoring.action_plan)
    match = re.search(r"finding\.impact >= ([\d.]+) and finding\.effort", src)
    if not match:
        raise SystemExit("collect_priority_model: could not find the phase "
                         "threshold in action_plan — the page must not guess it")
    phase_impact = float(match.group(1))
    quick_efforts = sorted(re.findall(r'"(trivial|small|medium|large)"', src))

    limit = inspect.signature(scoring.action_plan).parameters["limit"].default

    # Recompute the reach curve from the real property, never a copy of it.
    def reach_at(count: int) -> float:
        f = Finding(check_id="x", lane=Lane.INDEXABILITY, severity=Severity.MEDIUM,
                    title="t", detail="d", fix="f", count=count,
                    effort=Effort.TRIVIAL, impact=1.0)
        # priority = sev * impact * reach / effort_cost, with sev=2, impact=1,
        # effort_cost=1 — so the property returns the reach multiplier x 2.
        return round(f.priority / SEVERITY_WEIGHT[Severity.MEDIUM], 4)

    curve = {str(n): reach_at(n) for n in (1, 4, 9, 25, 100, 144, 500, 5000)}
    plateau = next((n for n in (100, 144, 200, 500, 1000, 5000)
                    if reach_at(n) == reach_at(5000)), None)
    if plateau is None:
        raise SystemExit("collect_priority_model: the reach curve no longer "
                         "plateaus; the page's claim that it is capped is stale")

    return {
        "severity_weight": severity,
        "effort_cost": effort,
        "phase_impact_threshold": phase_impact,
        "quick_win_efforts": quick_efforts,
        "plan_item_cap": limit,
        "reach_curve": curve,
        "reach_plateau_at": plateau,
        "reach_max": curve["5000"],
        "formula": "severity weight x impact x reach / effort cost",
        "source": ("seo_engine.models.SEVERITY_WEIGHT and EFFORT_COST, "
                   "Finding.priority, and seo_engine.scoring.action_plan"),
        "collected_by": "scripts/collect_priority_model.py",
        "note": "Generated. Do not edit by hand.",
    }


def main(argv: list) -> int:
    fresh = read()
    if "--check" in argv:
        if not OUT.is_file():
            print(f"PRIORITY MODEL stale — {OUT.name} does not exist; run "
                  f"scripts/collect_priority_model.py")
            return 1
        held = json.loads(OUT.read_text())
        drift = [k for k in ("severity_weight", "effort_cost", "reach_curve",
                             "phase_impact_threshold", "plan_item_cap",
                             "quick_win_efforts", "reach_plateau_at")
                 if held.get(k) != fresh[k]]
        if drift:
            print("PRIORITY MODEL stale — the engine changed "
                  f"{', '.join(drift)}. Re-run scripts/collect_priority_model.py")
            return 1
        print("PRIORITY MODEL ok — weights, phase threshold and reach curve "
              "match the engine")
        return 0

    OUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
    print(f"PRIORITY MODEL ok — {len(fresh['severity_weight'])} severities, "
          f"{len(fresh['effort_cost'])} effort levels, reach plateaus at "
          f"{fresh['reach_plateau_at']}")
    print(f"  written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
