---
name: workspacecombiner
description: >-
  Use when combining multiple RooFit workspaces with workspaceCombiner, editing
  workspace parameterization with the manager edit command, printing or
  splitting workspace categories, regulating a workspace, or preparing NP
  renaming maps for ATLAS Higgs combination workflows.
---

# workspaceCombiner

## Overview

workspaceCombiner is an XML-driven tool for combining, editing, and debugging
RooFit workspaces. Widely used in ATLAS and LHC combination efforts since the
Higgs boson discovery, it provides four main operations:

| Operation       | Flag                  | Description                                              |
| --------------- | --------------------- | -------------------------------------------------------- |
| `combine`       | `-w combine`          | Combine multiple input workspaces into one               |
| `edit`          | `-w edit`             | Modify PDFs, NPs, POIs in an existing workspace          |
| `split`/`print` | `-w split`/`-w print` | Print workspace contents; extract a subset of categories |
| `regulate`      | `-w regulate`         | Rebuild workspace PDFs with standardized structure       |

For statistical tests on a combined workspace, use
[quickFit](https://gitlab.cern.ch/atlas_higgs_combination/software/quickFit).

workspaceCombiner is included in the StatAnalysis release (available after
`asetup StatAnalysis,0.7,latest`).

Repository:
https://gitlab.cern.ch/atlas_higgs_combination/software/workspaceCombiner/

## Prerequisites for Input Workspaces

Input workspaces must satisfy the following requirements:

- **Fit model**: Use
  [`RooSimultaneous`](https://root.cern.ch/doc/master/classRooSimultaneous.html)
  even for single-category analyses.
- **Data**: Use
  [`RooDataSet`](https://root.cern.ch/doc/master/classRooDataSet.html),
  categorized with the same `RooCategory` as the fit model.
- **ModelConfig**: Provide a
  [`RooStats::ModelConfig`](https://root.cern.ch/doc/master/classRooStats_1_1ModelConfig.html)
  that correctly identifies observables, POIs, NPs, and global observables.
- **Constraint PDFs**: Implement as normal (Gaussian, unit sigma, zero mean)
  PDFs where possible; multiply them to the S+B PDF.
- **Observable uniqueness**: Each observable must have a unique name across the
  entire combination: `(observable)_(category)_(analysis)` convention
  recommended.
- **RooFormulaVar**: Use indexed syntax (`@0+@1`) not variable names; renaming
  breaks name-based formulas.

## Workspace Printing and Splitting

```bash
# Print workspace summary (categories, POIs, datasets)
manager -w print -f ws.root --wsName combWS --dataName obsData

# Extract categories 1, 3, 4, 5 into a new workspace
manager -w split -f ws.root --wsName combWS --dataName obsData \
  -i 1,3-5 -p split.root

# Keep all categories (split with all)
manager -w split -f ws.root --wsName combWS --dataName obsData -i all

# Regulate: rebuild all category PDFs, strip unused constraint terms
manager -w regulate -f ws.root --wsName combWS --dataName obsData
```

Split output always uses `combWS`/`ModelConfig`/`combData` as fixed names. Add
`--rebuildPdf 1` to rebuild per-category PDFs. Add `--rebin N` to convert
unbinned datasets to binned with N bins.

## Workspace Editing

Editing modifies parameterization of an existing workspace via an XML card:

```bash
manager -w edit -x modify.xml
```

### Edit card structure (Organization.dtd)

```xml
<!DOCTYPE Organization SYSTEM 'Organization.dtd'>
<Organization InFile="input.root" OutFile="output.root"
  ModelName="myModel"
  POINames="mu,mu_ttH"
  WorkspaceName="combWS"
  ModelConfigName="ModelConfig"
  DataName="combData">

  <!-- Create new RooFit objects (RooWorkspace::factory syntax) -->
  <Item Name="zero[0]"/>
  <Item Name="RooGaussian::myConstr(myNP,myNP_In,1)"
    Type="constraint" NP="myNP" GO="myNP_In"/>

  <!-- Replace old objects with new ones -->
  <Map Name="EDIT::NEWPDF(OLDPDF,
    old_param=new_param,
    old_NP=zero
  )"/>

  <!-- Optional: fit and/or create Asimov after editing -->
  <Asimov Name="ucmles" Setup="mu=1_0_5"
    Action="fit:savesnapshot" SnapshotAll="ucmles"/>
</Organization>
```

`Organization.dtd` must be present in the same folder as the XML card.

### Asimov action keywords

| Keyword           | Meaning                                                         |
| ----------------- | --------------------------------------------------------------- |
| `fit`             | Perform maximum likelihood fit                                  |
| `genasimov`       | Generate Asimov dataset (once per action list)                  |
| `savesnapshot`    | Save snapshot (once per action list)                            |
| `matchglob`       | Match global observables to NP values; always pair with `reset` |
| `reset`           | Reset parameters to state before current action list            |
| `raw`             | Reset to state before any actions                               |
| `fixsyst`         | Fix all constrained NPs                                         |
| `fixall`          | Fix all NPs                                                     |
| `float`           | Float NPs fixed by `fixsyst` or `Setup`                         |
| `<snapshot name>` | Load a named snapshot                                           |

Parameter `Setup` syntax: `param=value` to fix; `param=start_low_high` to float.

## Workspace Combination

Combines multiple input workspaces. Requires `Combination.dtd` in the same
folder as XML cards.

```bash
manager -w combine -x combine.xml
```

### Combination card structure (Combination.dtd)

```xml
<!DOCTYPE Combination SYSTEM 'Combination.dtd'>
<Combination WorkspaceName="combWS"
  ModelConfigName="ModelConfig"
  DataName="combData"
  OutputFile="combined.root">

  <!-- Combined POI list: value = fixed; start~lo~hi = floating -->
  <POIList Combined="mu[1~0~5],mu_ttH[1]"/>

  <!-- Optional fit / Asimov actions -->
  <Asimov Name="ucmles" Setup="mu=1_0_5"
    Action="fit:savesnapshot" SnapshotAll="ucmles"/>

  <!-- One Channel block per input workspace -->
  <Channel Name="channel_HZZ"
    InputFile="reparam/WS-HZZ.root"
    WorkspaceName="combined"
    ModelConfigName="ModelConfig"
    DataName="obsData">
    <!-- Input POI list must match Combined POIList one-to-one; use "dummy" for missing POIs -->
    <POIList Input="mu,mu_ttH,dummy,dummy"/>
    <!-- NP renaming map for correlations -->
    <RenameMap InputFile="syst_map/channel_HZZ.xml"/>
  </Channel>

  <Channel Name="channel_Hyy" ...>
    ...
  </Channel>
</Combination>
```

Add tag `_binned` to the channel name (e.g. `channel_HZZ_binned`) to enable
binned fit acceleration for HistFactory workspaces.

Set `SimplifiedImport="true"` on a channel if all objects already have unique
names — this skips renaming and is faster for large workspaces.

## NP Renaming Maps

The renaming map correlates NPs across input channels. NPs with the same
`NewName` become correlated in the combination.

```xml
<!-- Gaussian-constrained NP -->
<Syst OldName="lumi_pdf(lumi_NP, lumi_In)" NewName="ATLAS_LUMI_RUN2_CORR"/>

<!-- Unconstrained (free) NP -->
<Syst OldName="bkg_slope" NewName="bkg_slope_channel_yy"/>

<!-- HistFactory gamma NPs (bin-by-bin stat) — never correlate across channels -->
<Syst OldName="gamma_stat_SR_bin_0" NewName="gamma_stat_SR_bin_0"/>
```

NPs not listed in the map are renamed with the channel name as postfix. NPs
listed but absent in the workspace are silently skipped.

## Gotchas

- **`Combination.dtd` / `Organization.dtd`**: must be in the same folder as the
  XML card, not just the working directory.
- **One-to-one POI list**: the `Input` POI list in each `Channel` must have the
  same length as the `Combined` list; use `dummy` as placeholder.
- **Cross-channel NP correlation**: achieved only through matching `NewName` in
  renaming maps; never by identical `OldName`.
- **Custom RooFit classes**: workspaces using classes outside vanilla ROOT
  require those classes compiled into `RooFitExtensions` or added manually to
  the workspaceCombiner source (`inc/` + `src/` + `LinkDef.h`).
- **No intra-channel NP merging**: to correlate two NPs within the same input
  channel, edit the workspace first before combining.

## Interop

- **quickFit**: recommended fitting tool for combined workspaces.
- **xmlAnaWSBuilder**: produces single-channel analytic workspaces that are
  valid workspaceCombiner inputs.
- **StatAnalysis**: workspaceCombiner is available after
  `asetup StatAnalysis,0.7,latest`.

## Support

Contact: workspaceCombiner-user@cern.ch

## Docs

https://gitlab.cern.ch/atlas_higgs_combination/software/workspaceCombiner/
