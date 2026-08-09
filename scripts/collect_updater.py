#!/usr/bin/env python3
"""Generate site/updater.json — the manifest Docket's in-app updater reads.

Tauri's updater fetches this, compares `version` against the running build,
downloads `url`, verifies `signature` against the public key compiled into the
binary, then unpacks and relaunches.

Everything here is read from the artifacts the build just produced. The
signature in particular is read out of the `.sig` file rather than pasted:
a manifest whose signature does not match its tarball does not warn anybody,
it simply means every update is silently rejected and users sit on an old
build forever believing they are current. That is the worst failure this file
can have, so nothing in it is typed by hand.

Run after ./scripts/build_docket.sh --ship, before deploying the site.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import sys

APP = pathlib.Path("/Users/matthewkerr/Downloads/SEO audit app")
OUT = pathlib.Path(__file__).resolve().parent.parent / "site" / "updater.json"

TGZ = APP / "dist" / "Docket.app.tar.gz"
SIG = APP / "dist" / "Docket.app.tar.gz.sig"

#: Where the tarball is served from. The GitHub release, not the site: GitHub
#: Pages has a soft size limit and a 100 MB hard one per file, and serving a
#: 17 MB binary from the same host as the manifest buys nothing.
RELEASE = "https://github.com/mattkerr09/docket-site/releases/download"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True,
                    help="the version being published, e.g. 0.1.1")
    ap.add_argument("--tag", default="v0.1.0", help="release tag hosting the asset")
    ap.add_argument("--notes", default="", help="what changed, shown to the user")
    args = ap.parse_args()

    for path in (TGZ, SIG):
        if not path.is_file():
            sys.exit(f"missing {path} — run ./scripts/build_docket.sh --ship first")

    signature = SIG.read_text().strip()
    if not signature:
        sys.exit(f"{SIG} is empty; refusing to publish a manifest that rejects "
                 f"every update")

    data = {
        "version": args.version,
        "notes": args.notes or f"Docket {args.version}",
        "pub_date": datetime.datetime.now(datetime.timezone.utc)
                    .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "platforms": {
            # Apple Silicon only, and named explicitly. A manifest that also
            # claimed darwin-x86_64 would offer an arm64 binary to Intel Macs,
            # which fails after the download rather than before it.
            "darwin-aarch64": {
                "signature": signature,
                "url": f"{RELEASE}/{args.tag}/Docket.app.tar.gz",
            }
        },
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")

    digest = hashlib.sha256(TGZ.read_bytes()).hexdigest()[:16]
    print(f"  version   : {args.version}")
    print(f"  tarball   : {TGZ.name} ({TGZ.stat().st_size // 1024} KB, sha {digest})")
    print(f"  signature : {len(signature)} chars, read from {SIG.name}")
    print(f"  written   : {OUT}")


if __name__ == "__main__":
    main()
