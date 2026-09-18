---
name: trexfitter
description: >-
  Use when setting up or running a TRExFitter statistical analysis: writing a
  TRExFitter config file, defining regions, samples, systematics, and
  NormFactors, running actions (n/h/w/f/d/p/r/l/s), computing limits or
  significance, diagnosing fit convergence failures, NP pulls or constraints, or
  exporting workspaces to pyhf.
---

# TRExFitter

## Overview

TRExFitter is a ROOT/RooFit-based HistFactory fitting framework used across
ATLAS for profile likelihood fits. It reads a plain-text configuration file,
builds HistFactory workspaces from ROOT histograms or NTuples, runs fits, and
produces standard ATLAS diagnostic plots (pre/post-fit, pulls, rankings,
limits). The preferred stable release is via `StatAnalysis`:

```bash
setupATLAS
asetup StatAnalysis,0.7.3   # EL9; for CentOS7 use: setupATLAS -c el9
```

## When to Use

- Physics group mandates TRExFitter for an ATLAS publication
- Producing HistFactory XML/ROOT output (combinations with other analyses)
- Standard fit diagnostics: pre/post-fit plots, NP pulls, NP ranking, limits
- TOP, SM, or Higgs analyses following existing group config conventions
- pyhf is unavailable or the analysis requires ROOT-based systematics smoothing

## Key Concepts

### Action Codes

Run as `trex-fitter <actions> config.config [Options]`. Actions chain:
`trex-fitter nwfdprl config.config`.

| Code | Action                           | Requires      |
| ---- | -------------------------------- | ------------- |
| `n`  | Ntuple → histograms              | NTuple inputs |
| `h`  | Read/cache histograms            | HIST inputs   |
| `w`  | Build RooStats XML workspace     | `h` or `n`    |
| `f`  | Fit workspace                    | `w`           |
| `d`  | Pre-fit data/MC plots            | `h` or `n`    |
| `p`  | Post-fit plots (uses fit result) | `f`           |
| `r`  | NP ranking plot                  | `f`           |
| `l`  | CLs exclusion limit              | `w`           |
| `s`  | Discovery significance           | `w`           |
| `x`  | Likelihood scan only             | `f`           |
| `b`  | Re-run smoothing/rebinning       | `h` or `n`    |
| `i`  | Grouped NP impact                | `f`           |
| `j`  | Translate to HS3 JSON format     | `w`           |

### Config Block Hierarchy

Every `Job` needs exactly one `Fit`, at least one `Region` and one `Sample`.
`Limit`, `Significance`, `NormFactor`, `Systematic`, `ShapeFactor` are optional.
Blocks are separated by blank lines; `%` begins a comment.

### Systematic Types

| Type      | Effect                                 | Prior         |
| --------- | -------------------------------------- | ------------- |
| `OVERALL` | Normalization only                     | Log-normal    |
| `HISTO`   | Shape + norm from ±1σ templates        | Gaussian      |
| `SHAPE`   | Shape only (norm constrained to 1)     | Gaussian      |
| `STAT`    | MC stat (Barlow–Beeston, auto per bin) | Poisson/Gauss |

### Interpolation

Default `IntCode: 4` — piecewise-linear shape interpolation, exponential
normalization interpolation. Exponential normalization prevents negative yields
and, combined with the Gaussian constraint, produces a log-normal marginal
distribution for the normalization component.

### Histogram Input Convention (`ReadFrom: HIST`)

TRExFitter resolves input files as `{HistoPath}/{HistoFile}_{Region}.root` (or
per-sample overrides). The histogram inside is `HistoName`. Systematic
variations append to `HistoName`: `h_nom` → `h_JES_up`, `h_JES_dn`.

## Canonical Patterns

### Complete Config Skeleton

```
% ── Job (global settings) ─────────────────────────────────────────────────
Job: "MyAnalysis"
  CmeLabel: "13 TeV"
  POI: "mu_sig"
  ReadFrom: HIST
  HistoPath: "histograms"
  OutputDir: "output/MyAnalysis"
  LumiLabel: "139 fb^{-1}"
  Lumi: 139.0
  MCstatThreshold: 0.01
  SystPruningShape: 0.02
  SystPruningNorm: 0.02
  DebugLevel: 1

% ── Fit ───────────────────────────────────────────────────────────────────
Fit: "MyFit"
  FitType: SPLUSB
  FitRegion: CRSR
  POIAsimov: 1
  UseMinos: mu_sig

% ── Limit ─────────────────────────────────────────────────────────────────
Limit: "MyLimit"
  LimitType: ASYMPTOTIC
  POIAsimov: 0

% ── Significance ──────────────────────────────────────────────────────────
Significance: "MySig"
  SignificanceType: ASYMPTOTIC
  POIAsimov: 1

% ── Regions ───────────────────────────────────────────────────────────────
Region: "SR"
  Type: SIGNAL
  Label: "Signal Region"
  HistoName: "h_meff"
  VariableTitle: "m_{eff} [GeV]"
  ShortLabel: "SR"

Region: "CR_top"
  Type: CONTROL
  Label: "Top CR"
  HistoName: "h_meff"
  ShortLabel: "CR"

% ── Samples ───────────────────────────────────────────────────────────────
Sample: "Signal"
  Type: SIGNAL
  HistoFile: "signal"
  FillColor: 632
  NormalizedByTheory: TRUE

Sample: "ttbar"
  Type: BACKGROUND
  HistoFile: "ttbar"
  FillColor: 4

Sample: "Data"
  Type: DATA
  HistoFile: "data"

% ── NormFactor ────────────────────────────────────────────────────────────
NormFactor: "mu_ttbar"
  Title: "#mu_{t#bar{t}}"
  Nominal: 1
  Min: 0
  Max: 5
  Samples: ttbar

% ── Systematics ───────────────────────────────────────────────────────────
Systematic: "JES"
  Title: "Jet Energy Scale"
  Type: HISTO
  HistoNameUp: "h_meff_JES_up"
  HistoNameDown: "h_meff_JES_dn"
  Samples: ttbar, Signal
  Symmetrisation: TWOSIDED
  Smoothing: 40

Systematic: "Lumi"
  Title: "Luminosity"
  Type: OVERALL
  OverallUp: 0.015
  OverallDown: -0.015
  Samples: ttbar, Signal
```

### Standard Workflow

```bash
trex-fitter h config.config          # cache histograms
trex-fitter w config.config          # build workspace
trex-fitter d config.config          # pre-fit plots
trex-fitter f config.config          # fit
trex-fitter p config.config          # post-fit plots
trex-fitter r config.config          # NP ranking
trex-fitter l config.config          # CLs limit
trex-fitter s config.config          # significance
```

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`references/advanced-config-patterns.md`** — Asimov/blind fits,
  parallelising the histogram and ranking steps, correlating/decorrelating
  nuisance parameters, `NormFactor` `Expression` syntax, MC statistical
  uncertainty tuning, exporting to pyhf, and a fit/limit troubleshooting table.
  Read when running a blind or stat-only fit, splitting a slow `h`/`r` step
  across jobs, sharing or splitting a `NuisanceParameter`, writing a
  `TFormula`-based `NormFactor`, or diagnosing a fit convergence, pull, or limit
  failure.
- **`references/worked-example.md`** — Complete multi-region, multi-sample
  config for a ttH→bb search (2 regions, one signal, two backgrounds — ttbar and
  Wjets — one data sample, NormFactors, and systematics wired together) plus the
  full run pipeline and output directory layout. Read when adapting a full
  worked config rather than the minimal skeleton above.

## Gotchas

- **`%` is the comment character** (not `#` or `//`); `#` inside strings is fine
  for ROOT LaTeX titles.
- **Blank lines required between blocks**; missing blank lines silently merge
  blocks or cause parse errors.
- **`CRONLY` fit** profiles NPs in CRs only — switch to `CRSR` for the final
  result.
- **`MCstatThreshold: NONE`** disables all gamma parameters; use with care as MC
  stat can dominate in sparse bins.
- **Smoothing on correlated NPs**: use `Smoothing: 40`; for uncorrelated use
  `400`. Visualise `Systematics/` plots before trusting smoothed templates.
- **NuisanceParameter sharing = 100% correlation**: two `Systematic` blocks with
  the same `NuisanceParameter` value are treated as the same NP.
- **`OverallUp/Down` in `HISTO` systematics** are ignored; norm component is
  extracted automatically from the template integrals.
- **`POIAsimov`** in the `Fit` block controls the Asimov signal strength for
  expected quantities — set to `0` for expected limits, `1` for expected
  significance.
- **Ranking step (`r`) is slow** by default; parallelise via `LHscanStep`.
- **EL9 required** (`StatAnalysis ≥ 0.7`); CentOS7 needs the `el9` container:
  `setupATLAS -c el9`.

## Interop

- **pyhf**: `pyhf xml2json` converts TRExFitter XML output to JSON workspace;
  expressions and multiple POIs not yet supported in pyhf
- **cabinetry**: high-level Python wrapper; can consume pyhf JSON from
  TRExFitter and produce equivalent diagnostic plots
- **hist / uproot**: build histogram templates in Python, write to ROOT with
  uproot, feed to TRExFitter via `ReadFrom: HIST`
- **HistFitter**: workspaces interchange at the HistFactory XML level
- **pyHS3**: schema-compliant serialisation; TRExFitter produces HS3 via the `j`
  action

## Docs

https://trexfitter-docs.web.cern.ch/trexfitter-docs/latest/
