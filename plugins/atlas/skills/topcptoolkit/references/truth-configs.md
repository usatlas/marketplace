# Particle-Level and Parton-Level Configs

TCT supports three analysis levels in parallel. Each runs from the same input
DAOD and writes its own output TTree.

| Level    | CLI flag     | Default tree name | YAML file       |
| -------- | ------------ | ----------------- | --------------- |
| Detector | (default)    | `reco`            | `reco.yaml`     |
| Particle | `--particle` | `particle`        | `particle.yaml` |
| Parton   | `--parton`   | `truth`           | `parton.yaml`   |

All three configs live in the same folder under `share/configs/<analysis>/`.

## Particle-level config blocks (`PL_*`)

These blocks work on truth particles from the DAOD, not on calibrated
reconstructed objects. They are used in `particle.yaml`.

| YAML block          | Description                                                                                   |
| ------------------- | --------------------------------------------------------------------------------------------- |
| `PL_Electrons`      | Dressed truth electrons                                                                       |
| `PL_Muons`          | Dressed truth muons                                                                           |
| `PL_Photons`        | Dressed truth photons                                                                         |
| `PL_Taus`           | Hadronic truth taus                                                                           |
| `PL_Jets`           | Truth jets (AntiKt4TruthDressedWZJets or large-R truth jets)                                  |
| `PL_MET`            | Truth MET — output container is `Truth_MET`, not `MET_Truth`                                  |
| `PL_Neutrinos`      | Truth neutrinos                                                                               |
| `PL_Resonances`     | Truth resonances (Z, W, H, ...)                                                               |
| `PL_OverlapRemoval` | Truth-level overlap removal                                                                   |
| `PL_SoftMuons`      | Soft muons at particle level (requires specific PL_Muons + PL_Jets + PL_OverlapRemoval setup) |
| `PL_SpaNet`         | SpaNet reconstruction at particle level                                                       |

`EventSelection:` and `Output:` blocks work identically at particle level.

### Minimal particle.yaml

```yaml
GeneratorLevelAnalysis: {}

PL_Electrons:
  - containerName: "AnaElectrons_PL"
    PtEtaSelection:
      minPt: 27000.0
      maxEta: 2.47

PL_Muons:
  - containerName: "AnaMuons_PL"
    PtEtaSelection:
      minPt: 27000.0
      maxEta: 2.5

PL_Jets:
  - containerName: "AnaJets_PL"
    jetCollection: "AntiKt4TruthDressedWZJets"
    PtEtaSelection:
      minPt: 25000.0
      maxEta: 2.5

PL_MET:
  - containerName: "Truth_MET" # note: not MET_Truth!

PL_OverlapRemoval:
  - electrons: "AnaElectrons_PL"
    muons: "AnaMuons_PL"
    jets: "AnaJets_PL"

EventSelection:
  - electrons: "AnaElectrons_PL"
    muons: "AnaMuons_PL"
    jets: "AnaJets_PL"
    selectionName: "ejets_PL"
    selectionCuts: |
      EL_N  27000 == 1
      MU_N  27000 == 0
      JET_N 25000 >= 4
      SAVE

Output:
  treeName: "particle"
  containers:
    jet_: "AnaJets_PL"
    el_: "AnaElectrons_PL"
    mu_: "AnaMuons_PL"
    "": "EventInfo"
```

## Parton-level config blocks

Parton-level configs use truth-parton histories reconstructed from the generator
record. They are used in `parton.yaml`.

Required blocks: `CommonServices`, `GeneratorLevelAnalysis`, `PartonHistory`,
`Output`.

### Available `PartonHistory` values

Pass the `histories` list under `PartonHistory:`.

| History name      | Process                         |
| ----------------- | ------------------------------- |
| `Ttbar`           | ttbar production                |
| `Ttbarbbbar`      | ttbar + bb                      |
| `Ttbarccbar`      | ttbar + cc                      |
| `Ttz`             | ttZ                             |
| `Ttw`             | ttW                             |
| `Tth`             | ttH                             |
| `Tzq`             | tZq (single top + Z)            |
| `The`             | the or tWH (single top + Higgs) |
| `Wtb`             | Wtb (single top + W)            |
| `Tqgamma`         | tqγ                             |
| `Ttgamma`         | ttγ                             |
| `FourTop`         | tttt                            |
| `HWW`             | H→WW\*                          |
| `HWW_nonresonant` | H→WW\* (Sherpa)                 |
| `HZZ`             | H→ZZ\*                          |
| `Zb`              | Z+b                             |
| `Ztautau`         | Z→ττ                            |
| `WW_nonresonant`  | WW (Sherpa)                     |

Output branches follow the pattern `history_MC_resonance_variable` (no
systematics), e.g. `Ttbar_MC_t_pt`, `Ttbar_MC_Wdecay1_from_t_pdgId`.

### Minimal parton.yaml (ttbar)

```yaml
CommonServices: {}

GeneratorLevelAnalysis: {}

PartonHistory:
  - histories: "Ttbar"

Output:
  treeName: "truth"
  vars:
    - "EventInfo.mcChannelNumber -> mcChannelNumber"
    - "EventInfo.runNumber       -> runNumber"
    - "EventInfo.eventNumber     -> eventNumber"
  containers:
    "": "EventInfo"
    "Ttbar_": "TopPartonHistoryTtbar"
```

## TtbarNNLO reweighting

For ttbar samples, NNLO+PS QCD and EW corrections can be applied via the
`TtbarNNLO` block (must be registered first with `AddConfigBlocks`):

```yaml
AddConfigBlocks:
  - modulePath: "TopCPToolkit.TtbarNNLORecursiveRewConfig"
    functionName: "TtbarNNLORecursiveRewConfig"
    algName: "TtbarNNLO"
    pos: "Output"

TtbarNNLO: {}
```

For a newer alternative with higher-order corrections, use `TtbarHOC` instead
(same registration pattern, block name `TtbarHOC`).

## Docs

<https://topcptoolkit.docs.cern.ch/latest/settings/truth/>
