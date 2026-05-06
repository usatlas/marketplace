# HistFitter Systematic Types — Deep Reference

Read this reference when choosing a systematic method, debugging unexpected
normalization behavior, or understanding how HistFitter internally constructs
systematic variations.

## Table of Contents

- [Constructor](#constructor)
- [Type parameter](#type-parameter)
- [Complete method reference](#complete-method-reference)
- [Choosing a method — decision flowchart](#choosing-a-method--decision-flowchart)
- [Normalized systematics internals](#normalized-systematics-internals)
- [One-sided and envelope variants](#one-sided-and-envelope-variants)
- [Pruning and smoothing](#pruning-and-smoothing)
- [Constraint terms](#constraint-terms)
- [Common mistakes](#common-mistakes)

## Constructor

```python
from systematic import Systematic

syst = Systematic(name, nominal, high, low, type, method, constraint="Gaussian")
```

| Argument     | Description                                                    |
| ------------ | -------------------------------------------------------------- |
| `name`       | Unique name for the systematic (becomes NP `alpha_<name>`)     |
| `nominal`    | Tree suffix or weight tuple for the nominal                    |
| `high`       | Tree suffix or weight tuple for +1σ (or float for user type)   |
| `low`        | Tree suffix or weight tuple for −1σ (or float for user type)   |
| `type`       | `"tree"`, `"weight"`, or `"user"`                              |
| `method`     | One of the allowed methods (see table below)                   |
| `constraint` | `"Gaussian"` (default) or `"Poisson"` (only for shapeSys/Stat) |

## Type parameter

| Type       | `nominal` / `high` / `low`                         | When to use                                |
| ---------- | -------------------------------------------------- | ------------------------------------------ |
| `"tree"`   | TTree name suffixes (strings)                      | Separate TTrees per variation              |
| `"weight"` | Tuples of weight branch names                      | Same TTree, different event weights        |
| `"user"`   | Floats (overall) or lists of per-bin scale factors | No TTrees — user provides numbers directly |

**Tree example:**

```python
jes = Systematic("JES", "_NoSys", "_JES__1up", "_JES__1down",
                 "tree", "histoSys")
```

**Weight example:**

```python
btagSF = Systematic("BTag", ("genWeight", "btagSF"),
                    ("genWeight", "btagSF_up"),
                    ("genWeight", "btagSF_down"),
                    "weight", "overallSys")
```

**User example (overall):**

```python
lumiSys = Systematic("Lumi", configMgr.weights,
                     1.017, 0.983, "user", "userOverallSys")
```

**User example (per-bin shape):**

```python
shapeUp = Systematic("MyShape", configMgr.weights,
                     [1.1, 1.0, 0.95], [0.9, 1.0, 1.05],
                     "user", "userHistoSys")
```

## Complete method reference

The `allowedSys` list in HistFitter source defines all valid methods:

| Method                           | HistFactory mapping       | Shape? | Norm? | Normalized to CRs? |
| -------------------------------- | ------------------------- | ------ | ----- | ------------------ |
| `overallSys`                     | OverallSys                | No     | Yes   | No                 |
| `histoSys`                       | HistoSys                  | Yes    | Yes   | No                 |
| `normHistoSys`                   | HistoSys (renormalized)   | Yes    | No    | Yes                |
| `overallHistoSys`                | OverallSys + HistoSys     | Yes    | Yes   | No                 |
| `overallNormHistoSys`            | OverallSys + HistoSys     | Yes    | Yes   | Yes                |
| `overallNormSys`                 | OverallSys (renormalized) | No     | Yes   | Yes                |
| `shapeSys`                       | ShapeSys                  | Yes    | No    | No                 |
| `shapeStat`                      | ShapeSys (per-sample)     | Yes    | No    | No                 |
| `userOverallSys`                 | OverallSys                | No     | Yes   | No                 |
| `userHistoSys`                   | HistoSys                  | Yes    | Yes   | No                 |
| `userNormHistoSys`               | HistoSys (renormalized)   | Yes    | No    | Yes                |
| `histoSysOneSide`                | HistoSys (one-sided)      | Yes    | Yes   | No                 |
| `histoSysOneSideSym`             | HistoSys (sym one-sided)  | Yes    | Yes   | No                 |
| `normHistoSysOneSide`            | HistoSys (one-sided)      | Yes    | No    | Yes                |
| `normHistoSysOneSideSym`         | HistoSys (sym one-sided)  | Yes    | No    | Yes                |
| `overallNormHistoSysOneSide`     | OverallSys + HistoSys     | Yes    | Yes   | Yes                |
| `overallNormHistoSysOneSideSym`  | OverallSys + HistoSys     | Yes    | Yes   | Yes                |
| `normHistoSysEnvelopeSym`        | HistoSys (envelope)       | Yes    | No    | Yes                |
| `histoSysEnvelopeSym`            | HistoSys (envelope)       | Yes    | Yes   | No                 |
| `overallNormHistoSysEnvelopeSym` | OverallSys + HistoSys     | Yes    | Yes   | Yes                |
| `histoSysEnvelope`               | HistoSys (multi-var env)  | Yes    | Yes   | No                 |

### Method families

- **`overallSys` / `userOverallSys`**: Pure normalization. No bin-by-bin shape
  effect. The simplest systematic — a single scale factor up/down.
- **`histoSys` / `userHistoSys`**: Full shape+norm. The variation histograms
  enter HistFactory directly. Both shape and normalization effects are
  preserved.
- **`normHistoSys` / `userNormHistoSys`**: Shape only, normalized to control
  regions. The variation histograms are rescaled so their integral matches the
  nominal in the normalization regions. The normalization component cancels in
  the transfer factor.
- **`overallHistoSys`**: Factorized shape+norm without CR normalization. The
  shape is extracted (integrals equalized), and the residual normalization
  enters as an `overallSys`.
- **`overallNormHistoSys`**: The most common method for backgrounds with norm
  factors. Like `overallHistoSys` but the shape is additionally normalized to
  the control regions. The normalization is factorized out as an `overallSys`.
- **`shapeSys`**: Bin-by-bin uncorrelated uncertainties. One NP per bin, shared
  across samples (can merge samples with `syst.mergeSamples(sampleList)`).
  Constraint can be `"Gaussian"` or `"Poisson"`.
- **`shapeStat`**: Like `shapeSys` but for MC statistical uncertainty of a
  single sample. Uses the bin errors from the nominal histogram. Supports a
  `statErrorThreshold` to ignore bins with small relative errors.

## Choosing a method — decision flowchart

```
Is it a pure normalization uncertainty (no shape)?
├── Yes → Does the sample have normRegions/normFactor?
│   ├── Yes → overallNormSys (normalized to CRs)
│   └── No  → overallSys or userOverallSys
└── No (has shape component)
    ├── Is it MC statistical uncertainty?
    │   └── Yes → shapeStat (per sample) or shapeSys (merged)
    ├── Does the sample have normRegions/normFactor?
    │   ├── Yes → Do you want factorized norm + shape?
    │   │   ├── Yes → overallNormHistoSys (most common)
    │   │   └── No  → normHistoSys (shape only, norm cancels)
    │   └── No → histoSys or overallHistoSys
    └── Is it a user-defined variation (no TTrees)?
        └── Yes → userHistoSys or userNormHistoSys
```

**Rule of thumb**: If a background has `setNormFactor()` and `setNormRegions()`,
use `overallNormHistoSys` for its detector systematics. This preserves the
transfer factor cancellation while properly tracking the residual normalization
effect.

## Normalized systematics internals

When a "Norm" method is used, HistFitter performs these steps internally:

1. **Build variation histograms** in all regions (SR + CRs)
2. **Compute normalization integral** in the norm regions:
   `N_high = sum(high_histo in norm_regions)`
3. **Compute transfer factor ratio**: `TF_high = N_high / N_nominal`
4. **Rescale** the variation histogram: `high_normalized = high / TF_high`

For `overallNormHistoSys`, the factorized normalization is additionally
extracted:

5. **Compute shape integral ratio**:
   `S_high = integral(high_normalized) / integral(nominal)` in the channel of
   interest
6. **Rescale again**: `high_shape = high_normalized / S_high`
7. **Store** `S_high` as an `overallSys` entry

This decomposition means the shape part has unit normalization relative to the
nominal, and the normalization part is captured by a separate overall factor.
The advantage is that during the fit, the normalization factor `mu_BKG` absorbs
the normalization component in the CRs, and only the residual normalization (the
overall factor) and shape migrate to the SR.

**Requirements for normalized types:**

```python
sample.setNormFactor("mu_BKG", 1., 0., 5.)
sample.setNormRegions([("CR1", "nJet"), ("CR2", "met")])
```

Without `setNormRegions()`, HistFitter falls back to using all non-validation
channels and logs an error. Without a norm factor, the normalization uncertainty
is lost because there is no free parameter to absorb it.

## One-sided and envelope variants

### One-sided systematics

For systematics where only one variation exists (e.g., an ISR/FSR variation with
only "more radiation"):

- `histoSysOneSide`: Only `high` is used; `low` is set to nominal
- `histoSysOneSideSym`: `high` is used; `low` is constructed by reflecting
  around the nominal: `low = 2 * nominal - high`

The same `OneSide` / `OneSideSym` suffixes apply to `normHistoSys` and
`overallNormHistoSys`.

### Envelope systematics

For systematics with multiple alternative variations (e.g., PDF sets):

- `histoSysEnvelopeSym`: Takes max(up variations) as high, min(down variations)
  as low, then symmetrizes
- `histoSysEnvelope`: Takes an arbitrary number of weight variations and
  constructs high/low from the bin-by-bin max/min across all variations. The
  `low` parameter encodes the number of weight variations.
- `normHistoSysEnvelopeSym`, `overallNormHistoSysEnvelopeSym`: Same as above but
  with CR normalization

## Pruning and smoothing

### Pruning configuration

```python
configMgr.prun = True
configMgr.prunThreshold = 0.01   # relative threshold (1%)
configMgr.prunMethod = 2         # 1 = chi2 test, 2 = bin-by-bin
```

### How pruning works

HistFitter checks each systematic in each sample/region:

**Method 1 (chi2):** Performs a `Chi2Test("WW OF UF")` between the nominal and
varied histograms. If the p-value is above 0.05, the shape is considered
compatible with nominal and the shape component is removed.

**Method 2 (bin-by-bin):** For each bin, checks whether
`|varied - nominal| > threshold * nominal`. If no bin exceeds the threshold, the
systematic is pruned.

For factorized systematics (`overallNormHistoSys`, `overallHistoSys`), shape and
normalization are pruned independently:

- Shape pruned if chi2/bin-by-bin test passes
- Normalization pruned if `max(|high-1|, |1-low|) < prunThreshold`

Pruned systematics are tracked in `sample.systListOverallPruned` and
`sample.systListHistoPruned`.

### Validation

After enabling pruning, verify that the total systematic uncertainty on yields
is not significantly changed. Compare `SysTable.py` output with and without
pruning.

## Constraint terms

By default, all NPs have Gaussian constraints. Override per-parameter via
`Measurement`:

```python
meas.addConstraintTerm("alpha_JES", "Gaussian")      # default
meas.addConstraintTerm("gamma_stat_SR_bin_0", "Poisson")
meas.addConstraintTerm("alpha_ISR", "LogNormal", 0.1) # with relUnc
meas.addConstraintTerm("mu_BKG", "Uniform")           # flat prior
meas.addConstraintTerm("mu_BKG", "NoConstraint")      # no constraint
```

`shapeSys` and `shapeStat` accept their constraint type in the `Systematic`
constructor:

```python
mcstat = Systematic("mcstat", "_NoSys", "_NoSys", "_NoSys",
                    "tree", "shapeStat", "Poisson")
```

## Common mistakes

| Mistake                                                  | Consequence                                                    | Fix                                                         |
| -------------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------- |
| Using `normHistoSys` without `setNormRegions()`          | Error; falls back to all non-VR channels                       | Set norm regions explicitly                                 |
| Using `overallNormHistoSys` without a norm factor        | Normalization uncertainty silently lost                        | Add `setNormFactor()` to the sample                         |
| Using `histoSys` on a sample with normFactor+normRegions | Full (un-normalized) variation enters; TF cancellation is lost | Switch to `overallNormHistoSys` or `normHistoSys`           |
| Setting `high == low` in `overallSys`                    | HistFactory silently cancels the systematic (error = 0)        | HistFitter auto-symmetrizes with a warning; fix your inputs |
| Using `shapeSys` with `"Poisson"` on negative yields     | Fit failure (Poisson requires positive)                        | Use `"Gaussian"` or fix negative bins                       |
| Pruning threshold too aggressive                         | Significant systematics removed                                | Lower threshold; compare SysTable before/after              |
| Mixing `"tree"` type with user-defined floats            | Constructor error                                              | Use `"user"` type for numeric inputs                        |
