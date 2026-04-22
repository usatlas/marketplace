---
name: histfitter
description: >-
    Use when setting up or running a HistFitter-based statistical analysis:
    writing a HistFitter configuration Python script, defining channels,
    samples, and systematics, running the workspace generation and fit,
    producing exclusion contours, or migrating a HistFitter analysis to pyhf.
    HistFitter is a ROOT-based framework — prefer pyhf/cabinetry for new
    analyses.
---

# HistFitter

## Overview

HistFitter is a ROOT/RooFit-based framework for HistFactory profile likelihood fits, widely used in ATLAS SUSY and Exotics analyses. Configuration is written as a Python script defining channels (regions), samples, and systematics. For new analyses, prefer pyhf + cabinetry; use HistFitter only when required by your physics group or for legacy analyses.

## When to Use

- Legacy ATLAS analyses already using HistFitter
- Physics group mandates HistFitter output for combination
- Producing exclusion contours in a parameter plane (mass-mass grids)

## Config Script Structure

A HistFitter config is a Python script run by `HistFitter.py`:

```python
from configManager import configMgr
from configWriter import TopLevelXML, ChannelXML, Sample
from ROOT import kBlack, kWhite, kGray

# --- Global settings ---
configMgr.analysisName = "MySearch"
configMgr.outputFileName = f"results/{configMgr.analysisName}"
configMgr.treeName = "nominal"
configMgr.inputLumi = 139.0  # fb-1

# --- Fit configuration ---
myFitConfig = configMgr.addFitConfig("Exclusion_bkg")
myFitConfig.statErrThreshold = 0.05   # Barlow-Beeston threshold

# --- Samples ---
bkg = Sample("ttbar", kGray)
bkg.setNormFactor("mu_ttbar", 1.0, 0.0, 5.0)
bkg.addNtupleFactor("weight_mc * weight_pileup")

sig = Sample("signal", kBlack)
sig.setNormFactor("mu_sig", 1.0, 0.0, 10.0)

data = Sample("Data", kBlack)
data.setData()

# --- Systematics ---
from systematic import Systematic
jes = Systematic("JES", configMgr.weights, 1.0, 1.0, "user", "userOverallSys")
jes.addSample(bkg)

# --- Channels ---
cr = myFitConfig.addChannel("cuts", ["CR_top"], 1, 0.5, 1.5)
cr.addSample(bkg)
cr.addSample(data)

sr = myFitConfig.addChannel("meff", ["SR"], 5, 0, 2000)
sr.addSample(bkg)
sr.addSample(sig)
sr.addSample(data)

myFitConfig.setSignalChannels(["SR"])
myFitConfig.setBkgConstrainChannels(["CR_top"])
```

## Running HistFitter

```bash
# Setup (requires Athena or HistFitter standalone)
source setup.sh

# Step 1: Generate workspace
HistFitter.py -w config.py

# Step 2: Fit (background-only)
HistFitter.py -f config.py

# Step 3: Compute CLs p-values (for each signal point)
HistFitter.py -p config.py

# Step 4: Make plots
HistFitter.py -d config.py

# Step 5: Produce contours (for exclusion in a 2D parameter plane)
HistFitter.py -r config.py
```

## Key Commands Summary

| Flag | Action |
|---|---|
| `-w` | Write workspace (RooWorkspace .root file) |
| `-f` | Fit (profile likelihood minimisation) |
| `-p` | Compute p-values and CLs for each point |
| `-d` | Draw plots (pre/post-fit) |
| `-r` | Produce exclusion contours |
| `-t` | Toys for CLs (slow — use for final results) |

## Systematic Types

| HistFitter type | Equivalent pyhf modifier |
|---|---|
| `userOverallSys` | `normsys` (normalization-only) |
| `userHistoSys` | `histosys` (shape + norm) |
| `normFactor` | `normfactor` (free) |
| `stat` (auto) | `staterror` |

## Migrating to pyhf

HistFitter produces a RooWorkspace (`.root`). To migrate:

```bash
# Export HistFactory XML from the ROOT workspace
python -c "
import ROOT
ws = ROOT.RooStats.HistFactory.MakeModelAndMeasurementFast(...)
"

# Convert XML to pyhf JSON
pyhf xml2json path/to/config.xml > workspace.json
```

Then validate with pyhf and use cabinetry for future modifications.

## Gotchas

- **ROOT version dependency**: HistFitter is tied to specific ROOT versions; use the same Athena release your group uses
- **`statErrThreshold`**: Controls Barlow-Beeston; set too low and you get too many NPs; too high and you lose MC stat information
- **Signal injection**: Signal samples are zeroed in background-only fit by default — check your config uses the correct fit type
- **Contour production**: Requires running over a grid of signal points; each point needs its own `-p` run

## Interop

- **pyhf**: `pyhf xml2json` converts HistFactory XML output to pyhf-compatible JSON
- **TRExFitter**: Can produce HistFactory XML that HistFitter can read
- **Rucio/AMI**: Use `atlas-data-explorer` to find NTuple containers before configuring

## Docs

https://histfitter.docs.cern.ch/ (ATLAS internal — requires CERN SSO)
