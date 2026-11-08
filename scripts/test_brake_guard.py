#!/usr/bin/env python3
"""The deploy refuses while the update brake holds Docket, and passes only when told to. Run by deploy.sh every time.

    python3 scripts/test_brake_guard.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "brake_guard.sh"


def run(hold: Path, past: str | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("DOCKET_DEPLOY_PAST_BRAKE", "DOCKET_BRAKE_FILE")}
    env["DOCKET_BRAKE_FILE"] = str(hold)
    if past is not None:
        env["DOCKET_DEPLOY_PAST_BRAKE"] = past
    return subprocess.run(["bash", "-c", f'source "{GUARD}"; docket_brake_guard'], env=env,
                          capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        hold = Path(tmp) / "docket.json"
        free = run(hold, None)
        assert free.returncode == 0 and "brake guard" not in free.stdout, free
        hold.write_text('{"app": "docket"}\n')
        held = run(hold, None)
        assert held.returncode == 1, held
        assert "RUNBOOK.md section 3" in held.stdout and "DOCKET_DEPLOY_PAST_BRAKE=1" in held.stdout, held.stdout
        # After the roll-forward a newer version is live, and update-brake.py refuses a plain release then.
        assert "python3 ~/ops/bin/update-brake.py release docket --clear --yes" in held.stdout, held.stdout
        for wrong in ("0", "yes", "true", ""):
            assert run(hold, wrong).returncode == 1, f"only exactly 1 may pass the brake, not {wrong!r}"
        forward = run(hold, "1")
        assert forward.returncode == 0 and "on purpose" in forward.stdout, forward
    deploy = (GUARD.parent / "deploy.sh").read_text()
    first_gate = deploy.index('echo "==> build"')
    assert deploy.index("docket_brake_guard") < first_gate, "the guard must run before anything is built or pushed"
    print("BRAKE GUARD ok: refuses while Docket is held, passes only with DOCKET_DEPLOY_PAST_BRAKE=1, runs first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
