---
name: topcptoolkit
description: >-
    Use when using TopCPToolkit to process ATLAS DAOD files into analysis
    NTuples: configuring the YAML-based analysis setup, understanding the
    supported object collections and CP algorithm configuration, running the
    toolkit on the grid or locally, or understanding the output NTuple
    structure for downstream analysis with uproot or coffea.
---

# TopCPToolkit

## Overview

TopCPToolkit (TCT) is an ATLAS analysis framework that wraps the standard CP algorithms (jet calibration, lepton scale factors, b-tagging, systematics) and produces flat NTuples from DAOD input via a YAML configuration. It is the recommended path for top-quark analyses and is widely adopted across ATLAS for DAOD → NTuple production.

## When to Use

- Producing analysis-ready NTuples from DAOD_PHYS or DAOD_PHYSLITE
- Analyses requiring standard CP tool setup (jet/lepton/MET calibration + SFs)
- Top quark, ttbar, single-top, and related SM analyses
- When you want a supported, group-endorsed framework rather than a custom setup

## Workflow

```
DAOD_PHYS / DAOD_PHYSLITE
    ↓ TopCPToolkit (runs in AnalysisBase/Athena)
NTuples (ROOT, flat branches)
    ↓ uproot / coffea / FastFrames
Histograms → fit
```

## YAML Configuration

TopCPToolkit is driven by a YAML config file:

```yaml
# analysis.yaml
algSeq:
  - name: EventCleaning
    GoodRunsList: data16_13TeV.physics_25ns_20.7.grl.xml
    
  - name: JetAnalysis
    InputCollection: AnalysisJets   # PHYSLITE collection name
    PtCut: 25000   # MeV
    EtaCut: 2.5
    JVTCut: 0.5
    BTagWP: "DL1dv01:FixedCutBEff_77"
    
  - name: ElectronAnalysis
    InputCollection: AnalysisElectrons
    PtCut: 27000
    EtaCut: 2.47
    IdWP: TightLH
    IsoWP: Gradient
    
  - name: MuonAnalysis
    InputCollection: AnalysisMuons
    PtCut: 27000
    EtaCut: 2.5
    Quality: Medium
    IsoWP: FCLoose
    
  - name: OverlapRemoval
    ElJetDR: 0.2
    JetElDR: 0.4
    JetMuDR: 0.4
    
  - name: METAnalysis
    JetColl: AnalysisJets_Selected
    ElColl: AnalysisElectrons_Selected
    MuColl: AnalysisMuons_Selected
    
  - name: EventSelector
    NJets: 4
    NBJets: 2
    MET: 0   # no MET cut for this example
    
  - name: NTupleMaker
    OutputBranches:
      - jet_pt
      - jet_eta
      - jet_phi
      - jet_e
      - jet_mv2c10
      - el_pt
      - mu_pt
      - met_met
      - weight_mc
      - weight_pileup
      - weight_bTagSF_77
```

## Running TopCPToolkit

**Locally**:
```bash
# Setup AnalysisBase
asetup AnalysisBase,25.2.X

# Run on a local DAOD file
python TopCPToolkit/python/runTopCPToolkit.py \
    --config analysis.yaml \
    --input DAOD_PHYSLITE.pool.root \
    --output output.root \
    --nevents 1000   # for testing
```

**On the grid (Panda/GRID)**:
```bash
prun --exec "python TopCPToolkit/python/runTopCPToolkit.py --config %IN --output %OUT" \
     --inDS user.me.data18.DAOD_PHYSLITE.mycontainer \
     --outDS user.me.output.ntuple
```

## Output NTuple Structure

TCT produces ROOT TTrees with branches named following the convention in your `OutputBranches` config. Typical branch structure (one entry per event):

| Branch | Type | Unit | Notes |
|---|---|---|---|
| `jet_pt` | `vector<float>` | MeV | Calibrated jet pTs |
| `jet_eta` | `vector<float>` | — | |
| `jet_phi` | `vector<float>` | rad | |
| `jet_e` | `vector<float>` | MeV | |
| `jet_btag_dl1dv01` | `vector<float>` | — | DL1dv01 discriminant |
| `el_pt` | `vector<float>` | MeV | |
| `mu_pt` | `vector<float>` | MeV | |
| `met_met` | `float` | MeV | |
| `weight_mc` | `float` | — | MC × filter × k-factor |
| `weight_pileup` | `float` | — | Pile-up reweighting SF |
| `weight_bTagSF_77` | `float` | — | Combined b-tag SF at 77% WP |

## Reading TCT Output with uproot

```python
import uproot, awkward as ak, vector
vector.register_awkward()

with uproot.open("output.root:reco") as tree:
    jets = ak.zip({
        "pt":   tree["jet_pt"].array(),
        "eta":  tree["jet_eta"].array(),
        "phi":  tree["jet_phi"].array(),
        "mass": tree["jet_e"].array() * 0,  # placeholder if mass not stored
    })
    weight = tree["weight_mc"].array() * tree["weight_pileup"].array() * tree["weight_bTagSF_77"].array()
```

## Gotchas

- **Units are MeV**: All pT, energy, MET branches are in MeV — divide by 1000 before GeV-scale histograms
- **PHYSLITE vs PHYS collection names**: PHYSLITE uses `AnalysisJets`; PHYS uses `AntiKt4EMPFlowJets`. Your YAML must match the input DAOD type.
- **Systematic trees**: TCT produces separate TTrees for each systematic variation (e.g., `reco_JES__1up`). Upstream analysis must loop over these trees.
- **Output tree name**: Default is `reco` — check your config if uproot can't find the tree.

## Interop

- **uproot / awkward**: Primary downstream tools for reading TCT NTuples
- **FastFrames**: Alternative to TCT for RDataFrame-based analysis; can read TCT NTuples
- **coffea**: Can process TCT NTuples at scale using coffea processors
- **Rucio**: Use `atlas-data-explorer` to find DAOD containers before running TCT

## Docs

https://topcptoolkit.docs.cern.ch/latest/
