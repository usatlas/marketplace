---
name: iminuit
description: >-
  Use when performing a maximum-likelihood or least-squares fit in Python with
  iminuit: defining a cost function, setting initial parameter values and
  limits, running MIGRAD or MINOS, reading fit results and covariance, profiling
  a parameter, or comparing iminuit to pyhf for binned fits.
---

# iminuit

## Overview

iminuit is a Python interface to MINUIT2, the battle-tested minimizer from CERN.
It finds parameter values that minimize a scalar cost function (negative
log-likelihood, chi-squared, etc.) and estimates uncertainties via the Hessian
(HESSE) or exact likelihood profiling (MINOS). In HEP it is used for unbinned
fits, template fits, and any minimization where pyhf's HistFactory model is not
needed.

## When to Use

- Unbinned maximum-likelihood fits (mass spectra, lifetime, etc.)
- Binned chi-squared or Poisson likelihood fits to histograms
- Custom cost functions not expressible in HistFactory JSON
- Cross-checks and quick fits outside a full statistical framework
- Profiling or scanning a likelihood without a full workspace

## Key Concepts

| Concept              | Notes                                                               |
| -------------------- | ------------------------------------------------------------------- |
| `Minuit(cost, **p0)` | Construct minimizer with cost function and initial parameter values |
| `m.migrad()`         | Run MIGRAD minimization — always call first                         |
| `m.hesse()`          | Compute symmetric errors from Hessian — call after MIGRAD           |
| `m.minos()`          | Asymmetric errors via likelihood profiling — slow but exact         |
| `m.values`           | Dict-like access to best-fit parameter values                       |
| `m.errors`           | Symmetric 1σ uncertainties (from HESSE)                             |
| `m.merrors`          | Asymmetric MINOS uncertainties (`m.merrors["param"].lower/upper`)   |
| `m.covariance`       | Covariance matrix as numpy array                                    |
| `m.valid`            | True if MIGRAD converged                                            |
| `m.accurate`         | True if HESSE succeeded and errors are reliable                     |
| `m.visualize()`      | Plot data vs. fitted model (requires matplotlib)                    |
| `m.strategy`         | 0=skip explicit Hesse in Newton steps, 1=default, 2=always explicit |

### Cost functions (`iminuit.cost`)

| Cost function         | Input model callable                   | Use when                               |
| --------------------- | -------------------------------------- | -------------------------------------- |
| `UnbinnedNLL`         | `pdf(x, *p)` — normalized PDF          | Fitting shape only to unbinned data    |
| `ExtendedUnbinnedNLL` | `density(x, *p) → (n, pdf)`            | Fitting yield + shape to unbinned data |
| `BinnedNLL`           | `cdf(xe, *p)` — normalized CDF         | Fitting shape only to a histogram      |
| `ExtendedBinnedNLL`   | `integral(xe, *p)` — scaled CDF        | Fitting yield + shape to a histogram   |
| `LeastSquares`        | `model(x, *p)` — predicted y           | Chi-squared regression with y-errors   |
| `Template`            | `t` array (n_templates × n_bins) of MC | Template fits propagating MC stats     |
| `NormalConstraint`    | `(names, values, errors)`              | Gaussian penalty on named parameters   |

**Key distinction**: `Extended*` variants fit both shape and normalization
(yield). `BinnedNLL` and `ExtendedBinnedNLL` require a CDF-like callable
evaluated at bin edges, not a PDF at bin centers.

## Canonical Patterns

### Unbinned NLL (shape-only fit)

```python
import numpy as np
from iminuit import Minuit
from iminuit.cost import UnbinnedNLL

rng = np.random.default_rng(42)
data = rng.normal(loc=125.0, scale=2.0, size=500)

def pdf(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma)**2) / (sigma * np.sqrt(2 * np.pi))

cost = UnbinnedNLL(data, pdf)
m = Minuit(cost, mu=120.0, sigma=3.0)
m.limits["sigma"] = (0.01, None)
m.migrad()
m.hesse()
print(m.values["mu"], m.errors["mu"])
```

### ExtendedBinnedNLL and BinnedNLL

Both require a **CDF-like callable at bin edges**, not a PDF at bin centers.
`ExtendedBinnedNLL` takes a scaled CDF (yield × CDF per component); `BinnedNLL`
takes a normalized CDF.

```python
from iminuit.cost import ExtendedBinnedNLL, BinnedNLL
from scipy.stats import norm, expon

def integral(xe, n_sig, mu, sigma, n_bkg, tau):
    return n_sig * norm.cdf(xe, mu, sigma) + n_bkg * expon.cdf(xe, 0, tau)

n, xe = np.histogram(data, bins=40, range=(100, 150))
cost = ExtendedBinnedNLL(n, xe, integral)
m = Minuit(cost, n_sig=400, mu=125, sigma=2, n_bkg=100, tau=10)
m.limits["n_sig", "n_bkg", "sigma", "tau"] = (0, None)
m.migrad()
m.hesse()

# BinnedNLL: pass a normalized CDF instead
def cdf(xe, mu, sigma):
    return norm.cdf(xe, mu, sigma)

cost = BinnedNLL(n, xe, cdf)
m = Minuit(cost, mu=125, sigma=2)
m.limits["sigma"] = (0.01, None)
m.migrad()
m.hesse()
```

### ExtendedUnbinnedNLL

Model returns `(total_yield, density_per_point)` — the only cost function whose
callable returns a tuple.

```python
from iminuit.cost import ExtendedUnbinnedNLL

def density(x, n_sig, mu, sigma, n_bkg, tau):
    sig = n_sig * np.exp(-0.5 * ((x - mu) / sigma)**2) / (sigma * np.sqrt(2 * np.pi))
    bkg = n_bkg * np.exp(-x / tau) / tau
    return n_sig + n_bkg, sig + bkg

cost = ExtendedUnbinnedNLL(data, density)
```

### LeastSquares (chi-squared) fit

```python
from iminuit.cost import LeastSquares

def model(x, a, b):
    return a + b * x**2

x = np.linspace(0, 10, 50)
ye = np.full_like(x, 0.5)
y = model(x, 1, 2) + rng.normal(0, 0.5, len(x))
cost = LeastSquares(x, y, ye, model)
m = Minuit(cost, a=0, b=0)
m.migrad()
```

### Read results, MINOS, and scanning

```python
print(m.valid, m.accurate)   # convergence checks — verify before using results
print(m.values, m.errors)    # best-fit values and symmetric 1σ uncertainties
print(m.covariance)          # covariance matrix (numpy array)
m.visualize()                # plot data vs. fitted model (requires matplotlib)

m.minos("mu")                # asymmetric profiled errors for one parameter
print(m.merrors["mu"].lower, m.merrors["mu"].upper)

m.fixed["slope"] = True      # fix a parameter
m.migrad()                   # refit with it fixed
x, y, ok = m.mnprofile("mu", size=30, bound=3)  # profile ±3σ
```

### Template fit and NormalConstraint

`Template` fits histogram data to MC templates, propagating finite MC
statistics. `t` is shape `(n_templates, n_bins)`; iminuit auto-names parameters
`x0, x1, …` (accessible via `m.parameters`). Yields are non-negative by
construction.

```python
from iminuit.cost import Template, NormalConstraint

c = Template(n, xe, t)
m = Minuit(c, *initial_yields)   # parameters: x0, x1, ...
m.migrad()
m.hesse()
```

`NormalConstraint` adds a Gaussian penalty; combine with `+` to constrain
nuisance parameters. Cost functions support `+` generally for simultaneous fits.

```python
from iminuit.cost import ExtendedBinnedNLL, NormalConstraint

c = ExtendedBinnedNLL(n, xe, integral) + NormalConstraint(
    ["mu", "sigma"], [0.5, 0.1], [0.1, 0.1]
)
m = Minuit(c, n_sig=400, mu=0.5, sigma=0.1, n_bkg=100, tau=10)
m.migrad()
```

## Gotchas

- **`BinnedNLL` / `ExtendedBinnedNLL` need a CDF, not a PDF**: cumulative
  integral at bin edges. Use `use_pdf="approximate"` if only a PDF is available.
- **`ExtendedBinnedNLL` model returns a single array, not a tuple**: unlike
  `ExtendedUnbinnedNLL`; iminuit differences adjacent edge values for per-bin
  expected counts.
- **Always call `hesse()` after `migrad()`**: ensures `m.accurate` is set and
  errors are trustworthy.
- **MINOS runs on all parameters by default**: `m.minos()` computes asymmetric
  errors for every parameter, including nuisances you may not care about. Pass
  specific names to limit the work: `m.minos("mu")` or `m.minos("mu", "n_sig")`.
- **Initial values matter**: MIGRAD is a local minimizer; bad starting points
  produce wrong minima. Scan or grid-search if uncertain.
- **PDFs must be vectorized**: callables must operate element-wise on arrays.
- **`m.strategy`**: 0=fast (skips explicit Hesse in Newton steps; prefer for
  more than 10 parameters), 1=default (explicit Hesse when significant
  correlations are detected), 2=careful (explicit Hesse every Newton step).
  Strategy 0 still maintains a DFP approximation of the Hesse, so scaling is not
  linear in the number of parameters — only L-BFGS achieves that. Use 2 only for
  ill-conditioned Hessians.
- **Weighted histograms**: pass shape `(n_bins, 2)` as data — column 0 is
  sum-of-weights, column 1 is sum-of-weights-squared (variance per bin).

## Interop

- **hist**: `hist.Hist.values()` and `.axes[0].edges` provide the bin-count
  array and bin-edge array for `BinnedNLL` / `ExtendedBinnedNLL`; use
  `.axes[0].extent` only for the axis range tuple `(min, max)`.
- **pyhf**: Use pyhf for HistFactory-structured analyses; iminuit for custom or
  unbinned models.
- **numpy / scipy**: `scipy.stats` provides `cdf` / `pdf` methods compatible
  with iminuit cost functions.

## Docs

https://scikit-hep.org/iminuit/
