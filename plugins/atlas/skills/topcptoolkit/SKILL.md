---
name: topcptoolkit
description: >-
  Use when using TopCPToolkit (TCT) to produce ATLAS analysis NTuples from DAOD
  files: setting up the YAML-based analysis configuration (Jets, Electrons,
  Muons, OverlapRemoval, EventSelection, Output blocks), understanding the
  single-TTree output format with systematic variations and object selection
  flags, installing and compiling TCT from source, running locally with
  runTop_el.py or on the Grid via submitToGrid.py, configuring detector-level
  and particle/parton-level analyses, writing custom analysis algorithms or
  config blocks, or reading TCT NTuple output with uproot.
---

# TopCPToolkit

## Overview

TopCPToolkit (TCT) is the ATLAS-endorsed NTuple production framework for Run 2
and Run 3 analyses, built around the common CP algorithms in AnalysisBase
release 25. It is the recommended successor to AnalysisTop.

```text
DAOD_PHYS / DAOD_PHYSLITE
    ↓ TopCPToolkit (AnalysisBase 25.2.x, compiled from source)
output.root
  ├── reco              ← single TTree, all systematics per-event/object
  ├── CutBookkeeper_*   ← sum of weights per systematic
  ├── listOfSystematics ← histogram of systematic names
  └── metadata          ← data type, campaign, DSID
    ↓ uproot / FastFrames / coffea
Histograms → fit
```

TCT supports three analysis levels, each with its own YAML config:

| Level    | YAML file       | CLI flag     | Description                      |
| -------- | --------------- | ------------ | -------------------------------- |
| Detector | `reco.yaml`     | (default)    | Calibrated objects + systematics |
| Particle | `particle.yaml` | `--particle` | Truth-level particle objects     |
| Parton   | `parton.yaml`   | `--parton`   | Parton history (e.g. ttbar)      |

For particle-level (`PL_*`) and parton-level blocks, available `PartonHistory`
values, and example `particle.yaml`/`parton.yaml` configs, see
`references/truth-configs.md`.

## When to Use

- Producing analysis-ready NTuples from `DAOD_PHYS` or `DAOD_PHYSLITE`
- Analyses requiring standard CP tool setup (jets, leptons, MET, b-tagging,
  triggers, scale factors, pileup reweighting)
- Top quark, ttbar, single-top, and related SM/BSM analyses
- Migrating from AnalysisTop — TCT is its release-25 successor
- When you want a supported, group-endorsed framework with centralised
  maintenance

## Key Concepts

### Single-TTree output with systematic variations

TCT writes a **single TTree** (`reco` by default) for all systematics. There are
no per-systematic TTrees. Instead, each systematically-varying branch carries a
`%SYS%` suffix that is resolved at runtime:

| Branch                                  | Type            | Notes                                                 |
| --------------------------------------- | --------------- | ----------------------------------------------------- |
| `jet_pt_NOSYS`                          | `vector<float>` | Nominal jet pT (MeV)                                  |
| `jet_pt_JET_JER_EffectiveNP_1__1up`     | `vector<float>` | JER variation                                         |
| `jet_select_baselineJvt_%SYS%`          | `vector<char>`  | Boolean selection flag per jet                        |
| `el_pt_%SYS%`                           | `vector<float>` | Electron pT (MeV)                                     |
| `mu_pt_%SYS%`                           | `vector<float>` | Muon pT (MeV)                                         |
| `met_met_%SYS%`                         | `float`         | MET (MeV)                                             |
| `weight_mc`                             | `float`         | MC × filter × k-factor                                |
| `weight_pileup_%SYS%`                   | `float`         | Pileup reweighting SF                                 |
| `weight_btagSF_GN2v01_Continuous_%SYS%` | `float`         | Combined b-tag SF (lowercase `btagSF`; WP per config) |

**Object selection flags** (`object_select_NAME_%SYS%`) are the key to working
with this format: objects with `select_NAME == 0` must be skipped when analysing
systematic `%SYS%`. Objects are **not** sorted by pT (sorting cannot be
preserved across systematics).

### YAML config blocks

The config is driven by a YAML file where each top-level key names a config
block. See
[Auto-generated settings docs](https://topcptoolkit.docs.cern.ch/latest/settings/).

Minimal required blocks: `CommonServices` and `Output`.

Key blocks and their typical YAML keys:

| Block            | What it does                                     |
| ---------------- | ------------------------------------------------ |
| `CommonServices` | Pileup reweighting, systematics service, GRL     |
| `Electrons`      | Egamma calibration + ID/isolation working points |
| `Muons`          | Muon calibration + ID/isolation working points   |
| `Jets`           | Jet calibration, JVT, b-tagging                  |
| `Photons`        | Photon calibration and identification            |
| `Taus`           | Tau calibration and identification               |
| `MissingET`      | MET reconstruction (YAML block name `MissingET`) |
| `OverlapRemoval` | OR between object collections                    |
| `Trigger`        | Trigger decision + matching + scale factors      |
| `EventSelection` | Event-level cuts and region definitions          |
| `Thinning`       | Reduce containers to objects passing a selection |
| `Output`         | NTuple tree name, branches, and containers       |

## Installation and Setup

```bash
# Get the code
git clone https://gitlab.cern.ch/atlas-phys/top/TopCPToolkit.git
cd TopCPToolkit
mkdir -p build run

# Check out a stable release tag (recommended)
git fetch -a
git checkout tags/vX.Y.Z -b myanalysis

# Set up the software environment (on lxplus / CVMFS)
setupATLAS
cd build
asetup AnalysisBase,25.2.X

# Compile
cmake ../source
make -j4
source */setup.sh
```

## Running Locally

The entry point is `runTop_el.py` (available after compilation + setup):

```bash
cd run

# Minimal run (detector-level, all systematics)
runTop_el.py -i inputs.txt -o output

# Quick test: 10000 events, no systematics
runTop_el.py -i inputs.txt -o output -e 10000 --no-systematics

# Run a YAML config from the tutorial folder
runTop_el.py -i inputs.txt -o output -t exampleTtbarLjets

# Detector + particle + parton level with a custom package
runTop_el.py -i inputs.txt -o output --particle --parton \
    -p MyAnalysisPackage -a MyCustomAnalysis
```

`inputs.txt` is a plain text file with one input DAOD path per line. The run
must cover a **single sample** (one DSID/campaign per job).

Key CLI options:

| Flag                        | Default                                        | Purpose                                |
| --------------------------- | ---------------------------------------------- | -------------------------------------- |
| `-i`                        | required                                       | Text file with input DAOD paths        |
| `-o`                        | required                                       | Output directory name                  |
| `-t` / `--text-config`      | None                                           | YAML config folder name                |
| `-a` / `--analysis`         | `TopCPToolkit.TtbarCPalgoConfigBlocksAnalysis` | Python analysis module                 |
| `-p` / `--analysis-package` | `TopCPToolkit/configs`                         | Package/path for `-t` or `-a`          |
| `-e` / `--max-events`       | -1                                             | Max events (for testing)               |
| `--no-systematics`          | False                                          | Skip systematic variations             |
| `--no-filter`               | False                                          | Save all events (keep filter decision) |
| `--particle`                | False                                          | Enable particle-level analysis         |
| `--parton`                  | False                                          | Enable parton-level analysis           |

## Canonical YAML Config

### Minimal detector-level config

```yaml
# reco.yaml — full ttbar lepton+jets reco config
CommonServices: {}

Electrons:
  - containerName: "AnaElectrons"
    crackVeto: True
    WorkingPoint:
      - selectionName: "tight"
        identificationWP: "TightLH"
        isolationWP: "Tight_VarRad"
    PtEtaSelection:
      minPt: 27000.0 # MeV
      maxEta: 2.47
      useClusterEta: True

Muons:
  - containerName: "AnaMuons"
    WorkingPoint:
      - selectionName: "tight"
        quality: "Medium"
        isolation: "Tight_VarRad"
    PtEtaSelection:
      minPt: 27000.0 # MeV
      maxEta: 2.5

Jets:
  - containerName: "AnaJets"
    jetCollection: "AntiKt4EMPFlowJets" # PHYS; use AnalysisJets for PHYSLITE
    runJvtSelection: True
    PtEtaSelection:
      minPt: 25000.0
      maxEta: 2.5
    FlavourTagging:
      - btagger: "DL1dv01"
        btagWP: "FixedCutBEff_77"

MissingET:
  - containerName: "AnaMET"
    jets: "AnaJets.baselineJvt"
    electrons: "AnaElectrons.tight"
    muons: "AnaMuons.tight"

OverlapRemoval:
  - inputLabel: "preselectOR"
    outputLabel: "passesOR"
    jets: "AnaJets.baselineJvt"
    electrons: "AnaElectrons.tight"
    muons: "AnaMuons.tight"

EventSelection:
  - electrons: "AnaElectrons.tight"
    muons: "AnaMuons.tight"
    jets: "AnaJets.passesOR"
    btagDecoration: "ftag_select_DL1dv01_FixedCutBEff_77"
    selectionName: "ejets"
    selectionCuts: |
      EL_N tight 27000 == 1
      MU_N tight 27000 == 0
      JET_N passesOR 25000 >= 4
      JET_N_BTAG passesOR >= 2
      SAVE

Thinning:
  - containerName: "AnaJets"
    outputName: "OutJets"
    selectionName: "passesOR"
  - containerName: "AnaElectrons"
    outputName: "OutElectrons"
    selectionName: "tight"
  - containerName: "AnaMuons"
    outputName: "OutMuons"
    selectionName: "tight"

Output:
  treeName: "reco"
  containers:
    jet_: "OutJets"
    el_: "OutElectrons"
    mu_: "OutMuons"
    "": "EventInfo"
```

For the full `selectionCuts` keyword reference (`EL_N`, `JET_N_BTAG`,
`GLOBALTRIGMATCH`, `IMPORT`, `SAVE`, etc.) and patterns for combining loose and
tight working points with `||` (e.g. for fake-lepton estimates), see
`references/event-selection-dsl.md`.

For a full worked example of reading the `reco` TTree with uproot — applying the
object selection flag, combining event weights, and normalising via
CutBookkeeper — see `references/troubleshooting.md`.

## Grid Submission

```bash
# After local setup (lsetup emi, voms-proxy-init, lsetup rucio, lsetup panda)
cd run
getExamples          # creates run/grid/ with submitToGrid.py and sample lists

# Edit submitToGrid.py, then:
python submitToGrid.py
```

Key fields in `submitToGrid.py`:

| Field          | Purpose                                         |
| -------------- | ----------------------------------------------- |
| `code`         | The `runTop_el.py` command (without `-o`)       |
| `gridUsername` | Grid certificate username                       |
| `suffix`       | Tag appended to output container names          |
| `noSubmit`     | `True` to dry-run and check prun commands first |
| `names`        | List of sample names to process                 |
| `otherOptions` | Extra `prun` flags (e.g. `--nFilesPerJob 3`)    |

## Gotchas

- **Units are MeV**: All pT, energy, and MET branches are in MeV. Divide by 1000
  before making GeV-scale histograms.
- **PHYSLITE vs PHYS collection names**: PHYSLITE uses `AnalysisJets`,
  `AnalysisElectrons`, `AnalysisMuons`; PHYS uses `AntiKt4EMPFlowJets`,
  `Electrons`, `Muons`. The `jetCollection` key in `Jets:` must match your
  input.
- **Single sample per job**: `inputs.txt` must contain files from a single DSID
  and MC campaign. Mixing DSIDs corrupts CutBookkeeper normalisation.
- **b-tagger naming**: The current default tagger in the `Jets.FlavourTagging`
  block is `GN2v01` with `btagWP: 'Continuous'` (`DL1dv01` is still selectable;
  `MV2c10` is retired). The b-tag selection decoration follows
  `ftag_select_TAGGER_WP_%SYS%`, and the SF weight branch is
  `weight_btagSF_TAGGER_WP_%SYS%` (lowercase `btagSF`), e.g.
  `weight_btagSF_GN2v01_Continuous_NOSYS`.
- **Output tree name**: Default is `reco`. Parton-level output uses `truth`.
  Check your config's `Output.treeName` if uproot cannot find the tree.

For common crash messages, warning floods, debugging tips (including limiting
systematics to specific categories), AnalysisTop migration notes (including the
custom-algorithm / `AddConfigBlocks` pattern for analysis-specific logic), and a
worked uproot reading example, see `references/troubleshooting.md`.

## Interop

- **FastFrames**: Preferred histogramming framework for TCT NTuples; reads the
  single-TTree format natively with RDataFrame. Use instead of `TTree::Draw`.
- **uproot / awkward**: Primary Python tools for reading TCT NTuples downstream.
- **coffea**: Can process TCT NTuples at scale with coffea processors.
- **Rucio / atlas-data-explorer**: Use to find DAOD containers before running
  TCT.
- **cabinetry / pyhf**: Statistical analysis on histograms produced from TCT
  NTuples.

## Docs

<https://topcptoolkit.docs.cern.ch/latest/>

Settings reference: <https://topcptoolkit.docs.cern.ch/latest/settings/>

Tutorials: <https://topcptoolkit.docs.cern.ch/latest/tutorials/setup/>

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`event-selection-dsl.md`** — Full `selectionCuts` keyword table (`EL_N`,
  `JET_N_BTAG`, `GLOBALTRIGMATCH`, `IMPORT`, `SAVE`, etc.), subregion/`IMPORT`
  region patterns, per-region b-tag overrides, trigger-matching postfixes, and
  combining loose/tight working points with `||`. Read when writing or debugging
  an `EventSelection` block's `selectionCuts` DSL.
- **`truth-configs.md`** — Particle-level (`PL_*`) and parton-level config
  blocks, the full `PartonHistory` value table, example `particle.yaml`/
  `parton.yaml` configs, and `TtbarNNLO`/`TtbarHOC` reweighting. Read when
  configuring a particle- or parton-level analysis.
- **`troubleshooting.md`** — Common crash messages, warning floods,
  unexpected-output symptoms, AnalysisTop migration notes (including the
  `CustomEventSaver`/`AddConfigBlocks` equivalent), a worked uproot reading
  example, and debugging tips. Read when a TCT job crashes, prints unexpected
  warnings, or produces unexpected output.
