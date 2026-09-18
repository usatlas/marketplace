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

Exit code 0 if every plugin's skills pass, 1 otherwise.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLI = "skill-validator"


def main() -> None:
    if shutil.which(CLI) is None:
        print(
            f"error: '{CLI}' not found. Install with "
            "`brew tap agent-ecosystem/tap && brew install skill-validator` "
            "(requires trusting the tap: `brew trust agent-ecosystem/tap`), "
            "or rely on the pre-commit hook in .pre-commit-config.yaml, which "
            "pre-commit builds in its own isolated environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    plugin_skill_dirs = sorted(
        p for p in ROOT.glob("plugins/*/skills") if p.is_dir()
    )
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


if __name__ == "__main__":
    main()
