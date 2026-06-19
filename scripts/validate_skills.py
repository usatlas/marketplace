#!/usr/bin/env python3
"""Validate every SKILL.md against the Agent Skills specification.

Wraps the ``agentskills validate`` command from the ``skills-ref`` reference
library (https://agentskills.io/specification) and runs it over every skill
directory under ``plugins/*/skills/``. This checks frontmatter validity, the
``name``/``description`` constraints, and the directory naming rules defined by
the spec — complementing ``lint_skills.py`` (this repo's section-ordering rules).

Exit code 0 if every skill is valid, 1 otherwise.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The skills-ref PyPI package installs its CLI as ``agentskills``.
CLI = "agentskills"


def main() -> None:
    if shutil.which(CLI) is None:
        print(
            f"error: '{CLI}' not found. Install with `pixi install` "
            "(it is a pypi-dependency in pixi.toml).",
            file=sys.stderr,
        )
        sys.exit(1)

    skill_dirs = sorted(p.parent for p in ROOT.glob("plugins/*/skills/*/SKILL.md"))
    failures: list[tuple[Path, str]] = []

    for skill_dir in skill_dirs:
        result = subprocess.run(
            [CLI, "validate", str(skill_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            rel = skill_dir.relative_to(ROOT)
            failures.append((rel, (result.stdout + result.stderr).strip()))

    if failures:
        for rel, msg in failures:
            print(f"{rel}: {msg}")
        print(f"\n{len(failures)} skill(s) failed spec validation.", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(skill_dirs)} skill(s) valid against the Agent Skills spec.")


if __name__ == "__main__":
    main()
