#!/usr/bin/env python3
"""Validate every SKILL.md against the Agent Skills specification.

Wraps the ``skill-validator`` CLI (https://github.com/agent-ecosystem/skill-validator)
and runs it once per plugin's ``skills/`` directory. This checks frontmatter
validity, the ``name``/``description`` constraints, directory naming, SKILL.md
line/token budgets, and — critically — that every file under a skill's
``references/`` directory is actually linked from its SKILL.md (orphaned
references are a hard error, not just a lint nit). This complements
``lint_skills.py`` (this repo's section-ordering rules).

``skill-validator`` only looks one level deep for ``SKILL.md`` files under the
given path, so it must be invoked once per plugin's ``skills/`` directory
rather than once for the whole repo.

``skill-validator`` isn't a pixi/conda dependency (no conda-forge package for
this Go binary), so it usually isn't on PATH after a fresh ``pixi install``.
When it's missing, this script falls back to ``pre-commit run skill-validator``,
which pre-commit builds and caches in its own isolated golang environment —
the same hook configured in ``.pre-commit-config.yaml`` — so `pixi run
validate-skills` works out of the box without a manual ``brew install`` step.

Exit code 0 if every plugin's skills pass, 1 otherwise.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLI = "skill-validator"


def _run_direct(plugin_skill_dirs: list[Path]) -> None:
    """Invoke the skill-validator CLI once per plugin directory (fast path)."""
    failures: list[tuple[Path, str]] = []

    for skills_dir in plugin_skill_dirs:
        result = subprocess.run(
            [CLI, "check", str(skills_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            rel = skills_dir.relative_to(ROOT)
            failures.append((rel, (result.stdout + result.stderr).strip()))

    if failures:
        for rel, msg in failures:
            print(f"=== {rel} ===\n{msg}\n")
        print(f"{len(failures)} plugin(s) failed skill validation.", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(plugin_skill_dirs)} plugin(s) valid against the Agent Skills spec.")


def _run_via_pre_commit() -> None:
    """Fall back to the pre-commit-managed skill-validator hook."""
    print(
        f"'{CLI}' not found on PATH — running it via the pre-commit hook instead "
        "(pre-commit builds it in an isolated environment on first use).",
        file=sys.stderr,
    )
    result = subprocess.run(
        ["pre-commit", "run", CLI, "--all-files"],
        cwd=ROOT,
    )
    sys.exit(result.returncode)


def main() -> None:
    if shutil.which(CLI) is None:
        _run_via_pre_commit()
        return

    plugin_skill_dirs = sorted(
        p for p in ROOT.glob("plugins/*/skills") if p.is_dir()
    )
    _run_direct(plugin_skill_dirs)


if __name__ == "__main__":
    main()
