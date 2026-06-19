---
name: code-quality-tools
description: >-
  Use when setting up code quality tooling for a HEP Python project: configuring
  pre-commit hooks, adding ruff for linting and auto-formatting, setting up mypy
  for static type checking, or debugging linter failures in CI or a pre-commit
  run.
---

# Code Quality Tools

## Overview

The Scientific Python community standard for code quality is:

- **pre-commit** (or prek): runs checks and auto-fixes on commit or CI
- **Ruff**: ultra-fast linter _and_ formatter (replaces flake8, isort, black)
- **mypy**: static type checker

All three are configured in `pyproject.toml` (ruff, mypy) and
`.pre-commit-config.yaml`. Run locally with `pixi run pre-commit` or
`pre-commit run --all-files`.

## When to Use

- Starting a new HEP Python package and need code quality gates
- Adding linting/formatting to an existing project
- Configuring CI to reject style violations automatically
- Adding type annotations to existing code incrementally

## Key Concepts

| Tool        | Role                                           | Config location                      |
| ----------- | ---------------------------------------------- | ------------------------------------ |
| pre-commit  | Orchestrates all hooks; runs in isolated envs  | `.pre-commit-config.yaml`            |
| ruff-format | Auto-formatter (Black-compatible, 30× faster)  | `[tool.ruff]` in pyproject.toml      |
| ruff-check  | Linter; replaces flake8, isort, pyupgrade, etc | `[tool.ruff.lint]` in pyproject.toml |
| mypy        | Static type checker                            | `[tool.mypy]` in pyproject.toml      |
| codespell   | Spell checker for code and docs                | `.pre-commit-config.yaml`            |

**Hook execution order matters**: put auto-fixers (ruff-format, ruff-check
`--fix`) _before_ linters that may fail on unfixed code.

## Canonical Patterns

### Minimal `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: "v5.0.0"
    hooks:
      - id: check-added-large-files
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: check-yaml
      - id: debug-statements
      - id: end-of-file-fixer
      - id: mixed-line-ending
      - id: name-tests-test
        args: ["--pytest-test-first"]
      - id: trailing-whitespace

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: "v0.11.0"
    hooks:
      - id: ruff-format
      - id: ruff-check
        args: ["--fix", "--show-fixes"]

  - repo: https://github.com/codespell-project/codespell
    rev: "v2.4.1"
    hooks:
      - id: codespell
        additional_dependencies: ["tomli; python_version<'3.11'"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: "v1.15.0"
    hooks:
      - id: mypy
        files: src
        args: []
```

Keep `rev:` pinned to fixed tags; update with `pre-commit autoupdate`.

### Ruff configuration in `pyproject.toml`

```toml
[tool.ruff]
src = ["src"]

[tool.ruff.lint]
extend-select = [
  "B",    # flake8-bugbear — catches common bug patterns
  "I",    # isort — sorted imports
  "UP",   # pyupgrade — modernize syntax
  "RUF",  # Ruff-specific rules
  "NPY",  # NumPy-specific rules
]
ignore = [
  "PLR2004",  # magic value comparisons (common in HEP cuts)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["T20"]  # allow print() in tests
```

### mypy configuration in `pyproject.toml`

```toml
[tool.mypy]
files = "src"
python_version = "3.11"
strict = true
warn_unreachable = true
enable_error_codes = ["ignore-without-code", "redundant-expr", "truthy-bool"]

[[tool.mypy.overrides]]
module = ["awkward.*", "uproot.*", "hist.*", "ROOT.*"]
ignore_missing_imports = true
```

Start with `strict = false` and enable incrementally if adding mypy to a large
existing codebase. Add `[[tool.mypy.overrides]]` blocks for HEP libraries that
lack type stubs.

### Running locally

```bash
# With pixi
pixi run pre-commit run --all-files

# Without pixi
pre-commit run --all-files

# Update all hook versions
pre-commit autoupdate
```

## Gotchas

- **ruff-format before ruff-check**: always list `ruff-format` first so the
  formatter fixes style before the linter sees the code.
- **mypy needs stubs for external packages**: most HEP libraries (awkward,
  uproot, hist) lack complete type stubs — add `ignore_missing_imports = true`
  per package.
- **`--fix` in ruff-check is safe**: it makes changes that you review via
  `git diff`; `--show-fixes` explains what it changed.
- **pre-commit.ci**: free service that auto-runs hooks on every PR and updates
  `rev:` pins weekly — worth enabling at pre-commit.ci for shared projects.
- **HEP-specific linting suppressions**: magic number comparisons (`PLR2004`)
  frequently false-positive on physics cuts like `pt > 30`; add to `ignore` or
  suppress per line with `# noqa: PLR2004`.
- **codespell false positives**: HEP terms like `hist`, `gaus`, `Eta` may be
  flagged. Suppress with `[tool.codespell] ignore-words-list = ["hist", "gaus"]`
  in `pyproject.toml`.

## Interop

- **pixi**: `pixi run pre-commit` wraps the hook runner; define a task in
  `pixi.toml` so contributors don't need to install pre-commit globally
- **nox**: `nox -s lint` is an alternative entry point for CI that doesn't
  require pre-commit to be installed
- **CI**: GitHub Actions can run `pre-commit run --all-files` directly, or use
  the managed `pre-commit.ci` service

## Docs

- pre-commit: https://pre-commit.com
- Ruff: https://docs.astral.sh/ruff/
- mypy: https://mypy.readthedocs.io/
- Scientific Python style guide:
  https://learn.scientific-python.org/development/pages/guides/style/
