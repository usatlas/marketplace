---
name: roounfold
description: >-
    Use when performing statistical unfolding for an ATLAS cross-section
    measurement: building a response matrix from MC, applying Bayesian
    iterative unfolding (RooUnfoldBayes) or SVD unfolding (RooUnfoldSVD),
    propagating statistical and systematic uncertainties through the unfolding,
    or comparing unfolding methods for stability.
---

# RooUnfold

## Overview

RooUnfold provides algorithms for unfolding detector effects in measured distributions. Given a measured (reco-level) distribution and a response matrix (built from MC truth-reco pairs), it returns an unfolded estimate of the true distribution corrected for detector resolution, acceptance, and efficiency. The primary algorithms are Bayesian iterative (D'Agostini) and SVD (Tikhonov regularisation).

## When to Use

- Cross-section measurements where detector resolution smears the true distribution
- Differential measurements (jet pT, lepton pT, missing ET spectra)
- Comparing particle-level predictions to detector-corrected data
- Checking unfolding stability (number of iterations, regularisation parameter)

## Key Concepts

| Concept | Notes |
|---|---|
| Response matrix | 2D histogram: rows = truth bins, cols = reco bins, filled with MC |
| Migration matrix | Same as response matrix but normalised per truth bin |
| Efficiency | Fraction of truth events that pass reco selection |
| Bayesian iterations | More iterations → less bias, more variance; optimise with data |
| SVD regularisation k | Number of singular values kept; k too small → oversmoothing |

## Canonical Patterns

**Build the response matrix from MC**:
```python
import ROOT
import RooUnfold

# Create response matrix: (n_reco_bins, n_truth_bins)
response = RooUnfold.RooUnfoldResponse(
    n_reco, reco_lo, reco_hi,    # reco axis
    n_truth, truth_lo, truth_hi  # truth axis
)

# Fill from MC (loop over events)
for reco_val, truth_val, weight in mc_events:
    if passes_reco_selection:
        response.Fill(reco_val, truth_val, weight)
    else:
        response.Miss(truth_val, weight)  # truth-level event that failed reco selection
```

**From numpy/awkward arrays (more practical)**:
```python
import numpy as np

# Build using a 2D numpy histogram
h2d, reco_edges, truth_edges = np.histogram2d(
    reco_vals[reco_mask], truth_vals[reco_mask],
    bins=[reco_bins, truth_bins], weights=weights[reco_mask]
)
# Convert to ROOT TH2 and wrap in RooUnfoldResponse
```

**Bayesian unfolding (recommended)**:
```python
unfold = RooUnfold.RooUnfoldBayes(response, measured_hist, n_iterations=4)
unfolded = unfold.Hunfold()   # ROOT TH1 with unfolded distribution
unfolded_errors = unfold.Eunfold()  # covariance matrix
```

**SVD unfolding**:
```python
unfold = RooUnfold.RooUnfoldSvd(response, measured_hist, k_reg=4)
unfolded = unfold.Hunfold()
```

**Choosing number of iterations / k**:
- Start with a low value (2–3 iterations) and increase until the result stabilises
- Use closure test: unfold MC-reco with MC-truth as truth → check residuals
- Check d-vector from SVD to identify natural regularisation scale

**Propagating systematic uncertainties**:
```python
# For each systematic variation:
# 1. Vary the measured histogram (data-level effect)
# 2. Vary the response matrix (MC-level effect)
# 3. Unfold the varied measured histogram with the varied response
# 4. Take the difference from nominal as the uncertainty

for syst_name in systematics:
    unfold_var = RooUnfold.RooUnfoldBayes(response_var[syst_name], measured_var[syst_name], 4)
    unfolded_var = unfold_var.Hunfold()
    syst_uncertainty = unfolded_var - unfolded  # bin-by-bin difference
```

**Closure test**:
```python
# Build response from half the MC, unfold the other half's reco distribution
unfold_closure = RooUnfold.RooUnfoldBayes(response, mc_reco_hist, n_iterations=4)
unfolded_closure = unfold_closure.Hunfold()
# Compare to mc_truth_hist — should agree within statistical uncertainty
```

## Algorithm Comparison

| Feature | Bayesian (D'Agostini) | SVD (Tikhonov) |
|---|---|---|
| Tuning parameter | Number of iterations | Regularisation k |
| Bias control | More iterations = less bias | Larger k = less bias |
| Stability | Generally stable | Sensitive to k choice |
| ATLAS usage | Most common | Used in some SM analyses |
| Uncertainty handling | Propagated analytically | Via covariance matrix |

## Gotchas

- **Efficiency correction**: If events can fail the reco selection, use `response.Miss()` for every truth-level event that doesn't pass — failing to do this biases the result
- **Bin width effects**: Response matrix bins should be at least as wide as detector resolution in that variable
- **Overflow**: Include overflow in the response matrix or explicitly exclude it — inconsistency causes bias
- **Stat uncertainty of response**: For analyses with limited MC, the response matrix statistical uncertainty is significant — propagate it
- **Regularisation choice is data-dependent**: Final choice of iterations/k must be validated on data using e.g. the L-curve method

## Interop

- **hist**: Build response matrix from awkward arrays → convert to ROOT TH2 for RooUnfold
- **pyhf**: Use unfolded distribution + unfolded covariance as inputs to a pyhf measurement
- **numpy**: `np.histogram2d` for response matrix building; convert to ROOT with uproot

## Docs

https://gitlab.cern.ch/RooUnfold/RooUnfold
