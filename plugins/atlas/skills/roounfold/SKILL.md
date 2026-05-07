---
name: roounfold
description: >-
  Use when performing statistical unfolding for an ATLAS cross-section
  measurement: building a response matrix from MC, applying Bayesian iterative
  unfolding (RooUnfoldBayes), SVD unfolding (RooUnfoldSvd), bin-by-bin
  correction factors, or any other RooUnfold algorithm; handling detector-level
  fakes or backgrounds (response.Fake, SetBkg); propagating statistical and
  systematic uncertainties through the unfolding; comparing unfolding methods
  for stability; or performing closure tests.
---

# RooUnfold

## Overview

RooUnfold provides algorithms for unfolding detector effects in measured
distributions. Given a measured (reco-level) distribution and a response matrix
built from MC truth-reco pairs, it returns an estimate of the true distribution
corrected for detector resolution, acceptance, and efficiency. Seven algorithms
are implemented: Bayesian iterative (D'Agostini), SVD (Tikhonov), bin-by-bin,
TUnfold, matrix inversion, IDS, GP, and Poisson.

## When to Use

- Cross-section measurements where detector resolution smears the true
  distribution
- Differential measurements (jet pT, lepton pT, MET spectra)
- Comparing particle-level predictions to detector-corrected data
- Checking unfolding stability (number of iterations, regularisation parameter)
- Handling backgrounds not matched to truth (fakes)

## Key Concepts

| Concept              | Notes                                                              |
| -------------------- | ------------------------------------------------------------------ |
| Response matrix      | 2D histogram: x-axis = measured bins, y-axis = truth bins          |
| Migration matrix     | Response matrix normalised per truth bin                           |
| Miss                 | Truth-level event that failed reco selection — use `response.Miss` |
| Fake                 | Reco-level event with no truth match (e.g., QCD background)        |
| Efficiency           | Fraction of truth events that pass reco selection                  |
| Bayesian iterations  | More iterations → less bias, more variance; optimise with data     |
| SVD regularisation k | Number of singular values kept; k too small → oversmoothing        |

## Setup

In the ATLAS environment, RooUnfold is available via:

```bash
lsetup "lcgenv -p LCG_106a x86_64-el9-gcc14-opt" RooUnfold
```

Or build from source with pixi inside the RooUnfold repository:

```bash
pixi run python examples/RooUnfoldExample.py
```

## Canonical Patterns

**Import (critical)**: `import RooUnfold` triggers library loading, but the
classes live in ROOT's global namespace — use `ROOT.RooUnfoldBayes`, not
`RooUnfold.RooUnfoldBayes`.

```python
import ROOT
import RooUnfold  # loads the shared library; classes accessed via ROOT.*
```

**Build the response matrix from MC**:

```python
# (n_reco, reco_lo, reco_hi, n_truth, truth_lo, truth_hi)
response = ROOT.RooUnfoldResponse(40, -10.0, 10.0, 40, -10.0, 10.0)

for reco_val, truth_val, weight in mc_events:
    if passes_reco:
        response.Fill(reco_val, truth_val, weight)
    else:
        response.Miss(truth_val, weight)   # truth event that failed reco

# Reco-level events with no truth match (backgrounds, fakes)
for reco_val, weight in fake_events:
    response.Fake(reco_val, weight)
```

**Alternatively, initialise from existing TH1/TH2 histograms**:

```python
# measured and truth define bin edges; response is the 2D migration histogram
response = ROOT.RooUnfoldResponse(h_measured, h_truth, h2d_response)
```

**Bayesian unfolding (recommended for ATLAS)**:

```python
unfold = ROOT.RooUnfoldBayes(response, h_measured, 4)   # 4 iterations
h_unfolded = unfold.Hunfold()                           # TH1 with bin errors
cov_matrix = unfold.Eunfold()                           # TMatrixD covariance
unfold.PrintTable(ROOT.cout, h_truth)                   # closure validation
```

**SVD unfolding**:

```python
unfold = ROOT.RooUnfoldSvd(response, h_measured, 4)    # k=4 singular values
h_unfolded = unfold.Hunfold()
```

**Bin-by-bin (quick sanity check, no migration correction)**:

```python
unfold = ROOT.RooUnfoldBinByBin(response, h_measured)
h_unfolded = unfold.Hunfold()
```

**Subtracting a known background from the measured distribution**:

```python
unfold = ROOT.RooUnfoldBayes(response, h_measured, 4)
unfold.SetBkg(h_background)   # subtracted before unfolding
h_unfolded = unfold.Hunfold()
```

**Choosing number of iterations / k**:

- Start with 2–3 iterations and increase until the result stabilises.
- Use a closure test: unfold MC-reco with the MC-truth as the reference.
- Check the SVD d-vector to identify the natural regularisation scale.
- Validate the final choice with the L-curve method on data.

**Propagating systematic uncertainties**:

```python
# For each systematic: vary both the response matrix and measured histogram,
# unfold the varied measurement, and take the bin-by-bin difference as the
# uncertainty.
for syst_name in systematics:
    unfold_var = ROOT.RooUnfoldBayes(
        response_var[syst_name], measured_var[syst_name], 4
    )
    h_var = unfold_var.Hunfold()
    # bin-by-bin syst uncertainty: h_var - h_unfolded
```

**Closure test**:

```python
# Build response from training MC, unfold a separate MC reco sample.
unfold_closure = ROOT.RooUnfoldBayes(response, h_mc_reco, 4)
h_closure = unfold_closure.Hunfold()
unfold_closure.PrintTable(ROOT.cout, h_mc_truth)  # check residuals
```

## Algorithm Comparison

| Algorithm             | Class               | Tuning parameter   | Notes                         |
| --------------------- | ------------------- | ------------------ | ----------------------------- |
| Bayesian (D'Agostini) | `RooUnfoldBayes`    | Iterations         | Most common in ATLAS          |
| SVD (Tikhonov)        | `RooUnfoldSvd`      | Regularisation k   | Sensitive to k choice         |
| Bin-by-bin            | `RooUnfoldBinByBin` | None               | No migration correction       |
| TUnfold               | `RooUnfoldTUnfold`  | τ (regularisation) | ROOT built-in                 |
| Matrix inversion      | `RooUnfoldInvert`   | None               | Unstable with fine binning    |
| IDS                   | `RooUnfoldIds`      | Iterations         | Iterative dynamical stability |

## Gotchas

- **`import RooUnfold` does not expose classes**: use `ROOT.RooUnfoldBayes`, not
  `RooUnfold.RooUnfoldBayes`. The module's `__init__.py` replaces itself with
  the `ROOT.RooUnfold` namespace (enums/helpers), not the global-namespace
  classes.
- **Miss() is mandatory**: every truth-level event that fails reco selection
  must be passed to `response.Miss()` — omitting this biases the efficiency
  correction.
- **Fake() for backgrounds**: reco-level events with no truth match (e.g.,
  multijet fakes, pile-up) belong in `response.Fake()`, not `response.Fill()`.
- **Bin width**: response matrix bins should be at least as wide as detector
  resolution to avoid large off-diagonal migration.
- **Overflow**: include overflow consistently in both the response and measured
  histogram — any mismatch causes bias.
- **Stat uncertainty of response**: with limited MC, the response matrix
  statistical uncertainty is significant; propagate it explicitly.
- **Regularisation choice is data-dependent**: validate the final choice of
  iterations/k on data.
- **All energies/momenta in ATLAS ntuples are in MeV** — scale to GeV when
  filling response if plotting in GeV.

## Interop

- **hist / boost-histogram**: build response from awkward arrays → convert to
  ROOT TH2 via `uproot` or `ROOT.TH2D` before passing to `RooUnfoldResponse`.
- **pyhf / cabinetry**: use the unfolded distribution + covariance matrix
  (`Eunfold()`) as inputs to a pyhf measurement.
- **numpy**: use `np.histogram2d` to compute migration counts, then fill a
  `ROOT.TH2D` bin-by-bin to hand to `RooUnfoldResponse(measured, truth, h2d)`.

## Docs

https://gitlab.cern.ch/RooUnfold/RooUnfold
