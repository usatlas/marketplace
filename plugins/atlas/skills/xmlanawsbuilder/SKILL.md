---
name: xmlanawsbuilder
description: >-
  Use when building a RooFit workspace from XML cards with xmlAnaWSBuilder or
  XMLReader, constructing analytic signal or background models for H→γγ or
  similar ATLAS analyses, configuring systematic uncertainties in the XML
  workspace builder, setting up counting experiments, implementing blinded
  analysis ranges, or combining categories into a likelihood workspace for
  downstream fitting with quickFit or workspaceCombiner.
---

# xmlAnaWSBuilder

## Overview

xmlAnaWSBuilder constructs RooFit workspaces for statistical analyses using
XML configuration cards. It specializes in:

- **1D analytic models** (e.g. H→γγ signal as double-sided Crystal Ball,
  background as polynomial or power-law)
- **Counting experiments** (no shape information)
- **Multi-category likelihoods** combining signal and background processes

The produced workspace follows the standard `RooSimultaneous` + `ModelConfig`
convention and can be used directly with
[workspaceCombiner](https://gitlab.cern.ch/atlas_higgs_combination/software/workspaceCombiner)
and [quickFit](https://gitlab.cern.ch/atlas_higgs_combination/software/quickFit).

xmlAnaWSBuilder is included in the StatAnalysis release. It can also be built
standalone from:
https://gitlab.cern.ch/atlas-hgam-sw/xmlAnaWSBuilder

## Running XMLReader

```bash
XMLReader -x config/myanalysis/top.xml

# With options
XMLReader -x config/top.xml --plot rebin10
XMLReader -x config/top.xml -b 1 -s 0        # binned fit, Minuit2 strategy 0
XMLReader -x config/top.xml -v               # verbose debug output
```

| Option | Description |
|---|---|
| `-x` / `--xml` | Top-level XML card path (required) |
| `-v` / `--verbose` | Print debug info |
| `-m` / `--minimizerAlgo` | `Minuit2` (default) or `Minuit` |
| `-s` / `--minimizerStrategy` | 0, 1 (default), or 2 |
| `-t` / `--minimizerTolerance` | Default 1e-3 |
| `-b` / `--binned` | Fit to binned (pseudo-binned) dataset |
| `-o` / `--plotOption` | Plot options (e.g. `logy`, `rebin10`) |

## Three-Level XML Structure

```
top-level card (.xml)
  └── category-level cards (one per analysis category)
        └── pdf-level cards (one per physics process per category)
```

`AnaWSBuilder.dtd` must be present alongside every XML card file.

## Top-Level Card

```xml
<!DOCTYPE Combination SYSTEM 'AnaWSBuilder.dtd'>
<Combination WorkspaceName="combWS" ModelConfigName="ModelConfig"
  DataName="combData" OutputFile="workspace/output.root" Blind="false">

  <Input>config/category_A.xml</Input>
  <Input>config/category_B.xml</Input>

  <POI>mu,mu_ttH</POI>

  <!-- Fit and/or Asimov generation actions -->
  <Asimov Name="asimovData_0" Setup="mu=0"
    Action="fixsyst:fit:genasimov:float:savesnapshot"
    SnapshotNuis="nominalNuis" SnapshotGlob="nominalGlob"/>
  <Asimov Name="asimovData_1" Setup="mu=1,mu_ttH=1"
    Action="fit:matchglob:genasimov:savesnapshot:reset"
    SnapshotNuis="conditionalNuis_1" SnapshotGlob="conditionalGlob_1"/>
</Combination>
```

For blinded analysis set `Blind="true"` and add `BlindRange` to each `Data`
node (see [Blinded Analysis](#blinded-analysis)).

### Asimov action keywords

| Keyword | Meaning |
|---|---|
| `fit` | Maximum likelihood fit |
| `genasimov` | Generate Asimov dataset (once per line) |
| `savesnapshot` | Save parameter snapshot (once per line) |
| `matchglob` | Match global observables to NP values; always pair with `reset` |
| `reset` | Reset to state before current action list |
| `raw` | Reset to state before any actions |
| `fixsyst` | Fix all constrained NPs |
| `fixall` | Fix all NPs |
| `float` | Float NPs fixed by `fixsyst` or `Setup` |
| `<snapshot name>` | Load a saved snapshot |

## Category-Level Card

```xml
<!DOCTYPE Channel SYSTEM 'AnaWSBuilder.dtd'>
<Channel Name="ttH_c27" Type="shape" Lumi="139">

  <!-- Dataset from text file -->
  <Data InputFile="data/mass_points.txt"
    Observable="atlas_invMass_:category:[105,160]"
    Binning="220" InjectGhost="true" BlindRange="120,130"/>

  <!-- Common yield systematics (applied to processes via ImportSyst) -->
  <Systematic Name="ATLAS_lumi_run2" Constr="logn"
    CentralValue="1" Mag="0.017" WhereTo="yield"/>

  <!-- Common items (variables, functions) -->
  <Item Name="prod::resp_RES(response::ATLAS_EG_RESOLUTION_ALL)"/>

  <!-- Physics process -->
  <Sample Name="signal" InputFile="config/model/signal_:category:.xml"
    ImportSyst=":common:" MultiplyLumi="true" SharePdf="commonSig">
    <NormFactor Name="yield_sig[10,0,1000]"/>
    <NormFactor Name="mu[1,0,5]"/>
  </Sample>

  <Sample Name="background" InputFile="config/model/bkg_:category:.xml"
    ImportSyst=":self:" MultiplyLumi="false">
    <NormFactor Name="nbkg_:category:[100,0,100000]"/>
  </Sample>
</Channel>
```

### Data node attributes

| Attribute | Description |
|---|---|
| `InputFile` | Data file path (text, ROOT ntuple, or histogram) |
| `FileType` | `ascii` (default), `root`, or `histogram` |
| `TreeName` | TTree name (ROOT ntuple only) |
| `VarName` | Branch name (ROOT ntuple only) |
| `HistName` | Histogram name (histogram mode only) |
| `Observable` | `name:[lo,hi]` — name and range of observable |
| `Binning` | Number of bins for Asimov and pseudo-binned dataset |
| `InjectGhost` | `true`: inject weight-1e-9 ghost events per empty bin |
| `NumData` | Number of observed events (counting experiments only) |
| `BlindRange` | Range to veto, e.g. `120,130` |

Choose fine enough `Binning` — typically 10× smaller than detector resolution.
The pseudo-binned dataset introduces bias if bins are too coarse.

### Systematic node attributes

| Attribute | Description |
|---|---|
| `Name` | Nuisance parameter name (same name = correlated across categories) |
| `Constr` | Constraint type: `gaus`, `logn`, `asym`, `dfd` |
| `CentralValue` | Nominal response value (usually `1`; use `0` for additive) |
| `Mag` | Uncertainty magnitude; for `asym`: `upper,lower` |
| `WhereTo` | `yield` (auto-applied) or `shape` (user must place `response::`) |
| `Process` | Group name for routing to specific samples via `ImportSyst` |

**Constraint types and response functions:**

| Type | Response function |
|---|---|
| `gaus` | `CentralValue + NP × Mag` |
| `logn` | `(1 + Mag/CentralValue)^NP` |
| `asym` | Polynomial interp within ±1σ, log-normal extrapolation outside |
| `dfd` | Double-Fermi-Dirac box (for ill-defined uncertainties) |

Signs in `Mag` matter — always follow the sign convention of the upstream tool.
For `asym`, only the sign of the upper uncertainty is used.

### Sample node attributes

| Attribute | Description |
|---|---|
| `Name` | Process name (unique within category) |
| `InputFile` | Path to pdf-level XML card |
| `ImportSyst` | Comma-separated common systematic groups; `:common:` = all ungrouped; `:self:` = none |
| `MultiplyLumi` | Whether to multiply `Lumi` to yield |
| `SharePdf` | All processes with the same value share a single PDF |
| `Norm`, `XSection`, `BR`, etc. | Pre-defined constant scale factors on yield |

### NormFactor and ShapeFactor

- `NormFactor`: multiplied automatically to process yield.
- `ShapeFactor`: available as a building block but not auto-multiplied; user
  must incorporate it explicitly.

## PDF-Level Card

```xml
<!DOCTYPE Model SYSTEM 'AnaWSBuilder.dtd'>
<Model Type="UserDef">
  <Item Name="mu_CB[125.09]"/>
  <Item Name="sigma_CB[1.7]"/>
  <Item Name="prod::mu_smeared(mu_CB, response::ATLAS_EG_SCALE_ALL)"/>
  <Item Name="prod::sigma_smeared(sigma_CB, response::ATLAS_EG_RESOLUTION_ALL)"/>
  <ModelItem Name="RooTwoSidedCBShape::signal(:observable:,
    mu_smeared, sigma_smeared, alphaCBLo[1.9], nCBLo[3.4],
    alphaCBHi[1.9], nCBHi[3.8])"/>
</Model>
```

For an externally provided PDF (e.g. from HistFactory):

```xml
<Model Type="External" Input="bkg.root" WSName="combined"
  ModelName="channel_model" ObservableName="obs_x_channel"/>
```

Keep observable name consistent with HistFactory when importing external PDFs.

## XML Keywords

| Keyword | Meaning |
|---|---|
| `response::<NP>` | Response function for NP (in same domain) |
| `:category:` | Replaced by current category name |
| `:observable:` | Observable name of current category |
| `:process:` | Name of current Sample |
| `:common:` | All ungrouped common systematics |
| `:self:` | Only process-specific systematics; suppresses `:common:` |
| `:lt:` `:le:` `:gt:` `:ge:` | `<` `<=` `>` `>=` (XML-safe math symbols) |
| `:and:` `:or:` | Logic operators for ntuple cuts |

`RooFormulaVar` must use indexed syntax `@0, @1, ...` — never variable names
(renaming during workspace creation breaks name-based references).

## Counting Experiments

```xml
<Channel Name="sr" Type="counting" Lumi="20.3">
  <Data NumData="9" Observable="obs_sr[0,1]"/>
  <Sample Name="signal" Norm="0.5" ImportSyst=":common:" SharePdf="counting">
  </Sample>
</Channel>
```

- `Type="counting"` creates a `RooUniform` PDF per process.
- `Binning` is always 1 and is ignored if provided.
- `NumData` attribute sets event count directly without a data file.

## Blinded Analysis

```xml
<!-- Top-level: enable blinding -->
<Combination ... Blind="true">

<!-- Category-level: specify blinded range -->
<Data ... BlindRange="120,130"/>
```

Events in `BlindRange` are vetoed. Side-band fits use:

```cpp
pdf->createNLL(*data, ..., Range("SBLo,SBHi"), SplitRange())
```

Remove `SBLo` or `SBHi` if the blinded range touches the observable boundary.

## Gotchas

- **`AnaWSBuilder.dtd` location**: must be in every folder containing XML
  cards — copy or symlink (`ln -s`) from the xmlAnaWSBuilder repo `dtd/`
  directory.
- **Fine binning is critical**: pseudo-binned and Asimov datasets are biased
  when bins are coarse; use ~10× finer than detector resolution.
- **Indexed proxies in formulas**: `RooFormulaVar` must use `@0, @1, ...`
  because variables are renamed during workspace construction.
- **`matchglob` + `reset`**: always call `reset` at the end of any action
  list containing `matchglob`, otherwise global observable values are altered
  in the final workspace.
- **ResponseFunction custom class**: all workspaces produced by xmlAnaWSBuilder
  contain the `ResponseFunction` class (available in `RooFitExtensions`);
  downstream tools must have `RooFitExtensions` on `LD_LIBRARY_PATH`.
- **External HistFactory PDFs**: keep the observable name identical to the
  HistFactory one; renaming it breaks the binned model.

## Interop

- **workspaceCombiner**: consumes xmlAnaWSBuilder output for multi-channel
  combinations; observable unique-naming convention is required.
- **quickFit**: recommended fitting tool for workspaces created by
  xmlAnaWSBuilder.
- **StatAnalysis**: `XMLReader` is available after
  `asetup StatAnalysis,0.7,latest`.

## Support

Contact: xmlanawsbuilder-user@cern.ch

## Docs

https://gitlab.cern.ch/atlas-hgam-sw/xmlAnaWSBuilder
