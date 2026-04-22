---
name: fastframes
description: >-
  Use when using FastFrames to process CP-algorithm-style NTuples with
  RDataFrame: configuring FastFrames via YAML, understanding its columnar
  processing model, running FastFrames locally, or reading FastFrames output
  histograms with uproot or hist.
---

# FastFrames

## Overview

FastFrames is a histogramming and ntuple reprocessing framework built on ROOT's
RDataFrame. It processes NTuples produced by the standard CP algorithm stack in
a columnar, lazy-evaluation model that is faster than event-loop approaches for
many workflows. FastFrames automatically handles cross-section weighting,
systematic variations, and profile-likelihood unfolding. It officially supported
by the ATLAS AMG and is the recommended method to process TopCPToolkit outputs
into histograms.

## When to Use

- When you need process TopCPToolkit outputs
- When you want a supported framework for processing CP algorithm outputs

## YAML Configuration

```yaml
# config.yml
general:
  input_filelist_path: "filelist.txt"
  input_sumweights_path: "sum_of_weights.txt"
  output_path_histograms: ""
  default_sumweights: "NOSYS"
  default_event_weights: "weight_mc_NOSYS *globalTriggerEffSF_NOSYS"
  xsection_files:
  - campaigns: ["mc20a", "mc20d", "mc20e"]
    files: ["test/data/PMGxsecDB_mc16.txt"]
  automatic_systematics: True
  nominal_only: False
  number_of_cpus: 4
  define_custom_columns:
    - name: "jet_pt_GeV_NOSYS"
      definition: "jet_pt_NOSYS/1e3"

regions:
  - name: "Electron"
    selection: "el_pt_NOSYS.size() > 0 && el_pt_NOSYS[0] > 30000"
    histograms_2d:
      - x: "met_met"
        y: "met_phi"
    variables:
      - name: "jet_pt"
        #title : "histo title;X axis title;Y axis title"
        definition: "jet_pt_GeV_NOSYS"
        type: RVec<double>
        is_nominal_only: True
        binning:
          min: 0
          max: 300
          number_of_bins: 10
      - name: "met_met"
        title : "histo title;X axis title;Y axis title"
        definition: "met_met_NOSYS/1e3"
        type: "double"
        is_nominal_only: True
        binning:
          bin_edges: [0,20,60,80,140,250]
      - name: "met_phi"
        title : "histo title;X axis title;Y axis title"
        definition: "met_phi_NOSYS"
        type: "float"
        binning:
          min: -3.2
          max: 3.2
          number_of_bins: 16

truth_processing:
  - name: parton_ttbar
    produce_unfolding: True
    truth_tree_name: "truth"
    samples: ["ttbar_FS"]
    event_weight: "weight_mc_NOSYS"
    match_variables:
      - reco: "jet_pt"
        truth: "Ttbar_MC_t_afterFSR_pt"
    variables:
      - name: "Ttbar_MC_t_afterFSR_pt"
        definition:  "Ttbar_MC_t_afterFSR_pt/1e3"
        type: "double"
        binning:
          min: 0
          max: 500
          number_of_bins: 10

samples:
  - name: "ttbar_FS"
    dsids: [410470]
    campaigns: ["mc20e"]
    simulation_type: "fullsim"

systematics:
  - campaigns: ["mc20e"]
    regions: ["Electron"]
    variation:
      up: "JET_BJES_Response__1up"
      down: "JET_BJES_Response__1down"
  - samples: ["ttbar_FS"]
    campaigns: ["mc20e"]
    variation:
      up: "GEN_0p5muF_0p5muR_NNPDF31_NLO_0118"
      sum_weights_up: "GEN_0p5muF_0p5muR_NNPDF31_NLO_0118"
```

## Running FastFrames

```bash
# setup
asetup AnalysisBase,25.2.X
cmake -S fastframes -B build
cmake --build build
source build/setup.sh

# run
FastFrames.py --config config.yml
```

## Reading FastFrames Output

FastFrames produces ROOT files with histograms. Read with uproot:

```python
import uproot, hist

# By default FastFrames writes one ROOT file per sample
with uproot.open("output/ttbar_FS.root") as f:
    # FastFrames generally names histograms as {region}_{variable}
    h_root = f["Electron_jet_pt"]

    # Convert to hist.Hist for plotting
    h = hist.Hist(hist.axis.Variable(h_root.axis().edges(), name="pt", label=r"$p_T$ [GeV]"))
    h.view()[:] = h_root.values()
```

## Systematic Handling

FastFrames can automatically read systematics from a the input files when `automatic_systematics` is `True`.

FastFrames can also manually handle manually defined systematics in the YAML config.

## Gotchas

- **Units are MeV in ATLAS NTuples**: FastFrames cuts and histogram ranges are
  in the same units as your input — ATLAS NTuples use MeV, so `xmax: 2000000` is
  2 TeV.
- **RDataFrame lazy evaluation**: Column definitions aren't evaluated until an
  action (histogram fill, `Snapshot`) is triggered; bugs in column expressions
  appear at run time. Debugging is generally best performed when running with a
  single thread.

## Interop

- **TopCPToolkit**: FastFrames is the recommended way to process TopCPToolkit
  outputs
- **uproot / hist**: Downstream tools for reading FastFrames histogram output
- **cabinetry / pyhf**: Feed FastFrames histogram output into cabinetry for the
  statistical fit
- **coffea**: Alternative for columnar analysis without ROOT/CPalgs dependencies

## Docs

https://atlas-project-topreconstruction.web.cern.ch/fastframesdocumentation/latest/
