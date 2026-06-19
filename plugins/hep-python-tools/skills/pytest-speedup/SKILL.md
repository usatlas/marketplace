---
name: pytest-speedup
description: >-
  Use when a pytest suite is slow and needs speeding up: profiling slow tests,
  reducing collection time, parallelizing with pytest-xdist or pytest-split,
  selecting a subset of tests to run, blocking inadvertent network or large-file
  disk access in HEP tests, or optimizing CI test run time.
---

# Pytest Speedup

## Overview

A slow test suite discourages running tests locally and wastes CI minutes. The
discipline is **measure-first**: change one thing, measure locally and on CI,
keep it only if it actually helps. HEP suites have specific bottlenecks — heavy
import cost from libraries like uproot, awkward, and torch shows up on every
collection even for a single test; large ROOT files inflate fixture setup; and
network-backed fixtures accidentally call xrootd or rucio endpoints. Address the
bottleneck, not the symptom.

## When to Use

- A `pytest` run feels slow and you want to identify where time is spent
- Collection alone (before any test runs) is sluggish
- CI runs take too long and you want to shard or parallelize them
- Tests unexpectedly hit the network (xrootd, rucio, HTTP) or write large files
- Skipping known-slow tests locally while keeping them in full CI runs
- Writing the tests themselves → invoke `hep-python-tools:python-testing`
- Wiring CI steps (GitHub Actions matrix, coverage upload) → invoke
  `hep-python-tools:code-quality-tools`

## Key Concepts

| Concept                   | Notes                                                         |
| ------------------------- | ------------------------------------------------------------- |
| `pytest --durations N`    | Print N slowest tests/setup/teardown after a run              |
| `pytest --collect-only`   | Measure collection time without running any tests             |
| `pytest --noconftest`     | Skip `conftest.py` loading — isolates conftest import cost    |
| `pytest --trace-config`   | List all active plugins including builtins                    |
| `pytest --lf`             | Re-run only last-failed tests (fast local iteration)          |
| `PYTHONDONTWRITEBYTECODE` | Skip `.pyc` generation — small win on dev machines and CI     |
| `pytest-xdist`            | Parallel execution across CPU cores; `-n auto` uses all cores |
| `pytest-split`            | CI sharding: splits by stored durations across N runners      |
| `pytest-skip-slow`        | Mark tests `@pytest.mark.slow`; skip unless `--slow` passed   |
| `pytest-socket`           | Block socket calls; catches accidental network access         |

## Canonical Patterns

**Measure the whole suite with hyperfine**:

```bash
# Install: pixi add --feature test hyperfine  (or: brew install hyperfine)
hyperfine --warmup 1 'pytest tests/'
```

**Find the ten slowest tests**:

```bash
pytest --durations 10
```

**Profile import cost (critical for HEP libraries)**:

```bash
python -X importtime -m pytest --collect-only 2>&1 | grep 'import time'
# Paste stderr into: https://kmichel.github.io/python-importtime-graph/
```

Import cost from `uproot`, `awkward`, `hist`, or `torch` can dominate collection
time even when running a single test. Defer heavy top-level imports to inside
the fixture body or test function where possible.

**Speed up collection** in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
norecursedirs = ["docs", "*.egg-info", ".git", ".tox", "notebooks"]
```

Check whether `conftest.py` is the bottleneck:

```bash
pytest --collect-only --noconftest   # significantly faster? conftest is the culprit
```

**Disable `.pyc` generation** in CI env and `~/.profile`:

```bash
export PYTHONDONTWRITEBYTECODE=1
```

**Disable unused builtin plugins**:

```bash
# List all active builtins:
pytest --trace-config | grep 'active plugin'

# Disable ones you don't use (saves their import/registration cost):
pytest -p no:doctest -p no:pastebin
```

Only disable plugins that actually appear in `--trace-config`; `-p no:<name>`
errors if no such plugin is registered. (The `nose` compatibility plugin was
removed in modern pytest, so `-p no:nose` no longer applies.)

Add permanently via `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = ["-p", "no:doctest", "-p", "no:pastebin"]
```

**Run only last-failed tests (fast local iteration)**:

```bash
pytest --lf        # last-failed only
pytest --lf --ff   # last-failed first, then the rest
```

**Skip known-slow tests locally**:

```python
import pytest

@pytest.mark.slow
def test_full_analysis_chain():
    ...   # opens real ROOT files, hits rucio, takes >10s
```

```bash
pytest          # skips @pytest.mark.slow (fast local run)
pytest --slow   # runs everything (CI)
```

Requires `pytest-skip-slow`. Register the mark to avoid warnings:

```toml
[tool.pytest.ini_options]
markers = ["slow: marks tests as slow (skipped by default; run with --slow)"]
```

**Block inadvertent network access** (`pytest-socket`):

```toml
# pyproject.toml — disable globally
[tool.pytest.ini_options]
addopts = ["--disable-socket"]
```

```python
# conftest.py — allowlist specific hosts for integration tests
import pytest

@pytest.mark.allow_hosts(["xcache.example.cern.ch"])
def test_xrootd_read():
    ...
```

Catches accidental xrootd, rucio, or HTTP calls in unit tests that should be
fast and offline.

**Use `tmp_path` and `scikit-hep-testdata` instead of committing large files**:

```python
import skhep_testdata

def test_read_nanoaod(tmp_path):
    path = skhep_testdata.data_path("nanoAOD_2015_CMS_Open_Data_ttbar.root")
    # path is a real local file; use tmp_path for any output artifacts
```

Avoids multi-MB ROOT blobs in the repository and keeps fixture cost predictable.

**Parallelize across cores with pytest-xdist**:

```bash
pytest -n auto    # use all available cores
pytest -n 4       # use exactly 4 workers
```

**Shard across CI runners with pytest-split**:

```yaml
# .github/workflows/ci.yml
strategy:
  matrix:
    group: [1, 2, 3, 4]
steps:
  - run: |
      pytest --splits 4 --group ${{ matrix.group }} \
             --durations-path .test_durations
```

Merge coverage after all shards complete:

```bash
coverage combine
coverage xml
```

## Gotchas

- **Always measure before and after**: adding a plugin or config option can make
  things slower. A `hyperfine` run before and after each change is sufficient.
- **`-n auto` is not free**: worker startup and per-worker session fixture cost
  add overhead. On small suites (<100 fast tests), xdist can be _slower_ than a
  single-process run.
- **xdist runs session-scoped fixtures per worker, not once**: work around this
  by keying shared state on the `worker_id` fixture, or use `pytest-split` for
  CI sharding (which avoids the problem entirely).
- **`pytest-split` requires a stored durations file** (`.test_durations`): the
  first run splits naïvely by count; durations stabilize after a few CI runs.
  Also fix the `pytest-randomly` seed identically across all shards so each
  shard gets a consistent subset.
- **Heavy HEP imports dominate collection**: even
  `pytest tests/unit/test_one.py` triggers a full `import uproot` if it appears
  at the top of a `conftest.py`. Move such imports to fixture bodies or test
  functions where possible.
- **`pyfakefs` does not intercept C-extension I/O**: uproot and ROOT open files
  via C libraries that bypass the fake filesystem. Use `tmp_path` for those
  tests instead of `pyfakefs`.
- **`filterwarnings = ["error"]` plus new plugins**: some speedup plugins emit
  deprecation warnings under strict settings — audit for new failures after
  adding any plugin.

## Interop

- **python-testing**: defines the tests being sped up; fixture scope choices
  (session vs function) directly affect xdist compatibility
- **pixi / hatch**: add speedup dependencies to the test feature
  (`pixi add --feature test pytest-xdist pytest-socket pytest-skip-slow`) and
  run via `pixi run pytest`
- **code-quality-tools / GitHub Actions**: set `PYTHONDONTWRITEBYTECODE=1` in
  the workflow `env:` block; use a matrix strategy for `pytest-split` sharding
- **pytest-cov**: when using `pytest-split`, always run `coverage combine` after
  all shards before uploading to Codecov or generating the final report

## Docs

- Awesome pytest speedup: https://github.com/zupo/awesome-pytest-speedup
- pytest caching / `--lf`: https://docs.pytest.org/en/stable/how-to/cache.html
- pytest-xdist: https://pytest-xdist.readthedocs.io/
- pytest-split: https://github.com/jerry-git/pytest-split
- scikit-hep-testdata: https://github.com/scikit-hep/scikit-hep-testdata
