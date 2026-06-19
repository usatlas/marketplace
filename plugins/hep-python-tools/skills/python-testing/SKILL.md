---
name: python-testing
description: >-
  Use when writing or configuring tests for a HEP Python project with pytest:
  setting up pyproject.toml test configuration, writing fixtures and
  parametrized tests, handling numerical tolerances for physics quantities,
  setting up code coverage, or choosing between unit and integration tests.
---

# Python Testing with pytest

## Overview

pytest is the standard test framework for Scientific Python. It provides simple
assertion rewriting, powerful fixtures, parametrization, and marks — all with
minimal boilerplate. For HEP code, special attention is needed for **numerical
tolerances** (physics quantities are floats), **RNG seeding** (reproducible
results), and **testing the installed package** (src layout requirement).

## When to Use

- Writing new tests alongside new functionality
- Configuring pytest for a project (first time or upgrading)
- Adding numerical tolerance checks for physics calculations
- Setting up code coverage reporting
- Debugging flaky tests or unexpected warnings

## Key Concepts

| Concept          | Notes                                                              |
| ---------------- | ------------------------------------------------------------------ |
| Test discovery   | Files named `test_*.py`; functions named `test_*`                  |
| Fixtures         | Shared setup/teardown; defined in `conftest.py` or test files      |
| Parametrize      | Run one test with many input cases via `@pytest.mark.parametrize`  |
| `pytest.approx`  | Float/array comparison with tolerance; prefer over `==` for floats |
| `filterwarnings` | `"error"` turns warnings into failures — catch issues early        |
| `src` layout     | Tests run against the **installed** package, not the local source  |

### pytest configuration in `pyproject.toml`

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = ["-ra", "--showlocals", "--strict-markers", "--strict-config"]
xfail_strict = true
filterwarnings = ["error"]
log_level = "INFO"
testpaths = ["tests"]
```

- `-ra` prints a summary of all non-passing results
- `--showlocals` prints local variables in tracebacks
- `filterwarnings = ["error"]` catches deprecation warnings before they become
  failures in upstream releases

## Canonical Patterns

### Basic test

```python
def test_jet_selection():
    jets = [30.5, 15.2, 42.1, 8.0]  # pT in GeV
    selected = [pt for pt in jets if pt > 20]
    assert selected == [30.5, 42.1]
```

### Numerical tolerance (physics values)

```python
from pytest import approx
import numpy as np

def test_invariant_mass():
    m = compute_invariant_mass(pt=50.0, eta=1.2, phi=0.5, e=120.0)
    assert m == approx(91.2, rel=1e-3)  # Z mass, 0.1% tolerance

def test_array_output():
    result = compute_weights(n_events=100)
    expected = np.ones(100)
    np.testing.assert_allclose(result, expected, rtol=1e-6)
```

Prefer `pytest.approx` for scalar comparisons (better error messages);
`np.testing.assert_allclose` for array comparisons.

### Fixture with shared data

```python
import pytest

@pytest.fixture
def sample_events():
    return {
        "jet_pt": [50.0, 30.0, 80.0],   # GeV
        "jet_eta": [0.5, 1.2, -0.8],
        "weight_mc": [1.0, 0.9, 1.1],
    }

def test_event_selection(sample_events):
    selected = [pt for pt in sample_events["jet_pt"] if pt > 40]
    assert len(selected) == 2
```

### Parametrized test

```python
import pytest

@pytest.mark.parametrize(
    "pt, eta, expected",
    [
        (50.0, 0.5, True),   # passes both cuts
        (15.0, 0.5, False),  # fails pT cut
        (50.0, 3.0, False),  # fails eta cut
    ],
    ids=["central-hard", "soft-jet", "forward-jet"],
)
def test_jet_passes_selection(pt, eta, expected):
    assert passes_selection(pt, eta, pt_min=20, eta_max=2.5) == expected
```

### Expected exceptions

```python
import pytest

def test_bad_file_raises():
    with pytest.raises(FileNotFoundError):
        load_ntuple("nonexistent.root")
```

### Code coverage

```bash
# Run with coverage (pixi)
pixi run pytest --cov=src/my_hep_tool --cov-report=term-missing

# Or via coverage directly (preferred in CI)
coverage run -m pytest
coverage report
```

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["my_hep_tool"]
branch = true

[tool.coverage.report]
exclude_also = ["if TYPE_CHECKING:"]
```

## Gotchas

- **Seed RNGs explicitly**: any test using random numbers must set a fixed seed
  (`np.random.default_rng(42)`, `random.seed(42)`) — unseeded tests are
  non-deterministic and will fail intermittently.
- **Never use `==` for floats**: physics calculations accumulate floating-point
  error; always use `pytest.approx` or `np.testing.assert_allclose`.
- **Test the installed package, not local source**: with src layout, run
  `pip install -e .` (or `pixi install`) before `pytest`; otherwise you may test
  stale or missing files.
- **`filterwarnings = ["error"]` is strict**: you will catch upstream
  deprecations immediately. Add exemptions only for known false-positives:
  `"ignore::DeprecationWarning:some_package"`.
- **Do not place `__init__.py` in `tests/`**: it confuses package discovery and
  is unnecessary.
- **Separation of unit and integration tests**: keep tests that hit real files,
  real ROOT files, or the grid in a separate file (e.g., `test_integration.py`)
  and mark them with `@pytest.mark.slow` so they can be skipped in fast CI.

## Interop

- **pixi**: run tests with `pixi run pytest`; add a `test` task to `pixi.toml`
- **nox**: `nox -s tests` is useful for CI matrix testing across Python versions
- **coverage / pytest-cov**: add `--cov` flag or run `coverage run -m pytest`
- **uproot / awkward**: for integration tests that open ROOT files, use
  `scikit-hep-testdata` for small bundled test files rather than large git blobs

## Docs

- pytest: https://docs.pytest.org/
- pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
- Scientific Python testing guide:
  https://learn.scientific-python.org/development/pages/guides/pytest/
- scikit-hep-testdata: https://github.com/scikit-hep/scikit-hep-testdata
