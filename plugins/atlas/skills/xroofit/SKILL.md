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

# Declare the observable and add samples from histograms (bin errors trigger
# an automatic MC-stat ShapeSys — see references/workspace-building.md)
hBkg = XRF.TH1D("bkg", "Background;m_{T2} [GeV]", 5, 200, 700)
hBkg.GetXaxis().SetName("mt2")   # observable name
# ... fill histogram ...
w["pdfs/simPdf/SR/samples"].Add(hBkg)

hSig = XRF.TH1D("sig", "Signal;m_{T2} [GeV]", 5, 200, 700)
hSig.GetXaxis().SetName("mt2")
w["pdfs/simPdf/SR/samples"].Add(hSig)
w["pdfs/simPdf/SR/samples/sig"].coefs().Multiply("mu_sig", "norm")  # POI

# Observed data
hData = XRF.TH1D("obsData", "Data;m_{T2} [GeV]", 5, 200, 700)
# ... fill histogram ...
hData.SetName("obsData")
w["pdfs/simPdf/SR"].datasets().Add(hData)
```

### Adding systematics

Overall (normalization) systematics reuse the `coefs().Multiply()` +
`.Constrain()` pattern shown above (see `references/workspace-building.md` for
the Factor-vs-Sys distinction). Shape systematics vary the sample directly:

```python
# Histo (shape+norm) systematic via histograms
hJESup = XRF.TH1D("JES=1", ...)   # name must follow convention: parName=value
hJESdn = XRF.TH1D("JES=-1", ...)
w["pdfs/simPdf/SR/samples/bkg"].Vary(hJESup)
w["pdfs/simPdf/SR/samples/bkg"].Vary(hJESdn)

# Or set a single bin variation:
w["pdfs/simPdf/SR/samples/bkg"].SetBinContent(3, new_val, "alpha_JES", 1)
```

### Loading an existing workspace

```python
w = XRF.xRooNode("workspace.root")
# or
f = XRF.TFile("workspace.root")
ws = f.Get("combined")
w = XRF.xRooNode(ws)
```

### Fitting

```python
nll = w["pdfs/simPdf"].nll("obsData")   # construct NLL
fr  = nll.minimize()                    # fit; returns RooFitResult
fr.Draw()                               # post-fit parameter pulls

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

Inspect the correlation matrix with `fr.Draw("CORR10 COLZ TEXT")` (see
`references/fitting-diagnostics.md`).

### Profile likelihood scan

```python
hs = nll.hypoSpace("mu_sig")
hs.scan("plr", 20, 0, 3)   # 20 points between 0 and 3
hs.Draw()
```

### CLs upper limits (asymptotic)

```python
hs = nll.hypoSpace("mu_sig", XRF.xRooFit.TestStatistic.qmutilde)
hs.scan("cls visualize", 0, 0, 10)   # auto-scan; visualize shows progress
print(hs.limits())   # dict keyed by "-2","-1","0","1","2","obs"
```

See `references/hypothesis-testing.md` for test statistic definitions (`tmu`,
`qmu`, `qmutilde`, `q0`, `u0`), the full verbose limit-setting example, and
discovery significance. Goodness-of-fit (`nll.pgof()`) and uncertainty
breakdowns (`fr.conditionalError()`) are covered in
`references/fitting-diagnostics.md`.

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

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`workspace-building.md`** — Factor types (Const, Norm, Simple, Density,
  Shape, Varied, Overall, Histo), interpolation codes, MC stat handling,
  SetXaxis, log-normal constraints, SetBinData. Read when constructing a
  workspace from scratch, choosing a factor type, or configuring
  interpolation/MC-stat behavior.
- **`fitting-diagnostics.md`** — Full fit config settings (StrategySequence,
  HesseStrategy), impact/ranking (`fr.impact()`), conditional uncertainties
  (Schur complement), stat/syst/mc-stat breakdown, Shifted GO method,
  conditional fits (`fr.cfit()`). Read when tuning fit convergence, ranking
  nuisance parameters, or computing a stat/syst uncertainty breakdown.
- **`hypothesis-testing.md`** — Test statistic definitions (tmu, qmu, qmutilde,
  q0, u0), full verbose limit-setting example, toy-based limits, limit
  troubleshooting, hypoPoint methods/fits tables, limit-setting checklist. Read
  when setting CLs upper limits, computing discovery significance, or debugging
  NaN/failed limits.

## Docs

https://xroofit.readthedocs.io/
