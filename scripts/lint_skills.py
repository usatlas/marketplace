#!/usr/bin/env python3
"""Lint SKILL.md files for section ordering and required sections.

Only checks skills that follow the standard structure (i.e. have a
'## Canonical Patterns' section). Custom-format skills such as uchicago-af
or histfitter are skipped.

Exit code 0 if all checks pass, 1 if any errors are found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Canonical ordering rules
#
# These are PAIRS (A, B) meaning: if both A and B are present in a skill,
# A must appear before B. Derived from universally consistent ordering
# observed across all skills in the repo.
# ---------------------------------------------------------------------------

ORDERED_PAIRS: list[tuple[str, str]] = [
    ("Overview", "When to Use"),
    ("When to Use", "Canonical Patterns"),
    ("Canonical Patterns", "Worked Example"),
    ("Canonical Patterns", "Gotchas"),
    ("Canonical Patterns", "Interop"),
    ("Worked Example", "Troubleshooting"),
    ("Troubleshooting", "Gotchas"),
    ("Gotchas", "Interop"),
    ("Interop", "Docs"),
]

# Sections that MUST be present in any standard skill.
# "Standard" means the skill has a '## Canonical Patterns' section.
REQUIRED_IN_STANDARD_SKILL: list[str] = [
    "Overview",
    "When to Use",
    "Key Concepts",
    "Canonical Patterns",
    "Gotchas",
    "Interop",
    "Docs",
]


def _section_headings(path: Path) -> list[str]:
    """Return all top-level (##) headings in order."""
    text = path.read_text(encoding="utf-8")
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


def _heading_matches(heading: str, name: str) -> bool:
    """True if a heading equals name or starts with 'name:' / 'name '."""
    return (
        heading == name
        or heading.startswith(f"{name}:")
        or heading.startswith(f"{name} ")
    )


def _find_index(headings: list[str], name: str) -> int | None:
    """Return the index of the first heading matching name, or None."""
    for i, h in enumerate(headings):
        if _heading_matches(h, name):
            return i
    return None


def _docs_section_content(path: Path) -> str:
    """Return the text of the ## Docs section (empty string if absent)."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## Docs\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def check_skill(path: Path) -> list[str]:
    """Return a list of human-readable error strings for this SKILL.md."""
    headings = _section_headings(path)
    errors: list[str] = []

    # Skip non-standard skills (no Canonical Patterns section)
    if _find_index(headings, "Canonical Patterns") is None:
        return []

    # Required sections
    for req in REQUIRED_IN_STANDARD_SKILL:
        if _find_index(headings, req) is None:
            errors.append(f"missing required section '## {req}'")

    # Ordering pairs
    for a, b in ORDERED_PAIRS:
        idx_a = _find_index(headings, a)
        idx_b = _find_index(headings, b)
        if idx_a is not None and idx_b is not None and idx_a > idx_b:
            errors.append(
                f"section order: '## {headings[idx_a]}' (pos {idx_a + 1})"
                f" must come before '## {headings[idx_b]}' (pos {idx_b + 1})"
            )

    # Docs must be the last top-level section
    idx_docs = _find_index(headings, "Docs")
    if idx_docs is not None and idx_docs != len(headings) - 1:
        errors.append(
            f"'## Docs' must be the last section (found at pos {idx_docs + 1}"
            f" of {len(headings)})"
        )

    # Docs must contain at least one https?:// URL
    if idx_docs is not None and not re.search(r"https?://", _docs_section_content(path)):
        errors.append("'## Docs' section contains no URL (https?://)")

    return errors


def main() -> None:
    skill_files = sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))
    failures: dict[Path, list[str]] = {}

    for path in skill_files:
        errs = check_skill(path)
        if errs:
            failures[path] = errs

    if failures:
        for path, errs in failures.items():
            rel = path.relative_to(ROOT)
            for err in errs:
                print(f"{rel}: {err}")
        print(f"\n{len(failures)} skill(s) failed.", file=sys.stderr)
        sys.exit(1)

    checked = sum(
        1
        for p in skill_files
        if _find_index(_section_headings(p), "Canonical Patterns") is not None
    )
    skipped = len(skill_files) - checked
    print(f"OK: {checked} standard skill(s) checked, {skipped} non-standard skipped.")


if __name__ == "__main__":
    main()
