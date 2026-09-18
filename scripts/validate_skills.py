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
The `validate-skills` pixi task depends on `skill-validator-setup`, which runs
the hook via prek once to build and cache the binary (the same hook configured
in ``.pre-commit-config.yaml``) before this script runs — run this script
directly (rather than via `pixi run validate-skills`) and it's on you to have
already warmed that cache.

``skill-validator check`` exits 0 (clean), 2 (warnings only — e.g. a SKILL.md
over the spec's recommended line/token budget), or 1 (real errors — e.g. an
orphaned reference file, invalid frontmatter). Only exit code 1 fails this
script; exit code 2 is printed but does not fail the build, matching the
tool's own `--strict` flag description ("treat warnings as errors (exit 1
instead of 2)") — we deliberately don't pass `--strict`. Link-reachability
checks (`--skip links`) are excluded everywhere: those depend on third-party
uptime and network policy, not skill content.

Exit code 0 if every plugin's skills are error-free (warnings allowed), 1 if
any plugin has a real error.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLI = "skill-validator"
ARGS = ["check", "--skip", "links"]

PREK_CACHE_ROOTS = (
    Path.home() / ".cache" / "prek",
    Path.home() / "Library" / "Caches" / "prek",
)


def _find_cli() -> str | None:
    """Locate the skill-validator binary: bare PATH first, then prek's cache.

    Run `pixi run skill-validator-setup` (or just `pixi run validate-skills`,
    which depends on it) first if this comes back empty.
    """
    if shutil.which(CLI):
        return CLI
    for cache_root in PREK_CACHE_ROOTS:
        for candidate in cache_root.glob(f"**/{CLI}"):
            if candidate.is_file():
                return str(candidate)
    return None


def main() -> None:
    cli = _find_cli()
    if cli is None:
        print(
            f"error: '{CLI}' not found on PATH or in prek's cache. Run "
            "`pixi run skill-validator-setup` first, or install it directly "
            "with `brew tap agent-ecosystem/tap && brew install "
            "skill-validator` (requires `brew trust agent-ecosystem/tap`).",
            file=sys.stderr,
        )
        sys.exit(1)

    plugin_skill_dirs = sorted(
        p for p in ROOT.glob("plugins/*/skills") if p.is_dir()
    )
    hard_failures: list[tuple[Path, str]] = []
    warned: list[Path] = []

    for skills_dir in plugin_skill_dirs:
        result = subprocess.run(
            [cli, *ARGS, str(skills_dir)],
            capture_output=True,
            text=True,
        )
        rel = skills_dir.relative_to(ROOT)
        if result.returncode == 2:
            warned.append(rel)
            print(f"=== {rel} (warnings only, not blocking) ===\n{result.stdout}\n")
        elif result.returncode != 0:
            hard_failures.append((rel, (result.stdout + result.stderr).strip()))

    if hard_failures:
        for rel, msg in hard_failures:
            print(f"=== {rel} ===\n{msg}\n")
        print(f"{len(hard_failures)} plugin(s) failed skill validation.", file=sys.stderr)
        sys.exit(1)

    suffix = f" ({len(warned)} with non-blocking warnings)" if warned else ""
    print(f"OK: {len(plugin_skill_dirs)} plugin(s) valid against the Agent Skills spec{suffix}.")


if __name__ == "__main__":
    main()
