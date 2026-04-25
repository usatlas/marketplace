---
name: xroofit
description: >-
  Use when building RooFit statistical models with xRooFit, constructing
  workspaces with channels and samples, adding systematics or nuisance
  parameters, fitting models to data, constructing NLL functions, diagnosing fit
  convergence failures (status codes, covariance quality), computing profile
  likelihood ratios, calculating CLs upper limits or exclusion contours, or
  computing discovery significance.
---

# xRooFit

## Overview

xRooFit is a high-level Python/C++ API for the RooFit statistical analysis
toolkit, with the same relationship to RooFit as Keras has to TensorFlow: RooFit
can be used directly, but xRooFit makes building and fitting models
significantly more concise. xRooFit ships pre-installed with ROOT ≥ 6.30 and is
also distributed as part of the ATLAS
[StatAnalysis](https://gitlab.cern.ch/atlas/StatAnalysis) release.

## When to Use

- Building HistFactory-style statistical models programmatically with Python or
  C++ as an alternative to TRExFitter config files or HistFactory XML
- Manipulating or inspecting workspaces produced by TRExFitter or HistFitter
- Performing CLs upper limits, exclusion contours, or discovery significance
  tests using asymptotic formulae on a RooFit workspace
- Diagnosing fit convergence problems via status codes and covariance quality
- Choosing ROOT/RooFit-based statistics over pyhf when C++ performance, custom
  RooFit classes, or direct RooStats infrastructure access is required

## Key Concepts

### xRooNode

All objects in xRooFit are accessed through `xRooNode`, a smart pointer-like
wrapper that adds methods on top of the underlying RooFit object. In Python,
unknown attribute access is forwarded to the wrapped object, so workspace
methods are available directly:

```python
w = XRF.xRooNode("workspace.root")   # loads first workspace from file
w.factory("Gaussian::g(x[0,-5,5], mu[0,-3,3], sigma[1])")  # delegates to RooWorkspace
```

Navigate the workspace hierarchy with path syntax:

```python
w["pdfs/simPdf/SR/samples/bkg"]   # channel SR, sample bkg
w["pdfs"]["simPdf"]["SR"]          # equivalent
```

### Variable types

| Type                    | Symbol | xRooNode method | Description                                        |
| ----------------------- | ------ | --------------- | -------------------------------------------------- |
| Regular observables     | x      | `robs()`        | Column in the dataset                              |
| Global observables      | a      | `globs()`       | Auxiliary measurements (constraint nominal values) |
| All observables         |        | `obs()`         | All of the above                                   |
| Parameters of interest  | μ      | `poi()`         | Floatable, marked as POI                           |
| Nuisance parameters (α) | ν      | `np()`          | Gaussian-constrained NPs                           |
| Nuisance parameters (γ) | ν      | `np()`          | Poisson-constrained (MC-stat) NPs                  |
| All parameters          | θ      | `pars()`        | Everything that is not an observable               |
| Prespecified parameters |        | `pp()`          | Non-floatable (always constant) parameters         |
| Floating                |        | `floats()`      | Currently floating subset                          |
| Constant                |        | `consts()`      | Currently constant subset                          |

Mark or unmark parameters:

```python
w.pars().reduced("alpha_*").setAttribAll("Constant")  # fix all alpha NPs
w.pars()["mu_sig"].setAttribute("poi")               # promote to POI
w.floats().Print()                                   # list floating pars
```

## Canonical Patterns

### Setup

```python
# Option 1 — StatAnalysis (recommended for ATLAS users)
# In the shell:
#   setupATLAS && asetup StatAnalysis,0.7,latest
import ROOT as XRF               # xRooFit built on top of ROOT

# Option 2 — ROOT's bundled version (≥ 6.30)
import ROOT
from ROOT.Experimental import XRooFit as XRF
```

Using `import ROOT as XRF` (option 1) is the recommended form in the xRooFit
docs and is used in all examples below. Methods that are specific to the
built-in version would use `XRF.xRooFit.<method>` in both options.

#### Standalone build (if not using StatAnalysis)

```bash
git clone https://:@gitlab.cern.ch:8443/will/xroofit.git
cmake -S xroofit -B xroofit_build && cmake --build xroofit_build
source xroofit_build/setup.sh   # add to PATH each session
```

Requires ROOT ≥ 6.32 (6.38+ recommended). The StatAnalysis 0.7 branch provides
ROOT 6.38 on EL9.

### Building a workspace from scratch

```python
import ROOT as XRF

w = XRF.xRooNode("RooWorkspace", "combined", "my workspace")

# Multi-channel (RooSimultaneous) top-level PDF
w["pdfs"].Add("simPdf")

# Add a channel (RooProdPdf)
w["pdfs/simPdf"].Add("SR").SetTitle("Signal Region")

# Declare the observable and add a sample from a histogram
hBkg = XRF.TH1D("bkg", "Background;m_{T2} [GeV]", 5, 200, 700)
hBkg.GetXaxis().SetName("mt2")   # observable name
# ... fill histogram ...
w["pdfs/simPdf/SR/samples"].Add(hBkg)   # bin errors → automatic MC-stat ShapeSys

# Signal sample
hSig = XRF.TH1D("sig", "Signal;m_{T2} [GeV]", 5, 200, 700)
hSig.GetXaxis().SetName("mt2")
w["pdfs/simPdf/SR/samples"].Add(hSig)

# Signal-strength NormFactor
w["pdfs/simPdf/SR/samples/sig"].coefs().Multiply("mu_sig", "norm")

# Observed data
hData = XRF.TH1D("obsData", "Data;m_{T2} [GeV]", 5, 200, 700)
# ... fill histogram ...
hData.SetName("obsData")
w["pdfs/simPdf/SR"].datasets().Add(hData)
```

### Adding systematics

```python
# Overall (normalization) systematic — creates a NormFactor + Gaussian constraint
w["pdfs/simPdf/SR/samples/bkg"].coefs().Multiply("mu_bkg", "norm")
w["pdfs/simPdf"].pars()["alpha_JES"].Constrain("normal")  # adds Gaussian constraint

# Histo (shape+norm) systematic via histograms
hJESup = ROOT.TH1D("JES=1", ...)   # name must follow convention: parName=value
hJESdn = ROOT.TH1D("JES=-1", ...)
w["pdfs/simPdf/SR/samples/bkg"].Vary(hJESup)
w["pdfs/simPdf/SR/samples/bkg"].Vary(hJESdn)

# Or set a single bin variation:
w["pdfs/simPdf/SR/samples/bkg"].SetBinContent(3, new_val, "alpha_JES", 1)
```

### Loading an existing workspace

```python
w = XRF.xRooNode("workspace.root")
# or
f = ROOT.TFile("workspace.root")
ws = f.Get("combined")
w = XRF.xRooNode(ws)
```

### Fitting

```python
nll = w["pdfs/simPdf"].nll("obsData")   # construct NLL
fr  = nll.minimize()                    # fit; returns RooFitResult
fr.Draw()                               # post-fit parameter pulls
fr.Draw("CORR10 COLZ TEXT")             # top-10 off-diagonal correlations

# Check convergence (must have status=0, covQual=3 for a valid fit)
print(fr.status(), fr.covQual())

# Asymmetric (MINOS) uncertainties for a specific parameter
nll.pars().find("mu_sig").setAttribute("minos")
fr = nll.minimize()
fr.floatParsFinal().find("mu_sig").getErrorHi()
fr.floatParsFinal().find("mu_sig").getErrorLo()
```

### Fit status and covariance quality

| Code      | Meaning                                                   |
| --------- | --------------------------------------------------------- |
| status=0  | Last algorithm ran successfully (valid fit)               |
| status=1  | Covariance forced positive-definite → try higher Strategy |
| status=2  | Covariance invalid (Hesse strategy 3 only)                |
| status=3  | EDM above threshold → increase Tolerance (max ~10)        |
| status≥4  | Fit cannot be trusted                                     |
| covQual=3 | Positive-definite covariance (required)                   |
| covQual=2 | Forced positive-definite (status=1)                       |
| covQual=1 | Approximation only (status=2)                             |
| covQual=0 | Unavailable (no floating parameters)                      |

Tune fit hyperparameters:

```python
nll = w["pdfs/simPdf"].nll("obsData", [XRF.xRooFit.Tolerance(1),
                                        ROOT.RooFit.Strategy(2)])
# or after construction:
nll.fitConfig().MinimizerOptions().SetTolerance(1)
nll.fitConfig().MinimizerOptions().SetStrategy(2)
```

### Profile likelihood scan

```python
hs = nll.hypoSpace("mu_sig")
hs.scan("plr", 20, 0, 3)   # 20 points between 0 and 3
hs.Draw()
```

### CLs upper limits (asymptotic)

```python
import ROOT as XRF

w   = XRF.xRooNode("workspace.root")
nll = w["pdfs/simPdf"].nll("obsData")
hs  = nll.hypoSpace("mu_sig", XRF.xRooFit.TestStatistic.qmutilde)

hs.scan("cls visualize", 0, 0, 10)   # auto-scan; visualize shows progress
limits = hs.limits()   # dict keyed by "-2","-1","0","1","2","obs"
print(limits)

# Minimal version (POI must be pre-declared in workspace):
print(w.nll("obsData").hypoSpace().limits())
```

Available test statistics: `tmu`, `qmu`, `qmutilde` (default for upper limits),
`q0`, `u0` (for discovery).

### Discovery significance

```python
hs = nll.hypoSpace("mu_sig", XRF.xRooFit.TestStatistic.u0)
hs.scan("pnull", 1, 0, 0)   # single point at mu=0

print("Observed p0:", hs[0].pNull_asymp())
print("Expected p0:", hs[0].pNull_asymp(0))
# convert to significance:
sig = ROOT.Math.gaussian_quantile_c(hs[0].pNull_asymp().value(), 1)
```

### Goodness of fit

```python
nll.mainTermPgof()   # p-value (main term only, recommended for observed data)
nll.pgof()           # p-value including constraint term (use for toys only)
```

### Uncertainty breakdown

```python
totErr  = fr.floatParsFinal().find("mu_sig").getError()
statErr = fr.conditionalError("mu_sig", "alpha_*,gamma_*", up=True, approx=True)
systErr = ROOT.TMath.Sqrt(totErr**2 - statErr**2)
```

## Gotchas

- **Two import styles, one namespace**: Both `import ROOT as XRF` (standalone
  build) and `from ROOT.Experimental import XRooFit as XRF` (bundled) give you
  an `XRF` namespace. The standalone build adds methods directly to `ROOT`; the
  bundled version exposes them under `ROOT.Experimental.XRooFit`.
- **Bin errors trigger MC-stat ShapeSys**: If you add a histogram with non-zero
  bin errors, xRooFit automatically creates a `ShapeSys` for MC statistical
  uncertainties. Suppress this by zeroing out bin errors before adding, or
  control the prefix with `hBkg.SetOption("statPrefix=stat_SR")`.
- **Variation histograms must have zero bin errors**: When calling `Vary()`,
  ensure variation histograms have no bin errors to avoid errors-on-errors.
- **Histogram names encode parameter values**: Variations must be named
  `parName=value`, e.g. `JES=1`, `JES=-1`.
- **Python method forwarding**: In Python, `w["path"].someMethod()` can call
  either `xRooNode.someMethod()` or the underlying RooFit object's method. In
  C++ you must use `w["path"].get<ClassName>()->someMethod()`.
- **All energies in MeV in ATLAS**: When setting axis ranges for observables
  derived from reconstructed physics objects, use MeV not GeV unless explicitly
  converting.
- **Tolerance ≤ 10**: Setting `Tolerance > 10` has been observed to cause
  incorrect parameter uncertainties even with covQual=3.

## Interop

- **StatAnalysis**: Preferred environment; provides ROOT 6.38 + xRooFit + all
  ATLAS stat tools on EL9.
- **TRExFitter**: TRExFitter workspaces are HistFactory/RooStats XML; load with
  `xRooNode("workspace.root")` after running `trex-fitter w`.
- **pyhf**: Convert HistFactory XML to pyhf JSON with `pyhf xml2json`; or use
  pyhf's workspace directly (not xRooFit format).
- **cabinetry**: Reads pyhf JSON workspaces and produces ROOT-style diagnostic
  plots; complementary to xRooFit.
- **xRooBrowser**: Interactive ROOT GUI (`ROOT::Experimental::RooBrowser` in
  ROOT 6.28+) for exploring workspaces.

## Docs

https://xroofit.readthedocs.io/

### Additional Resources

For detailed content beyond this overview, consult the reference files:

- **`references/workspace-building.md`** — Factor types (Const, Norm, Simple,
  Density, Shape, Varied, Overall, Histo), interpolation codes, MC stat
  handling, SetXaxis, log-normal constraints, SetBinData
- **`references/fitting-diagnostics.md`** — Full fit config settings
  (StrategySequence, HesseStrategy), impact/ranking (`fr.impact()`), conditional
  uncertainties (Schur complement), stat/syst/mc-stat breakdown, Shifted GO
  method, conditional fits (`fr.cfit()`)
- **`references/hypothesis-testing.md`** — Test statistic definitions (tmu, qmu,
  qmutilde, q0, u0), full verbose limit-setting example, toy-based limits, limit
  troubleshooting, hypoPoint methods/fits tables, limit-setting checklist
