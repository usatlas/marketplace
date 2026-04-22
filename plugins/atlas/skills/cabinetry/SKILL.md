---
name: cabinetry
description: >-
    Use when building an ATLAS statistical analysis with cabinetry: writing
    a cabinetry config file, building histogram templates from ROOT NTuples,
    constructing a pyhf workspace, running a profile likelihood fit,
    visualising pre/post-fit data-MC comparisons, producing pull plots and
    NP rankings, or computing CLs exclusion limits via cabinetry's high-level
    API.
---

# cabinetry

## Overview

cabinetry is a high-level Python library that sits above pyhf and automates the workflow from ROOT NTuples → histogram templates → pyhf workspace → fit results → plots. It is driven by a YAML/JSON config file and is the recommended end-to-end framework for new ATLAS analyses using the Python stack.

## When to Use

- Building a complete analysis fit chain from NTuples to results
- Producing standard ATLAS fit diagnostic plots (pulls, rankings, data/MC)
- Automating template building across many samples and regions
- Wrapping pyhf with a config-driven interface that non-experts can use

## Workflow

```
NTuples (ROOT) → cabinetry templates → pyhf workspace → fit → plots
```

1. Write a config file (YAML or Python dict)
2. `cabinetry.templates.build(config)` — fills histograms from NTuples
3. `cabinetry.workspace.build(config)` — creates HistFactory JSON
4. `cabinetry.fit.fit(model, data)` — profile likelihood fit
5. `cabinetry.visualize.*` — plots

## Config Structure

```yaml
General:
  HistogramFolder: "histograms/"
  InputPath: "ntuples/{SamplePath}"
  
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
    Data: true
    SamplePath: "data/*.root"
  - Name: "Signal"
    SamplePath: "signal/signal.root"
    NormFactor: "mu_sig"
  - Name: "ttbar"
    SamplePath: "ttbar/ttbar.root"

Systematics:
  - Name: "JES"
    Up:
      SamplePath: "ttbar/ttbar_JES_up.root"
    Down:
      SamplePath: "ttbar/ttbar_JES_dn.root"
    Type: NormPlusShape
    Samples: "ttbar"
  - Name: "Lumi"
    Value: 0.015
    Type: Normalization
    Samples: ["Signal", "ttbar"]
```

## Canonical Patterns

**Full workflow**:
```python
import cabinetry

config = cabinetry.configuration.load("config.yaml")
cabinetry.configuration.print_overview(config)

# Build histogram templates from NTuples
cabinetry.templates.build(config)

# Construct pyhf workspace
workspace = cabinetry.workspace.build(config)
cabinetry.workspace.save(workspace, "workspace.json")

# Build model and fit
model, data = cabinetry.model_utils.model_and_data(workspace)
fit_results = cabinetry.fit.fit(model, data)
```

**Visualisation**:
```python
# Pre-fit data/MC
cabinetry.visualize.data_mc(config, figure_folder="figures/prefit/")

# Post-fit data/MC
cabinetry.visualize.data_mc(config, figure_folder="figures/postfit/", fit_results=fit_results)

# NP pulls
cabinetry.visualize.pulls(fit_results, figure_folder="figures/")

# NP ranking (impact on POI)
ranking_results = cabinetry.fit.ranking(model, data, fit_results=fit_results)
cabinetry.visualize.ranking(ranking_results, figure_folder="figures/")
```

**CLs upper limit**:
```python
limit_results = cabinetry.fit.limit(model, data)
print(f"Observed limit: {limit_results.observed_limit:.2f}")
print(f"Expected limit: {limit_results.expected_limit[2]:.2f}")  # median
```

**Load a pre-built workspace directly** (skip template building):
```python
import json, pyhf
with open("workspace.json") as f:
    ws = pyhf.Workspace(json.load(f))
model, data = cabinetry.model_utils.model_and_data(ws)
fit_results = cabinetry.fit.fit(model, data)
```

## Config Tips

- `NormFactor` on a sample inserts a free `normfactor` modifier — use for signal μ and CR-driven backgrounds
- `Type: NormPlusShape` creates separate norm and shape modifiers — correct for most experimental systematics
- `Type: Normalization` (with `Value`) creates a `normsys` modifier — for luminosity and cross-section uncertainties
- Samples not listed under a Systematic get that systematic applied with zero effect — fine for backgrounds with no uncertainty
- `AddStatError: true` (global option) adds Barlow-Beeston staterror to all bins

## Gotchas

- **ROOT file variable names**: cabinetry reads branches by name; branch names must match what you put in `Variable` and `Filter`
- **Units in cuts**: NTuples in MeV → write cuts in MeV (`met > 200e3`, not `> 200`)
- **Missing NTuple files**: cabinetry raises at template-build time — check `SamplePath` glob patterns
- **Pre-existing histograms**: If `HistogramFolder` has old files, `build()` will use them. Delete the folder to force a rebuild.
- **Symmetric systematics**: If only `Up` is specified, cabinetry mirrors it for `Down` automatically

## Interop

- **pyhf**: cabinetry workspaces are valid pyhf JSON — use pyhf directly for advanced patching or combination
- **hist**: cabinetry can also accept pre-built `Hist` objects instead of NTuples via custom template providers
- **pyhs3**: save cabinetry workspaces with pyhs3 for schema-compliant archiving

## Docs

https://cabinetry.readthedocs.io/en/latest/
