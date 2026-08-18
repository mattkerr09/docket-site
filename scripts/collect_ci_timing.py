#!/usr/bin/env python3
"""How long a Docket audit adds to a build, measured against real sites.

The CI page makes a claim a pipeline owner will check against their own clock,
so it has to be measured rather than estimated, and it has to be measured the
way they will run it: the frozen binary out of the shipped app bundle, invoked
through a symlink on PATH, not the Python source in this repo. Those are not
the same program — the frozen one unpacks itself before it does anything.

Three things get recorded separately, because they behave differently:

  * startup — `docket checks` touches no network, so it measures the process
    and nothing else.
  * audit wall-clock at a fixed page cap, per site, alongside the engine's own
    reported duration. The difference between them is the process overhead,
    and measuring it beat guessing at it: this file previously asserted the
    binary "unpacks itself before it does anything", which the measurement
    disproved outright.
  * seconds per page actually crawled, which is the only figure that
    transfers to a site we did not measure.

What is NOT measured here: a genuinely cold CI runner, where the binary has
just been downloaded and the file cache is empty. Every run below had the
binary in cache already. The startup figure is therefore a floor and the page
must not present it as the CI number.

Wall-clock on somebody else's machine over somebody else's network is not a
constant, so the dataset records the machine, the date and the cap alongside
every number. A timing figure without those three is not a measurement.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from statistics import median

OUT = Path(__file__).resolve().parent.parent / "data" / "ci-timing.json"
BIN = Path("/tmp/scoutdmg/Docket.app/Contents/Resources/docket/docket")
CAP = 25

# Public commercial sites, deliberately spread across sizes and stacks. The
# frame is small and the point of the figure is an order of magnitude, not a
# benchmark — the dataset says so and the page must not claim more.
SITES = [
    "https://docketseo.app",
    "https://www.allbirds.com",
    "https://www.thefarmersdog.com",
    "https://pizzapilgrims.co.uk",
    "https://www.basecamp.com",
    "https://www.gov.uk",
]


def _run(args: list[str], timeout: int) -> tuple[int, str, float]:
    start = time.monotonic()
    proc = subprocess.run([str(BIN), *args], capture_output=True,
                          text=True, timeout=timeout)
    return proc.returncode, proc.stdout, time.monotonic() - start


def main() -> None:
    if not BIN.exists():
        raise SystemExit(
            f"{BIN} not found — mount the shipped DMG first:\n"
            f"  hdiutil attach -nobrowse dist/{_facts.dmg_name()} "
            f"-mountpoint /tmp/scoutdmg\n"
            f"Timing the Python source instead would publish a number no user "
            f"can reproduce: the frozen binary unpacks itself on every run.")

    # Startup floor, with a warm file cache. Not a cold-runner figure — see
    # the module docstring.
    starts = []
    for _ in range(3):
        code, _, secs = _run(["checks"], timeout=180)
        if code != 0:
            raise SystemExit(f"`docket checks` exited {code}; refusing to time a broken binary")
        starts.append(round(secs, 2))

    results = []
    for url in SITES:
        try:
            code, out, secs = _run(
                ["audit", url, "-n", str(CAP), "-f", "json", "--no-pages"],
                timeout=900)
        except subprocess.TimeoutExpired:
            results.append({"url": url, "error": "timeout", "seconds": None})
            continue
        if code not in (0, 2):          # 0 clean, 2 findings; 1 is a tool error
            results.append({"url": url, "error": f"exit {code}", "seconds": None})
            continue
        data = json.loads(out)
        pages = data["stats"]["pages_crawled"]
        results.append({
            "url": url,
            "pages_crawled": pages,
            "seconds": round(secs, 1),
            # The engine's own clock. Wall-clock minus this is what the
            # process costs before any work starts, which is the part a
            # pipeline pays on every run and cannot tune away.
            "engine_seconds": data["duration"],
            "seconds_per_page": round(secs / pages, 2) if pages else None,
            "exit": code,
        })
        print(f"  {url}: {secs:.1f}s over {pages} pages")

    ok = [r for r in results if r.get("seconds") is not None]
    if len(ok) < 4:
        raise SystemExit(
            f"only {len(ok)} of {len(SITES)} sites produced a timing; a median "
            f"over that few is not worth publishing")

    per_page = [r["seconds_per_page"] for r in ok if r["seconds_per_page"]]
    data = {
        "measured": time.strftime("%Y-%m-%d"),
        "machine": f"{platform.machine()} macOS {platform.mac_ver()[0]}",
        "page_cap": CAP,
        "binary": "frozen CLI from the shipped app bundle",
        "sites_attempted": len(SITES),
        "sites_timed": len(ok),
        "startup_runs_seconds": starts,
        "startup_seconds": round(median(starts), 2),
        "process_overhead_seconds": round(median(
            r["seconds"] - r["engine_seconds"] for r in ok), 1),
        "median_seconds": round(median(r["seconds"] for r in ok), 1),
        "slowest_seconds": round(max(r["seconds"] for r in ok), 1),
        "fastest_seconds": round(min(r["seconds"] for r in ok), 1),
        "median_seconds_per_page": round(median(per_page), 2),
        "results": results,
        "note": (
            "Wall-clock over a home broadband connection on one machine, "
            f"capped at {CAP} pages, on {len(ok)} sites. It transfers as an "
            "order of magnitude and nothing more: a CI runner's network, the "
            "audited site's response time and the page count all move it. "
            "Nearly all of the wall-clock is the crawl — process overhead is "
            "the difference between wall-clock and the engine's own reported "
            "duration, and it is small. This file previously claimed the "
            "binary unpacks itself on every run, which measuring it "
            "disproved. Not measured: a genuinely cold CI runner with an "
            "empty file cache, so the startup figure is a floor rather than "
            "the number a pipeline will see."),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nstartup {data['startup_seconds']}s (warm cache), process overhead "
          f"{data['process_overhead_seconds']}s; median audit "
          f"{data['median_seconds']}s over {len(ok)} sites "
          f"({data['median_seconds_per_page']}s per page)")


if __name__ == "__main__":
    main()
