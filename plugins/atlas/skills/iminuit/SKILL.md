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

## Canonical Patterns

### Unbinned negative log-likelihood (NLL)

```python
import numpy as np
from iminuit import Minuit
from iminuit.cost import UnbinnedNLL

# Data: simulated Gaussian signal
rng = np.random.default_rng(42)
data = rng.normal(loc=125.0, scale=2.0, size=500)

def pdf(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma)**2) / (sigma * np.sqrt(2 * np.pi))

cost = UnbinnedNLL(data, pdf)
m = Minuit(cost, mu=120.0, sigma=3.0)
m.limits["sigma"] = (0.01, None)    # sigma must be positive
m.migrad()     # minimize
m.hesse()      # symmetric errors from Hessian
print(m.values["mu"], m.errors["mu"])
```

### Binned extended NLL

```python
from iminuit.cost import ExtendedBinnedNLL
import numpy as np

# Define model: returns (total_yield, pdf_values_per_bin)
def model(xe, n_sig, mu, sigma, n_bkg, slope):
    centers = 0.5 * (xe[:-1] + xe[1:])
    sig = n_sig * np.exp(-0.5 * ((centers - mu) / sigma)**2) / (sigma * np.sqrt(2*np.pi))
    bkg = n_bkg * np.exp(slope * centers)
    return np.sum(sig + bkg), sig + bkg

n, xe = np.histogram(data, bins=40, range=(100, 150))
cost = ExtendedBinnedNLL(n, xe, model)
m = Minuit(cost, n_sig=400, mu=125, sigma=2, n_bkg=100, slope=-0.01)
m.limits["n_sig"] = (0, None)
m.limits["sigma"] = (0.1, 10)
m.migrad()
m.hesse()
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

# As a table:
print(m)                # prints parameter table with values, errors, limits
```

### MINOS (asymmetric errors, likelihood profiling)

```python
m.minos()               # run MINOS for all parameters
print(m.mirrors["mu"])  # MnAsymErrors object
print(m.mirrors["mu"].lower, m.mirrors["mu"].upper)
```

### Parameter fixing and scanning

```python
m.fixed["slope"] = True    # fix slope at current value
m.migrad()                 # refit with slope fixed

# Scan one parameter (profile)
x, y, ok = m.mnprofile("mu", size=30, bound=3)  # ±3σ range
```

## Gotchas

- **Always call `hesse()` after `migrad()`**: `migrad()` computes the Hessian
  internally, but calling `hesse()` explicitly ensures `m.accurate` is set and
  errors are trustworthy.
- **MINOS is slow for many parameters**: fix nuisance parameters or restrict
  `parameters=["poi"]` to run MINOS only on the POI.
- **Initial values matter**: MIGRAD is a local minimizer; bad starting points
  lead to wrong minima. Scan or grid-search if uncertain.
- **`iminuit.cost` requires numpy ufunc-compatible PDFs**: ensure your PDF
  operates element-wise on arrays, not scalars.
- **Units**: iminuit has no units — be consistent throughout the cost function.

## Interop

- **hist**: Build `hist.Hist` objects for binned fits; `hist.Hist.values()` and
  `.axes[0].centers` provide arrays for `BinnedNLL`.
- **pyhf**: For HistFactory-structured analyses use pyhf; use iminuit for custom
  or unbinned models.
- **numpy / scipy**: iminuit replaces `scipy.optimize.minimize` for likelihood
  fits with proper uncertainty estimation.

## Docs

https://scikit-hep.org/iminuit/
