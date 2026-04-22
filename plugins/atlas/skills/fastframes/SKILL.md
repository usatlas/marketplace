---
name: fastframes
description: >-
  Use when using FastFrames to process ATLAS DAOD or NTuple files with
  RDataFrame: configuring FastFrames via YAML, understanding its columnar
  processing model, comparing it to TopCPToolkit, running FastFrames locally or
  on the grid, or reading FastFrames output histograms with uproot or hist.
---

# FastFrames

## Overview

FastFrames is an ATLAS analysis framework built on ROOT RDataFrame. It processes
DAOD or NTuple input in a columnar, lazy-evaluation model that is faster than
event-loop approaches for many workflows. It is an alternative to TopCPToolkit
for analyses that need high throughput or more flexible columnar
transformations.

## When to Use

- Large-scale ATLAS analyses where processing speed matters
- Analyses that prefer a columnar model (define columns, filter, fill
  histograms) over event-loop
- When you need to process both DAOD and NTuple inputs in the same framework
- Teams comfortable with ROOT RDataFrame patterns

## FastFrames vs TopCPToolkit

| Feature               | FastFrames                  | TopCPToolkit      |
| --------------------- | --------------------------- | ----------------- |
| Execution model       | RDataFrame (columnar, lazy) | Event loop        |
| Speed                 | Faster for many workflows   | Adequate for most |
| CP algorithm coverage | Good, growing               | Comprehensive     |
| Systematic handling   | Supports variation TTrees   | Variation TTrees  |
| Community support     | Smaller but active          | Broad (top group) |
| Config format         | YAML                        | YAML              |
| Output                | ROOT histograms or NTuples  | Flat NTuples      |

For most standard ATLAS analyses with full CP tool coverage, **TopCPToolkit is
the safer choice**. Use FastFrames when throughput is critical or when your
analysis team already uses it.

## YAML Configuration

```yaml
# config.yaml
general:
  input_filelist: "filelist.txt" # list of ROOT file paths
  output_path: "output/"
  campaign: "mc20e"
  data_type: "mc" # "data" or "mc"

samples:
  - name: "ttbar"
    dsid: 410470
    cross_section: 831.76 # pb
    filter_efficiency: 1.0
    k_factor: 1.139
    input_path: "/path/to/ttbar/*.root"

regions:
  - name: "SR"
    selection: "n_jets >= 4 && n_bjets >= 2 && met > 200000"

  - name: "CR_top"
    selection: "n_jets >= 4 && n_bjets >= 2 && met < 150000"

histograms:
  - variable: "jet_pt[0]" # Leading jet pT
    name: "leading_jet_pt"
    regions: ["SR", "CR_top"]
    nbins: 50
    xmin: 0
    xmax: 2000000 # MeV

  - variable: "met"
    name: "met_dist"
    regions: ["SR"]
    nbins: 30
    xmin: 0
    xmax: 1000000

systematics:
  - name: "JES"
    type: "tree" # reads separate _JES__1up/_JES__1down trees

  - name: "BTag_77"
    type: "weight" # applies weight variation
    weight_up: "weight_bTagSF_77_up"
    weight_dn: "weight_bTagSF_77_dn"
```

## Running FastFrames

**Locally**:

```bash
# Setup
asetup AnalysisBase,25.2.X
source FastFrames/setup.sh

# Run
fastframes --config config.yaml --ncpu 4
```

**On the grid**:

```bash
prun --exec "fastframes --config config.yaml" \
     --inDS user.me.ntuples.mycontainer \
     --outDS user.me.output.histograms
```

## Reading FastFrames Output

FastFrames produces ROOT files with histograms. Read with uproot:

```python
import uproot, hist

with uproot.open("output/histograms.root") as f:
    # FastFrames names histograms as {sample}_{region}_{variable}
    h_root = f["ttbar_SR_leading_jet_pt"]

    # Convert to hist.Hist for plotting
    h = hist.Hist(hist.axis.Variable(h_root.axis().edges(), name="pt", label=r"$p_T$ [GeV]"))
    h.view()[:] = h_root.values()
```

## Systematic Handling

FastFrames supports two systematic types:

**Tree-based** (for shape systematics from varied NTuples):

```yaml
- name: "JES"
  type: "tree"
  # Reads TTrees named {nominal_tree}_JES__1up and _JES__1down
```

**Weight-based** (for systematics stored as weight branches):

```yaml
- name: "BTag_77"
  type: "weight"
  weight_up: "weight_bTagSF_77_up"
  weight_dn: "weight_bTagSF_77_dn"
```

## Gotchas

- **Units are MeV in ATLAS NTuples**: FastFrames cuts and histogram ranges are
  in the same units as your input — ATLAS NTuples use MeV, so `xmax: 2000000` is
  2 TeV.
- **RDataFrame lazy evaluation**: Column definitions aren't evaluated until an
  action (histogram fill, `Snapshot`) is triggered; bugs in column expressions
  appear at run time.
- **CP algorithm coverage**: FastFrames does not yet cover all CP algorithms;
  check the FastFrames documentation for current support status before choosing
  it over TopCPToolkit.
- **Tree-based systematics require pre-existing variation trees**: FastFrames
  reads variation trees from the input files — you need TCT or another framework
  to have produced them.

## Interop

- **TopCPToolkit**: Can process the same DAOD inputs; TCT NTuples can also be
  read by FastFrames
- **uproot / hist**: Primary downstream tools for reading FastFrames histogram
  output
- **cabinetry / pyhf**: Feed FastFrames histogram output into cabinetry for the
  statistical fit
- **coffea**: Alternative for columnar analysis without ROOT dependency

## Docs

https://atlas-project-topreconstruction.web.cern.ch/fastframesdocumentation/latest/
