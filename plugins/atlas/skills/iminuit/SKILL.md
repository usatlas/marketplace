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
| `m.strategy`         | Minimization strategy: 0=fast, 1=default, 2=careful                 |

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

### Extended binned NLL (yield + shape fit from histogram)

`ExtendedBinnedNLL` requires an **integrated density** (scaled CDF) evaluated at
bin edges — not a per-bin PDF. The function returns the cumulative integral from
the left edge up to each `xe` value; iminuit differences adjacent values to get
expected counts per bin.

```python
from iminuit.cost import ExtendedBinnedNLL
import numpy as np
from scipy.stats import norm, expon

def integral(xe, n_sig, mu, sigma, n_bkg, tau):
    # scaled CDF: integral from -inf to xe for each component
    return n_sig * norm.cdf(xe, mu, sigma) + n_bkg * expon.cdf(xe, 0, tau)

n, xe = np.histogram(data, bins=40, range=(100, 150))
cost = ExtendedBinnedNLL(n, xe, integral)
m = Minuit(cost, n_sig=400, mu=125, sigma=2, n_bkg=100, tau=10)
m.limits["n_sig", "n_bkg", "sigma", "tau"] = (0, None)
m.migrad()
m.hesse()
```

### Binned NLL (shape-only, normalized CDF)

`BinnedNLL` requires a normalized CDF (not a PDF), evaluated at bin edges.

```python
from iminuit.cost import BinnedNLL
from scipy.stats import norm

def cdf(xe, mu, sigma):
    return norm.cdf(xe, mu, sigma)

cost = BinnedNLL(n, xe, cdf)
m = Minuit(cost, mu=125, sigma=2)
m.limits["sigma"] = (0.01, None)
m.migrad()
m.hesse()
```

### Extended unbinned NLL

`ExtendedUnbinnedNLL` model returns `(total_yield, pdf_values)` — the only cost
function whose model returns a tuple.

```python
from iminuit.cost import ExtendedUnbinnedNLL

def density(x, n_sig, mu, sigma, n_bkg, tau):
    sig = n_sig * np.exp(-0.5 * ((x - mu) / sigma)**2) / (sigma * np.sqrt(2 * np.pi))
    bkg = n_bkg * np.exp(-x / tau) / tau
    return n_sig + n_bkg, sig + bkg   # (total yield, density per point)

cost = ExtendedUnbinnedNLL(data, density)
```

### Least-squares (chi-squared) fit

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

### Read results and covariance

```python
# After migrad + hesse:
print(m.valid)          # True if fit converged
print(m.accurate)       # True if Hesse succeeded
print(m.values)         # parameter values dict
print(m.errors)         # symmetric 1σ errors
print(m.covariance)     # covariance matrix (numpy array)
print(m.fval)           # minimum value of cost function
print(m)                # prints parameter table with values, errors, limits
```

### MINOS (asymmetric errors, likelihood profiling)

```python
m.minos()               # run MINOS for all parameters
print(m.merrors["mu"].lower, m.merrors["mu"].upper)
```

### Parameter fixing and scanning

```python
m.fixed["slope"] = True    # fix slope at current value
m.migrad()                 # refit with slope fixed

# Scan one parameter (profile)
x, y, ok = m.mnprofile("mu", size=30, bound=3)  # ±3σ range
```

### Template fit (MC templates with statistical uncertainty)

`Template` fits histogram data to a sum of MC-derived templates, correctly
propagating the finite MC statistics into the result. `t` is a 2D array of shape
`(n_templates, n_bins)`; the fit parameters are one yield per template.

```python
from iminuit.cost import Template
import numpy as np

# t[i] = MC histogram for component i (counts, not normalized)
# n    = observed data histogram
# xe   = bin edges
c = Template(n, xe, t)             # default method handles MC uncertainties
m = Minuit(c, *initial_yields)
m.limits = (0, None)               # yields must be non-negative
m.migrad()
m.hesse()
```

### Adding constraints (`NormalConstraint`)

`NormalConstraint` adds a Gaussian penalty term to any cost function. Combine
with `+` to constrain nuisance parameters to external measurements.

```python
from iminuit.cost import ExtendedBinnedNLL, NormalConstraint

# Constrain mu to 0.5 ± 0.1 and sigma to 0.1 ± 0.1
c = ExtendedBinnedNLL(n, xe, integral) + NormalConstraint(
    ["mu", "sigma"], [0.5, 0.1], [0.1, 0.1]
)
m = Minuit(c, n_sig=400, mu=0.5, sigma=0.1, n_bkg=100, tau=10)
m.migrad()
```

### Combining cost functions

Cost functions can be added together to perform simultaneous fits with shared
parameters:

```python
combined = cost1 + cost2
m = Minuit(combined, **shared_params)
m.migrad()
```

## Gotchas

- **`BinnedNLL` and `ExtendedBinnedNLL` need a CDF, not a PDF**: pass a function
  returning the cumulative integral at bin edges, not the density at centers.
  Use `use_pdf="approximate"` if only a PDF is available.
- **`ExtendedBinnedNLL` model does NOT return a tuple**: unlike
  `ExtendedUnbinnedNLL`, the integral callable returns a single array; iminuit
  computes the per-bin expected counts from differences of adjacent values.
- **Always call `hesse()` after `migrad()`**: `migrad()` computes the Hessian
  internally, but calling `hesse()` explicitly ensures `m.accurate` is set and
  errors are trustworthy.
- **MINOS is slow for many parameters**: fix nuisance parameters or restrict
  `parameters=["poi"]` to run MINOS only on the POI.
- **Initial values matter**: MIGRAD is a local minimizer; bad starting points
  lead to wrong minima. Scan or grid-search if uncertain.
- **PDFs must be vectorized**: `iminuit.cost` callables must operate
  element-wise on arrays, not scalars.
- **Units**: iminuit has no units — be consistent throughout the cost function.
- **`m.strategy`**: default is 1; set to 0 for faster convergence when fitting
  many parameters (>10) — scales linearly instead of quadratically with
  parameter count. Use 2 only for difficult fits where the Hesse matrix changes
  rapidly.
- **Weighted histograms**: pass an array of shape `(n_bins, 2)` instead of
  `(n_bins,)` as data to `BinnedNLL` or `ExtendedBinnedNLL`, where column 0 is
  sum-of-weights and column 1 is sum-of-weights-squared (variance estimate per
  bin).

## Interop

- **hist**: Build `hist.Hist` objects for binned fits; `hist.Hist.values()` and
  `.axes[0].extent` provide arrays for `BinnedNLL` / `ExtendedBinnedNLL`.
- **pyhf**: For HistFactory-structured analyses use pyhf; use iminuit for custom
  or unbinned models.
- **numpy / scipy**: iminuit replaces `scipy.optimize.minimize` for likelihood
  fits with proper uncertainty estimation. `scipy.stats` provides convenient
  `cdf` and `pdf` methods compatible with iminuit cost functions.

## Docs

https://scikit-hep.org/iminuit/
