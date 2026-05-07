---
name: cabinetry
description: >-
  Use when building an ATLAS statistical analysis with cabinetry: writing a
  cabinetry config file, building histogram templates from ROOT NTuples,
  constructing a pyhf workspace, running a profile likelihood fit, visualising
  pre/post-fit data-MC comparisons, producing pull plots and NP rankings, or
  computing CLs exclusion limits or discovery significance via cabinetry's
  high-level API.
---

# cabinetry

## Overview

cabinetry is a high-level Python library that sits above pyhf and automates the
workflow from ROOT NTuples → histogram templates → pyhf workspace → fit results
→ plots. It is driven by a YAML/JSON config file and is the recommended
end-to-end framework for new ATLAS analyses using the Python stack.

## When to Use

- Building a complete analysis fit chain from NTuples to results
- Producing standard ATLAS fit diagnostic plots (pulls, rankings, data/MC)
- Automating template building across many samples and regions
- Wrapping pyhf with a config-driven interface that non-experts can use

## Key Concepts

```text
NTuples (ROOT) → cabinetry templates → pyhf workspace → fit → plots
```

1. Write a config file (YAML or Python dict)
2. `cabinetry.templates.build(config)` — fills histograms from NTuples
3. `cabinetry.templates.postprocess(config)` — applies smoothing /
   symmetrization
4. `cabinetry.workspace.build(config)` — creates HistFactory JSON
5. `cabinetry.fit.fit(model, data)` — profile likelihood fit
6. `cabinetry.visualize.*` — plots

### Config Structure

`General`, `Regions`, `Samples`, and `NormFactors` are all required top-level
blocks. `Systematics` is optional. NormFactors live in their own block — they
are **not** nested inside Samples.

```yaml
General:
  Measurement: "my_analysis"
  HistogramFolder: "histograms/"
  InputPath: "ntuples/{SamplePath}"
  POI: "mu_sig"

Regions:
  - Name: "SR"
    Filter: "n_bjets >= 2 and met > 200e3"
    Variable: "meff"
    Binning: [0, 500e3, 700e3, 1000e3, 1500e3, 2000e3]
  - Name: "CR_top"
    Filter: "n_bjets >= 2 and met < 150e3"
    Variable: "meff"
    Binning: [0, 500e3, 1000e3, 2000e3]

Samples:
  - Name: "Data"
    Tree: "nominal"
    SamplePath: "data/*.root"
    Data: true
  - Name: "Signal"
    Tree: "nominal"
    SamplePath: "signal/signal.root"
  - Name: "ttbar"
    Tree: "nominal"
    SamplePath: "ttbar/ttbar.root"
    Weight: "weight"

NormFactors:
  - Name: "mu_sig"
    Samples: "Signal"
    Nominal: 1
    Bounds: [0, 10]

Systematics:
  - Name: "JES"
    Up:
      SamplePath: "ttbar/ttbar_JES_up.root"
    Down:
      SamplePath: "ttbar/ttbar_JES_dn.root"
    Type: NormPlusShape
    Samples: "ttbar"
  - Name: "Lumi"
    Up:
      Normalization: 0.015
    Down:
      Normalization: -0.015
    Type: Normalization
```

## Canonical Patterns

**Full workflow**:

```python
import cabinetry

cabinetry.set_logging()  # optional: verbose logging

config = cabinetry.configuration.load("config.yaml")
cabinetry.configuration.print_overview(config)

# Build and post-process histogram templates from NTuples
cabinetry.templates.build(config)
cabinetry.templates.postprocess(config)

# Construct pyhf workspace
workspace = cabinetry.workspace.build(config)
cabinetry.workspace.save(workspace, "workspace.json")

# Reload workspace, build model and fit
ws = cabinetry.workspace.load("workspace.json")
model, data = cabinetry.model_utils.model_and_data(ws)
fit_results = cabinetry.fit.fit(model, data)
```

**Visualisation**:

```python
# Get pre- and post-fit model predictions
prediction_prefit = cabinetry.model_utils.prediction(model)
prediction_postfit = cabinetry.model_utils.prediction(model, fit_results=fit_results)

# Pre-fit and post-fit data/MC comparison plots
cabinetry.visualize.data_mc(prediction_prefit, data, config=config)
cabinetry.visualize.data_mc(prediction_postfit, data, config=config)

# Yield table (post-fit)
cabinetry.tabulate.yields(prediction_postfit, data)

# NP pulls and correlation matrix
cabinetry.visualize.pulls(fit_results, figure_folder="figures/")
cabinetry.visualize.correlation_matrix(fit_results, figure_folder="figures/")

# NP ranking (impact on POI)
ranking_results = cabinetry.fit.ranking(model, data, fit_results=fit_results)
cabinetry.visualize.ranking(ranking_results, figure_folder="figures/")
```

**Likelihood scan**:

```python
scan_results = cabinetry.fit.scan(model, data, "mu_sig")
cabinetry.visualize.scan(scan_results, figure_folder="figures/")
```

**CLs upper limit**:

```python
limit_results = cabinetry.fit.limit(model, data)
print(f"Observed limit: {limit_results.observed_limit:.2f}")
# expected_limit is a 5-element array: [-2s, -1s, median, +1s, +2s]
print(f"Expected limit: {limit_results.expected_limit[2]:.2f}")

cabinetry.visualize.limit(limit_results, figure_folder="figures/")
```

**Discovery significance**:

```python
sig_results = cabinetry.fit.significance(model, data)
print(f"Observed significance: {sig_results.observed_significance:.2f} sigma")
print(f"Expected significance: {sig_results.expected_significance:.2f} sigma")
```

**Load a pre-built workspace directly** (skip template building):

```python
import json, pyhf
with open("workspace.json") as f:
    ws = pyhf.Workspace(json.load(f))
model, data = cabinetry.model_utils.model_and_data(ws)
fit_results = cabinetry.fit.fit(model, data)
```

### Config Tips

- `NormFactors` is a top-level config block — each entry has `Name`, `Samples`,
  `Nominal`, and optionally `Bounds`. Use for signal μ and CR-driven
  backgrounds.
- `Type: NormPlusShape` creates separate norm and shape modifiers — correct for
  most experimental systematics
- `Type: Normalization` uses `Up.Normalization` / `Down.Normalization` (a
  fractional value, e.g. `0.015` for 1.5%) — for luminosity and cross-section
  uncertainties
- `Down: {Symmetrize: true}` mirrors the Up variation, useful when only one
  variation is available
- Stat errors (Barlow-Beeston) are included automatically; use
  `DisableStaterror: true` on a sample to suppress them

## Gotchas

- **ROOT file variable names**: cabinetry reads branches by name; branch names
  must match what you put in `Variable` and `Filter`
- **Units in cuts**: NTuples in MeV → write cuts in MeV (`met > 200e3`, not
  `> 200`)
- **Missing NTuple files**: cabinetry raises at template-build time — check
  `SamplePath` glob patterns
- **Pre-existing histograms**: If `HistogramFolder` has old files, `build()`
  will use them. Delete the folder to force a rebuild.
- **`postprocess()` is required**: skipping it means smoothing and
  symmetrization from the config are never applied before workspace construction
- **`data_mc` takes a ModelPrediction, not a config**: call
  `cabinetry.model_utils.prediction(model)` first, then pass it as the first
  argument along with `data`

## Interop

- **pyhf**: cabinetry workspaces are valid pyhf JSON — use pyhf directly for
  advanced patching or combination
- **hist**: cabinetry can also accept pre-built `Hist` objects instead of
  NTuples via custom template providers
- **pyhs3**: save cabinetry workspaces with pyhs3 for schema-compliant archiving

## Docs

https://cabinetry.readthedocs.io/en/latest/
