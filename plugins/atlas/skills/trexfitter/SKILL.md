---
name: trexfitter
description: >-
  Use when setting up or running a TRExFitter statistical analysis: writing a
  TRExFitter config file, defining regions, samples, systematics, and
  NormFactors, running workspace generation (n), fitting (f), drawing plots (d),
  or computing limits (l). TRExFitter is the most common ROOT-based ATLAS fit
  framework for top and other analyses.
---

# TRExFitter

## Overview

TRExFitter is a ROOT/RooFit-based HistFactory fitting framework widely used in
ATLAS top, Higgs, and SM analyses. It reads a plain-text configuration file,
produces HistFactory workspaces from ROOT histograms or NTuples, runs fits, and
generates standard ATLAS diagnostic plots. It is the de facto standard for ATLAS
publications that use a ROOT-based fit.

## When to Use

- Physics group mandates TRExFitter for the analysis
- Producing standard ATLAS publication-quality fit plots (pre/post-fit, pulls,
  rankings, limits)
- TOP, SM, or Higgs analyses following group conventions
- When you need HistFactory XML/ROOT output (e.g., for combination with other
  analyses)

## Key Concepts

### Histogram Input Convention

When `ReadFrom: HIST`, TRExFitter looks for:

```text
{HistoPath}/{Sample}_{Region}.root
```

Each ROOT file contains the `HistoName` histogram for nominal and each
systematic variation:

```text
histograms/ttbar_SR.root          → h_meff (nominal)
histograms/ttbar_JES_up_SR.root   → h_meff (JES up variation)
```

### Systematic Types

| TRExFitter Type | Effect                                            |
| --------------- | ------------------------------------------------- |
| `OVERALL`       | Normalization-only, log-normal prior              |
| `HISTO`         | Shape+norm from ±1σ histogram templates           |
| `SHAPE`         | Shape-only (no normalization change)              |
| `STAT`          | MC statistical uncertainty (auto, Barlow-Beeston) |

### Key Config Parameters

| Parameter        | Values                 | Notes                                |
| ---------------- | ---------------------- | ------------------------------------ |
| `FitType`        | `SPLUSB`, `BONLY`      | SPLUSB for exclusion/measurement     |
| `FitRegion`      | `CRSR`, `CRONLY`       | CR-only fit for background estimate  |
| `ReadFrom`       | `HIST`, `NTUP`         | HIST reads pre-made ROOT histograms  |
| `POIAsimov`      | `0`, `1`               | Asimov μ for expected limits         |
| `StatOnly`       | `TRUE`/`FALSE`         | Stat-only fit for cross-checks       |
| `Symmetrisation` | `TWOSIDED`, `ONESIDED` | How to handle asymmetric systematics |

## Canonical Patterns

### Config File Structure

TRExFitter config is a plain text file with key-value blocks:

```config
% ===============================
% Job settings
% ===============================
Job: "MyAnalysis"
  CmeLabel: "13 TeV"
  POI: "mu_sig"
  ReadFrom: HIST
  HistoPath: "histograms"
  OutputDir: "output/MyAnalysis"
  LumiLabel: "139 fb^{-1}"
  Lumi: 139.0

% ===============================
% Fit configuration
% ===============================
Fit: "MyFit"
  FitType: SPLUSB
  FitRegion: CRSR
  POIAsimov: 1

% ===============================
% Regions
% ===============================
Region: "SR"
  Type: SIGNAL
  Label: "Signal Region"
  HistoName: "meff"
  ShortLabel: "SR"

Region: "CR_top"
  Type: CONTROL
  Label: "Top CR"
  HistoName: "meff"

% ===============================
% Samples
% ===============================
Sample: "Signal"
  Type: SIGNAL
  HistoFile: "signal"
  FillColor: 632

Sample: "ttbar"
  Type: BACKGROUND
  HistoFile: "ttbar"
  FillColor: 4

Sample: "Data"
  Type: DATA
  HistoFile: "data"

% ===============================
% Systematics
% ===============================
Systematic: "JES"
  Title: "Jet Energy Scale"
  Type: HISTO
  HistoNameUp: "JES_up"
  HistoNameDown: "JES_dn"
  Samples: ttbar, Signal
  Symmetrisation: TWOSIDED

Systematic: "Lumi"
  Title: "Luminosity"
  Type: OVERALL
  OverallUp: 0.015
  OverallDown: -0.015
  Samples: ttbar, Signal

NormFactor: "mu_ttbar"
  Title: "#mu_{t#bar{t}}"
  Nominal: 1
  Min: 0
  Max: 5
  Samples: ttbar
```

### Running TRExFitter

```bash
# Step n: Normalise histograms and prepare inputs
trex-fitter n config.config

# Step w: Write workspace (RooWorkspace)
trex-fitter w config.config

# Step f: Fit
trex-fitter f config.config

# Step d: Draw plots (pre/post-fit, data/MC)
trex-fitter d config.config

# Step p: Draw NP pulls
trex-fitter p config.config

# Step r: Draw NP rankings
trex-fitter r config.config

# Step l: Compute limits
trex-fitter l config.config

# Chain multiple steps
trex-fitter nwfdprl config.config
```

### Exporting to pyhf

TRExFitter can produce HistFactory XML for conversion:

```bash
trex-fitter w config.config       # produces XML in output dir
pyhf xml2json output/MyAnalysis/config.xml > workspace.json
```

## Gotchas

- **Case sensitivity in config**: Region names, sample names, and systematic
  names must match exactly between definitions and references
- **`%` is a comment**: In TRExFitter config files, `%` starts a comment (not
  `#`)
- **Histogram paths**: TRExFitter looks for `{HistoFile}_{Region}` — naming must
  be consistent
- **`CRONLY` fit**: Use for validating CR modelling; switch to `CRSR` for the
  final result
- **Symmetrisation**: `ONESIDED` mirrors the up variation; only use if
  physically motivated

## Interop

- **HistFitter**: Workspaces are interchangeable at the HistFactory XML level
- **pyhf**: `pyhf xml2json` converts TRExFitter XML output to pyhf JSON
- **hist**: Produce histogram templates with hist/awkward, save to ROOT with
  uproot, feed to TRExFitter

## Docs

https://trexfitter-docs.web.cern.ch/ (requires CERN SSO for ATLAS-internal
version) Public: https://gitlab.cern.ch/TRExStats/TRExFitter
