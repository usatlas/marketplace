---
name: python-packaging
description: >-
  Use when creating a new Python package, adding pyproject.toml to an existing
  project, choosing a build backend, setting up src layout, configuring VCS-based
  versioning, or managing a development environment with pixi or uv for a HEP
  Python project.
---

# Python Packaging

## Overview

Modern Python packages declare all metadata in `pyproject.toml` and use a
dedicated build backend (hatchling, flit, uv_build, etc.). The src layout
(`src/<package>/`) is the community standard. Environment management for HEP
projects should use **pixi** (preferred) or **uv**.

The Scientific Python community maintains a template (
`github.com/scientific-python/cookie`) and checker (`sp-repo-review`) that
encode these recommendations. Use them as a reference for new projects.

## When to Use

- Starting a new Python package for a HEP analysis tool or library
- Migrating an existing `setup.py` / `setup.cfg` project to `pyproject.toml`
- Choosing between build backends or environment managers
- Setting up automatic versioning from git tags
- Adding a `pixi.toml` for reproducible developer environments

## Key Concepts

| Concept            | Details                                                          |
| ------------------ | ---------------------------------------------------------------- |
| `pyproject.toml`   | Single config file; replaces `setup.py`, `setup.cfg`, `MANIFEST.in` |
| Build backend      | Hatchling is recommended; flit-core and uv_build also work well   |
| src layout         | `src/<package>/` prevents accidental local-import bugs            |
| `requires-python`  | Set minimum; **never** set an upper cap                           |
| VCS versioning     | `hatch-vcs` reads git tags; no manual version bumps              |
| pixi               | Preferred for lockfile-based reproducible environments            |

### pyproject.toml metadata (`[project]`)

```toml
[project]
name = "my-hep-tool"
description = "Short description"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dynamic = ["version"]
dependencies = [
  "awkward>=2",
  "uproot>=5",
  "hist>=2.7",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov"]
```

`dynamic = ["version"]` lets the backend compute the version; omit it only if
you pin the version manually.

### Directory layout

```text
my-hep-tool/
  pyproject.toml
  pixi.toml          # or uv.lock / environment.yaml
  src/
    my_hep_tool/
      __init__.py
      analysis.py
  tests/
    test_analysis.py
```

## Canonical Patterns

### Hatchling backend with VCS versioning

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"
```

Add these two files so `git archive` (GitHub downloads) also get the version:

`.git_archival.txt`:

```text
node: $Format:%H$
node-date: $Format:%cI$
describe-name: $Format:%(describe:tags=true,match=*[0-9]*)$
```

`.gitattributes` (append):

```text
.git_archival.txt  export-subst
```

### pixi environment

```toml
# pixi.toml
[project]
name = "my-hep-tool"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64"]

[dependencies]
python = ">=3.11"
awkward = ">=2"
uproot = ">=5"
hist = ">=2.7"

[feature.dev.dependencies]
pytest = "*"
pre-commit = "*"

[feature.dev.tasks]
test = "pytest"
pre-commit = "pre-commit run --all-files"

[environments]
dev = { features = ["dev"], solve-group = "default" }
```

### uv alternative (no pixi)

```toml
# In pyproject.toml, uv_build backend
[build-system]
requires = ["uv_build>=0.7.19"]
build-backend = "uv_build"
```

Run with `uv run pytest` or `uv sync --group dev`.

## Gotchas

- **Never use `setup.py` or `setup.cfg`** for new projects — those are
  setuptools-specific legacy files. Modern backends don't use them.
- **No upper cap on `requires-python`**: `>=3.11` is correct; `>=3.11,<4` is
  not — upper caps break installation for future Python versions.
- **src layout is required** to avoid testing the local source instead of the
  installed package; without it, `import my_hep_tool` silently picks up the
  un-installed tree.
- **Flit needs `license.file`** set explicitly in `[project]`; hatchling and
  uv_build detect it automatically.
- **`dynamic = ["version"]`** must be set when using `hatch-vcs`; otherwise
  hatchling expects a static version string.

## Interop

- **pixi**: preferred environment manager — handles both Python and non-Python
  (e.g., ROOT) dependencies via conda-forge
- **uv**: lightweight alternative to pixi for pure-Python projects
- **nox**: task runner for CI matrix tests; see
  `github.com/scikit-hep/hist/blob/main/noxfile.py` for a HEP example
- **scientific-python/cookie**: template with all conventions pre-configured
- **sp-repo-review**: audit an existing repo against the guidelines

## Docs

- Scientific Python packaging guide:
  https://learn.scientific-python.org/development/guides/packaging-simple/
- PyPA packaging tutorial: https://packaging.python.org/tutorials/packaging-projects/
- Hatchling: https://hatch.pypa.io/latest/
- pixi: https://pixi.sh/
