# xmlAnaWSBuilder XML Schema Reference

Read this reference when looking up a specific XML node attribute, choosing an
Asimov action keyword, or picking a systematic constraint type while writing
xmlAnaWSBuilder XML cards.

## Table of Contents

- [Asimov action keywords](#asimov-action-keywords)
- [Data node attributes](#data-node-attributes)
- [Systematic node attributes](#systematic-node-attributes)
- [Sample node attributes](#sample-node-attributes)
- [NormFactor and ShapeFactor](#normfactor-and-shapefactor)

## Asimov action keywords

Used in the top-level card's `<Asimov Action="...">` attribute (colon-separated
list, e.g. `Action="fixsyst:fit:genasimov:float:savesnapshot"`):

| Keyword           | Meaning                                                         |
| ----------------- | --------------------------------------------------------------- |
| `fit`             | Maximum likelihood fit                                          |
| `genasimov`       | Generate Asimov dataset (once per line)                         |
| `savesnapshot`    | Save parameter snapshot (once per line)                         |
| `matchglob`       | Match global observables to NP values; always pair with `reset` |
| `reset`           | Reset to state before current action list                       |
| `raw`             | Reset to state before any actions                               |
| `fixsyst`         | Fix all constrained NPs                                         |
| `fixall`          | Fix all NPs                                                     |
| `float`           | Float NPs fixed by `fixsyst` or `Setup`                         |
| `<snapshot name>` | Load a saved snapshot                                           |

## Data node attributes

`<Data>` lives inside a category-level `<Channel>` card and points to the
observed dataset:

| Attribute     | Description                                           |
| ------------- | ----------------------------------------------------- |
| `InputFile`   | Data file path (text, ROOT ntuple, or histogram)      |
| `FileType`    | `ascii` (default), `root`, or `histogram`             |
| `TreeName`    | TTree name (ROOT ntuple only)                         |
| `VarName`     | Branch name (ROOT ntuple only)                        |
| `HistName`    | Histogram name (histogram mode only)                  |
| `Observable`  | `name:[lo,hi]` — name and range of observable         |
| `Binning`     | Number of bins for Asimov and pseudo-binned dataset   |
| `InjectGhost` | `true`: inject weight-1e-9 ghost events per empty bin |
| `NumData`     | Number of observed events (counting experiments only) |
| `BlindRange`  | Range to veto, e.g. `120,130`                         |

Choose fine enough `Binning` — typically 10× smaller than detector resolution.
The pseudo-binned dataset introduces bias if bins are too coarse.

## Systematic node attributes

`<Systematic>` lives inside a category-level `<Channel>` card and defines a
common systematic that samples opt into via `ImportSyst`:

| Attribute      | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `Name`         | Nuisance parameter name (same name = correlated across categories) |
| `Constr`       | Constraint type: `gaus`, `logn`, `asym`, `dfd`                     |
| `CentralValue` | Nominal response value (usually `1`; use `0` for additive)         |
| `Mag`          | Uncertainty magnitude; for `asym`: `upper,lower`                   |
| `WhereTo`      | `yield` (auto-applied) or `shape` (user must place `response::`)   |
| `Process`      | Group name for routing to specific samples via `ImportSyst`        |

**Constraint types and response functions:**

| Type   | Response function                                              |
| ------ | -------------------------------------------------------------- |
| `gaus` | `CentralValue + NP × Mag`                                      |
| `logn` | `(1 + Mag/CentralValue)^NP`                                    |
| `asym` | Polynomial interp within ±1σ, log-normal extrapolation outside |
| `dfd`  | Double-Fermi-Dirac box (for ill-defined uncertainties)         |

Signs in `Mag` matter — always follow the sign convention of the upstream tool.
For `asym`, only the sign of the upper uncertainty is used.

## Sample node attributes

`<Sample>` lives inside a category-level `<Channel>` card and represents one
physics process:

| Attribute                      | Description                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------- |
| `Name`                         | Process name (unique within category)                                                 |
| `InputFile`                    | Path to pdf-level XML card                                                            |
| `ImportSyst`                   | Comma-separated common systematic groups; `:common:` = all ungrouped; `:self:` = none |
| `MultiplyLumi`                 | Whether to multiply `Lumi` to yield                                                   |
| `SharePdf`                     | All processes with the same value share a single PDF                                  |
| `Norm`, `XSection`, `BR`, etc. | Pre-defined constant scale factors on yield                                           |

## NormFactor and ShapeFactor

- `NormFactor`: multiplied automatically to process yield.
- `ShapeFactor`: available as a building block but not auto-multiplied; user
  must incorporate it explicitly.
