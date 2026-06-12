---
name: histfitter
description: >-
  Use when setting up, running, or debugging a HistFitter statistical analysis:
  writing config scripts, defining channels/samples/systematics, choosing
  systematic types, running workspace generation and fits, producing yields or
  systematics tables, making pull/ranking plots, running hypothesis tests or
  upper limits, producing exclusion contours, debugging failed fits, using the
  built-in pyhf backend, or migrating a HistFitter analysis to pyhf.
---

# HistFitter

## Overview

HistFitter is a ROOT/RooFit-based framework for HistFactory profile likelihood
fits, widely used in ATLAS SUSY and Exotics analyses. The user writes a Python
configuration script defining channels (regions), samples, and systematics.
HistFitter then builds histograms from TTrees or user input, creates a
RooWorkspace via HistFactory, and runs fits, hypothesis tests, and upper limit
scans. For new analyses, prefer pyhf + cabinetry; use HistFitter when required
by your physics group or for legacy analyses.

## When to Use

- Legacy ATLAS analyses already using HistFitter
- Physics groups that mandate HistFactory XML or RooWorkspace output
- Producing exclusion contours over signal grids
- Debugging or extending an existing HistFitter config

## Setup

### Via StatAnalysis (recommended on lxplus)

```bash
setupATLAS
asetup StatAnalysis,0.5.X
mkdir MyProject && cd MyProject
source setup_histfitter.sh -e   # -e copies tutorial examples
```

### From source (cmake build)

```bash
setupATLAS && lsetup git
mkdir HF && cd HF && mkdir build install run
git clone git@github.com:histfitter/histfitter.git
lsetup "views LCG_107a x86_64-el9-gcc13-opt"
cd build
cmake ../histfitter -B. -DCMAKE_INSTALL_PREFIX=../install
make -j4 install
cd ../run
source ../install/bin/setup_histfitter.sh
```

Re-run `source setup_histfitter.sh` from the `run/` folder in every new shell
session; HistFitter uses the current working directory as its work directory.

## Key Concepts

### Fit Types (`-F`)

| Flag      | `myFitType`          | Purpose                                        |
| --------- | -------------------- | ---------------------------------------------- |
| `-F bkg`  | `FitType.Background` | Estimate backgrounds; SR used as VR            |
| `-F excl` | `FitType.Exclusion`  | Set limits on a signal model (CR + SR in fit)  |
| `-F disc` | `FitType.Discovery`  | Model-independent limit (dummy signal, one SR) |

Aliases: `model-dep` = `excl`, `model-indep` = `disc`.

### Region Types

- **Signal region (SR)**: signal-enriched, drives signal extraction.
  `myFitConfig.addSignalChannels([sr])`
- **Control region (CR)**: background-enriched, constrains background params.
  `myFitConfig.addBkgConstrainChannels([cr1, cr2])`
- **Validation region (VR)**: predicted but not fit; validates extrapolation.
  `myFitConfig.addValidationChannels([vr1])`

In a bkg-only fit, use the SR as a validation region. In an exclusion fit, do
not configure validation regions.

### Transfer Factors

The extrapolation from CR to SR uses the ratio `TF = MC(SR) / MC(CR)` for each
background process. Systematic uncertainties partially cancel in this ratio —
this is why "normalized" systematic types (`normHistoSys`,
`overallNormHistoSys`) exist.

## Canonical Patterns

### CLI Workflow

```bash
# Typical three-step sequence (histograms → workspace → fit)
HistFitter.py -t -w -f -F bkg config.py

# Re-run fit only (cuts/weights unchanged since last -t and -w)
HistFitter.py -f -F bkg config.py

# Re-run workspace + fit (norm factor or workspace config changed, but histograms unchanged)
HistFitter.py -w -f -F bkg config.py

# Exclusion: build workspace then run CLs hypothesis test separately
HistFitter.py -t -w -F excl config.py
HistFitter.py -p -F excl config.py

# Discovery: build workspace then run p₀ significance separately
HistFitter.py -t -w -F disc config.py
HistFitter.py -z -F disc config.py

# Produce post-fit plots and tables
HistFitter.py -d -F bkg config.py
```

### Exclusion fit config

```python
from configManager import configMgr
from configWriter import fitConfig, Measurement, Channel, Sample
from systematic import Systematic
from ROOT import kBlack, kGreen, kAzure, kPink

# --- Global settings ---
configMgr.analysisName = "MySearch"
configMgr.inputLumi  = 0.001    # lumi of input TTrees (fb⁻¹)
configMgr.outputLumi = 139.0    # target lumi for output histograms
configMgr.setLumiUnits("fb-1")
configMgr.calculatorType = 2    # 0=frequentist, 2=asymptotic
configMgr.testStatType   = 3    # one-sided profile likelihood (LHC default)
configMgr.nPoints = 20          # scan points for upper limit

# --- Cuts and weights ---
configMgr.cutsDict["CR"] = "nJet>=4 && met>200"
configMgr.cutsDict["SR"] = "nJet>=4 && met>400"
configMgr.weights = ("genWeight", "eventWeight", "leptonWeight")
configMgr.nomName = "_NoSys"    # suffix of nominal TTree name

# --- Input files ---
bgdFiles = []
if configMgr.readFromTree:
    bgdFiles.append("samples/bkg.root")
else:
    bgdFiles = [configMgr.histCacheFile]

# --- Systematics ---
jes = Systematic("JES", "_NoSys", "_JESup", "_JESdown",
                 "tree", "histoSys")
highWeights = configMgr.weights + ("ktScaleUp",)
lowWeights  = configMgr.weights + ("ktScaleDown",)
ktScale = Systematic("KtScale", configMgr.weights,
                     highWeights, lowWeights,
                     "weight", "overallNormHistoSys")

# --- Samples ---
topSample = Sample("Top", kGreen-9)
topSample.setStatConfig(True)
topSample.setNormFactor("mu_Top", 1., 0., 5.)
topSample.setNormRegions([("CR", "nJet")])
topSample.addInputs(bgdFiles)

dataSample = Sample("Data", kBlack)
dataSample.setData()
dataSample.addInputs(["samples/data.root"])

# --- Fit configuration ---
if myFitType == FitType.Exclusion:
    excl = configMgr.addFitConfig("Exclusion")
    meas = excl.addMeasurement(name="NormalMeasurement",
                               lumi=1.0, lumiErr=0.039)
    meas.addPOI("mu_SIG")
    excl.addSamples([topSample, dataSample])
    excl.addSystematic(jes)
    excl.getSample("Top").addSystematic(ktScale)

    cr = excl.addChannel("nJet", ["CR"], 2, 4, 6)
    sr = excl.addChannel("met", ["SR"], 5, 400, 900)
    excl.addBkgConstrainChannels([cr])
    excl.addSignalChannels([sr])

    sigSample = Sample("Signal", kPink)
    sigSample.setNormFactor("mu_SIG", 1., 0., 10.)
    sigSample.setNormByTheory()
    sigSample.setStatConfig(True)
    sigSample.addInputs(["samples/signal.root"])
    excl.addSamples(sigSample)
    excl.setSignalSample(sigSample)
```

### User-input histograms (no TTrees)

For counting experiments without input trees:

```python
bkg = Sample("Bkg", kGreen-9)
bkg.buildHisto([5.0], "SR", "cuts", 0.5)
bkg.buildStatErrors([1.0], "SR", "cuts")
bkg.addSystematic(Systematic("ucb", configMgr.weights,
                             1.2, 0.8, "user", "userOverallSys"))
```

`buildHisto([values], region, variable, binLow, binWidth)` creates histograms
directly from numbers. Use `"cuts"` as the variable for a single-bin channel
with `addChannel("cuts", ["SR"], 1, 0.5, 1.5)`.

## CLI Reference

```bash
HistFitter.py [options] configFile.py
```

| Flag             | Action                                          |
| ---------------- | ----------------------------------------------- |
| `-t`             | Build histograms from TTrees                    |
| `-w`             | Create RooWorkspace from histograms             |
| `-f`             | Fit the workspace                               |
| `-p`             | Run exclusion hypothesis test (CLs)             |
| `-z`             | Run discovery hypothesis test (p₀)              |
| `-l`             | Upper limit scan                                |
| `-d`             | Draw before/after plots                         |
| `-D <plots>`     | Specific plots: before, after, corrMatrix,      |
|                  | separateComponents, likelihood, systematics,    |
|                  | plotInterpolation                               |
| `-F <type>`      | Fit type: bkg, excl, disc                       |
| `-x`             | Write XML then call hist2workspace              |
| `-j`             | Write JSON workspace from XML output            |
| `-i`             | Stay in interactive Python after running        |
| `-a`             | Use Asimov dataset                              |
| `-m <params>`    | Run MINOS (asymmetric errors); use ALL for all  |
| `-C <p1:v1,...>` | Fix parameters to constant values               |
| `-g <points>`    | Signal grid points (comma-separated)            |
| `-r <regions>`   | Signal regions to process (comma-separated)     |
| `-R`             | Rebin non-equidistant histograms to proxy bins  |
| `-V`             | Include validation regions                      |
| `-u <arg>`       | Arbitrary user argument (accessible in config)  |
| `--pyhf`         | Use pyhf backend where possible                 |
| `--pyhf-backend` | Backend: numpy, tensorflow, pytorch, jax        |
| `-L <level>`     | Log level: VERBOSE, DEBUG, INFO, WARNING, ERROR |

Typical workflow: `-t -w -f` (histos → workspace → fit). After first run, skip
`-t` if cuts/weights are unchanged: `-w -f` or just `-f`.

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`systematic-types.md`** — Complete method reference table, decision
  flowchart for choosing a type, how normalized systematics work internally,
  one-sided/envelope variants, pruning mechanics, constraint terms. Read when
  the user asks which systematic type to use or is debugging unexpected
  normalization behavior.
- **`config-api.md`** — Full configMgr properties, fitConfig/Channel/Sample/
  Measurement methods, object hierarchy, weight/systematic propagation rules,
  input file management. Read when constructing a config script or looking up a
  specific API method.
- **`helper-scripts.md`** — Detailed CLI options and Python API for
  YieldsTable.py, SysTable.py, SystRankingPlot.py, UpperLimitTable.py, plus
  other utility scripts and workspace file naming conventions. Read when
  producing publication tables or plots from a fitted workspace.

## Systematic Types

### Constructor

```python
syst = Systematic(name, nominal, high, low, type, method)
```

- **type**: `"tree"` (different TTrees), `"weight"` (different weight branches),
  `"user"` (numeric values)
- **method**: controls how the variation enters the likelihood

### Method Reference

| Method                            | Effect                                        |
| --------------------------------- | --------------------------------------------- |
| `overallSys`                      | Scale normalization only (no shape)           |
| `histoSys`                        | Correlated shape + normalization              |
| `normHistoSys`                    | Shape only (normalized to nominal integral)   |
| `overallHistoSys`                 | Factorized: overallSys + shape-only histoSys  |
| `overallNormHistoSys`             | overallSys + normHistoSys (uses norm regions) |
| `shapeSys`                        | Bin-by-bin uncorrelated (sum of samples)      |
| `shapeStat`                       | Bin-by-bin uncorrelated (single sample)       |
| `userOverallSys`                  | User-defined numeric overall scale            |
| `userHistoSys`                    | User-defined numeric shape + norm             |
| `normHistoSysOneSide[Sym]`        | One-sided [symmetrized] normHistoSys          |
| `overallNormHistoSysOneSide[Sym]` | One-sided [symmetrized] overallNormHistoSys   |
| `histoSysEnvelopeSym`             | Envelope from vector of variations            |

### Choosing a Type

- Pure normalization uncertainty → `overallSys` or `userOverallSys`
- Shape + normalization → `histoSys`
- Shape only (using transfer factor approach) → `normHistoSys`
- Transfer factor with factorized norm → `overallNormHistoSys` (most common for
  backgrounds with norm factors and norm regions)
- MC statistical uncertainty → `shapeStat` per sample

"Norm" types require `sample.setNormRegions([(region, variable), ...])` to
define which CRs to normalize against. Only use on samples that carry a
normalization factor `mu_...`; otherwise the normalization uncertainty is lost.

## Helper Scripts

### Yields table

```bash
YieldsTable.py -s Top,WZ,BG -c CR_nJet,SR_cuts \
  -w results/MyAnalysis/BkgOnly_combined_NormalMeasurement_model_afterFit.root \
  -o yields.tex
```

Options: `-b` (show before-fit), `-S` (show sum), `-B` (blind SR), `-P` (per-bin
yields).

### Systematics breakdown table

```bash
SysTable.py -c SR_cuts \
  -w results/MyAnalysis/BkgOnly_combined_NormalMeasurement_model_afterFit.root \
  -o systable.tex
```

Options: `-s <sample>` (per-sample), `-%` (show percentages), `-m 2` (method 2:
refit with parameter fixed), `-z` (shade systematic based on size).

### Systematics ranking plot

```bash
SystRankingPlot.py \
  -w results/MyAnalysis/Exclusion_combined_NormalMeasurement_model_afterFit.root \
  -f CR,SR -p mu_SIG --max-np 20 -o plots/
```

Shows pre/post-fit impact of each nuisance parameter on the POI.

### Upper limit table

```bash
UpperLimitTable.py -c SR_cuts \
  -w results/MyAnalysis/Discovery_combined_NormalMeasurement_model_afterFit.root \
  -l 139.0 -p mu_Discovery -o upperlimit.tex
```

Produces a table of observed/expected upper limits on visible cross-section,
signal events, and signal strength from a model-independent (discovery) fit.

### Pull / summary plot

Run `YieldsTable.py` first (produces a `.pickle` file), then use
`pullPlotUtils.makePullPlot()` from `python/pullPlotUtils.py`.

## Advanced Features

### Blinding

```python
configMgr.blindSR = True   # replace SR data with total bkg estimate
configMgr.blindCR = False
configMgr.blindVR = False
configMgr.useSignalInBlindedData = False  # True adds signal MC to blind data
```

Per-channel blinding: `myChannel.blind = True`.

### MINOS (asymmetric errors)

```bash
HistFitter.py -f -m "alpha_JES,mu_Top" config.py   # specific params
HistFitter.py -f -m ALL config.py                   # all params
```

Use MINOS when profile likelihood is non-parabolic (check with `-D likelihood`).
Errors < 1 on alpha parameters indicate the fit is constraining ("profiling")
that systematic.

### Pruning

```python
configMgr.prun = True
configMgr.prunThreshold = 0.05   # 5% relative to nominal
configMgr.prunMethod = 2         # 1=chi2 test, 2=bin-by-bin check
```

Removes small systematics to speed up fits. Validate that total uncertainty is
unchanged. Pruning plots are saved to `plots/`.

### Histogram recycling

```python
configMgr.useCacheToTreeFallback = True
configMgr.useHistBackupCacheFile = True
configMgr.histBackupCacheFile = "data/MyAnalysis_template.root"
```

Reuses previously built histograms; only rebuilds missing ones (e.g., new signal
points). Run with `-w` (not `-t`) to activate the fallback.

### Fixing parameters in a fit

```bash
HistFitter.py -f -C "mu_Sig:0." config.py   # bkg-only equivalent
HistFitter.py -f -C "mu_Sig:1." config.py   # S+B with mu=1
```

Useful for reproducing individual fits from `-p` for debugging.

### Non-equidistant bins

Use `-R` to remap non-uniform bins to proxy equidistant bins `[0, 1, ..., N]`
before the fit, then unfold post-fit. Output ROOT files contain the unfolded
histograms; PDF/EPS plots use the proxy bins.

### Discovery fit setup

```python
if myFitType == FitType.Discovery:
    disc = configMgr.addFitConfig("Discovery")
    # ... add CRs and samples ...
    srBin = disc.addChannel("cuts", ["SR"], 1, 0.5, 1.5)
    srBin.addDiscoverySamples(["Discovery"], [1.], [0.], [10000.], [kMagenta])
    disc.addSignalChannels([srBin])
```

The dummy signal has expectation = 1 event, no systematics. Run with
`-F disc -z` for the discovery hypothesis test. Only one SR is allowed.

## pyhf Integration

HistFitter v1.3+ supports pyhf as a backend:

```bash
# Use pyhf for hypothesis tests
HistFitter.py -p --pyhf config.py

# Specify backend
HistFitter.py -p --pyhf --pyhf-backend jax config.py

# Export workspace to JSON (via XML intermediate)
HistFitter.py -w -x -j config.py
```

The `-j` flag writes a pyhf-compatible JSON workspace from the XML output.

### Standalone pyhf conversion

```bash
# From HistFactory XML to pyhf JSON
pyhf xml2json config/MyAnalysis/TopLevelXML.xml --basedir results/ \
  -o workspace.json

# Validate
pyhf cls workspace.json
```

## Troubleshooting

| Problem                         | Cause / Fix                                                                |
| ------------------------------- | -------------------------------------------------------------------------- |
| Upper limit scan returns 0s     | Scan range too wide; set `configMgr.scanRange = (0., 1.)`                  |
| `All fits seem to have failed`  | Check log for which fit failed; reproduce with `-f -C "mu_Sig:<val>"`      |
| Negative yields after fit       | Over-aggressive systematic; check with `-D systematics`                    |
| MINOS errors < 1 on alpha param | Fit is constraining ("profiling") that syst; expected if CR has high stats |
| Pruning removes too much        | Lower `prunThreshold`; validate total uncertainty unchanged                |
| `Cannot open workspace`         | Wrong path; check `results/` directory structure                           |
| Histograms not found in cache   | Run with `-t` to rebuild, or check `histBackupCacheFile` path              |
| Slow histogram building         | Use parallelization (split samples with `-u`), or histogram recycling      |

## Gotchas

- **ROOT version**: HistFitter is tied to specific ROOT versions; use the LCG
  view or StatAnalysis release your group uses
- **`statErrThreshold`**: Controls Barlow-Beeston; too low = too many NPs, too
  high = loses MC stat info. Default is 0 (off); `setStatConfig(True)` per
  sample is the modern approach
- **Signal in bkg-only fit**: Signal samples are ignored in `-F bkg`; to see the
  SR, use it as a validation channel
- **Norm regions required**: `overallNormHistoSys` and `normHistoSys` require
  `sample.setNormRegions(...)` and a norm factor on the sample
- **Contour production**: Each signal point needs its own `-p` run; use `-g` to
  select points
- **`readFromTree` flag**: Set automatically when `-t` is used; controls whether
  `configMgr.readFromTree` is True in the config
- **Re-run `-t`**: Required whenever cuts, weights, or systematics change; skip
  only when reusing existing histograms
- **Workspace naming**: Results are in
  `results/<analysisName>/<FitType>_combined_<MeasName>_model_afterFit.root`

## Interop

- **pyhf**: `pyhf xml2json` converts XML output; `--pyhf` flag for in-process
  use; `-j` exports JSON workspace
- **cabinetry**: reads pyhf JSON workspaces produced by HistFitter
- **TRExFitter**: can produce HistFactory XML that HistFitter can read
- **StatAnalysis**: bundles HistFitter with other ATLAS stat tools on cvmfs
- **Rucio/AMI**: use to find NTuple containers before configuring input files

## Tutorial Examples

The HistFitter repository ships with tutorial configs in `analysis/tutorial/`:

- `MyUserAnalysis.py` — minimal counting experiment with user-defined yields
- `MyOneBinExample.py` — one-bin from TTrees with exclusion/discovery setup
- `MyShapeFitExample.py` — binned shape fit (6 bins, one channel)
- `MyConfigExample.py` — multi-channel simultaneous fit with CRs/VRs
- `MySimpleChannelConfig.py` — signal grid scan and contour production
- `MyABCDExample.py` — QCD background estimation via ABCD method

These are good starting points; copy and adapt for your analysis.

## Docs

- Source: <https://github.com/histfitter/histfitter>
- Main TWiki:
  <https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/SusyFitter>
- Tutorial:
  <https://twiki.cern.ch/twiki/bin/view/AtlasProtected/HistFitterTutorial>
- Advanced tutorial:
  <https://twiki.cern.ch/twiki/bin/view/AtlasProtected/HistFitterAdvancedTutorial>
- Paper: <https://doi.org/10.1140/epjc/s10052-015-3327-7>
- HistFactory manual:
  <https://cds.cern.ch/record/1456844/files/CERN-OPEN-2012-016.pdf>
