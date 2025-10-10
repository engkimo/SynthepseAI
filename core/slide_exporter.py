"""
Lightweight slide generator for artifacts.

Generates a Marp-compatible `slides.md` from `report.md` (or `plan.md` as
fallback) under `workspace/artifacts/<plan_id>/slides/` without external
dependencies.

Usage:
- Call `generate_slides(artifacts_dir)` after a plan completes to refresh slides.
"""

from __future__ import annotations

import os
from typing import Optional, List


def _read_text(path: str) -> Optional[str]:
    """Safely read a UTF-8 text file and return its content, or None if missing."""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        return None
    return None


def _split_slides_from_markdown(md: str) -> List[str]:
    """
    Split markdown into slide chunks.

    Heuristic: start a new slide at each level-2 heading line starting with
    `## `. If no such headings exist, return a single-slide list.
    """
    lines = md.splitlines()
    slides: List[List[str]] = []
    current: List[str] = []

    def push_current():
        nonlocal current
        if current:
            slides.append(current)
            current = []

    has_h2 = any(line.strip().startswith("## ") for line in lines)
    if not has_h2:
        return [md.strip()]

    for line in lines:
        if line.strip().startswith("## "):
            push_current()
            # Promote H2 to H1 for slide title
            current.append("# " + line.strip()[3:].strip())
        else:
            current.append(line)
    push_current()

    # Normalize trailing whitespace
    normalized = ["\n".join(chunk).strip() for chunk in slides if any(s.strip() for s in chunk)]
    return [c for c in normalized if c]


def generate_slides(artifacts_dir: str) -> Optional[str]:
    """
    Generate a simple Marp-compatible slides.md under `<artifacts_dir>/slides/`.

    - Prefers `report.md` as the source; falls back to `plan.md`.
    - Splits slides on `## ` section headings and inserts `---` delimiters.

    Args:
        artifacts_dir: Directory for a specific plan's artifacts.

    Returns:
        Path to the generated `slides.md` or None on failure.
    """
    try:
        report_path = os.path.join(artifacts_dir, "report.md")
        plan_path = os.path.join(artifacts_dir, "plan.md")

        source_md = _read_text(report_path) or _read_text(plan_path)
        if not source_md:
            return None

        slides_chunks = _split_slides_from_markdown(source_md)

        # Compose Marp-compatible markdown with simple front matter
        header = (
            "---\n"
            "marp: true\n"
            "theme: default\n"
            "paginate: true\n"
            "---\n\n"
        )

        body = ("\n\n---\n\n").join(slides_chunks)
        slides_md = header + body + ("\n" if not body.endswith("\n") else "")

        slides_dir = os.path.join(artifacts_dir, "slides")
        os.makedirs(slides_dir, exist_ok=True)
        out_path = os.path.join(slides_dir, "slides.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(slides_md)

        return out_path
    except Exception:
        return None

