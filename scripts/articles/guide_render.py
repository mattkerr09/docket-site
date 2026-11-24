"""Render guides whose next step is their own free check or audit, followed by the site's shared next step.

24 Nov 2026 (Quality Desk ruling on the content audit, CONTENT-STANDARD rules 2 and 8): these guides used to drop the shared
offer block and end only in the free online checker, so no page of the family carried a tracked hub /dl or /buy link. They now keep
the shared "Try it free, Buy beside it" block like every other article; the guide's own free-checker ending stays above it.
"""
from __future__ import annotations

from pathlib import Path

import render as site_render


def render_free_guide(**kwargs) -> Path:
    return site_render.render(**kwargs)
