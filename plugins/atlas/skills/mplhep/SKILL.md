---
name: mplhep
description: >-
  Use when creating ATLAS publication-quality plots with matplotlib using mplhep:
  applying the ATLAS experiment style, placing ATLAS labels (Internal,
  Preliminary, Simulation), plotting 1D or 2D histograms from hist/uproot/numpy,
  making data/MC comparison plots with ratio panels, using mplhep comparison
  functions (ratio, pull, split_ratio), or customizing ATLAS label positions and
  luminosity text on matplotlib figures.
---

# mplhep -- Matplotlib for HEP

## Overview

`mplhep` is the scikit-hep matplotlib wrapper for publication-quality HEP plots.
It provides experiment-specific styles (ATLAS, CMS, LHCb, ALICE, DUNE),
histogram plotting functions that accept `hist.Hist`, `uproot.TH1`, and numpy
arrays via the Unified Histogram Interface (UHI), and dedicated comparison
plotters for data/MC ratio panels. For ATLAS work, `mplhep` replaces the ROOT
`atlasrootstyle` macros with a pure-Python matplotlib workflow.

## When to Use

- Creating ATLAS publication-quality plots in matplotlib (not ROOT)
- Applying the ATLAS experiment style (`mplhep.style.use("ATLAS")`)
- Placing ATLAS labels (Internal, Preliminary, Simulation) on matplotlib figures
- Plotting prebinned histograms from `hist.Hist`, `uproot.TH1`, or numpy arrays
- Making data/MC comparison plots with ratio, pull, or split-ratio panels
- Customizing ATLAS label positions, luminosity text, and center-of-mass energy
- Using `mplhep.comp.data_model()` for stacked background + signal + data plots

## Key Concepts

| Function / Module         | Purpose                                               |
| ------------------------- | ----------------------------------------------------- |
| `mh.style.use("ATLAS")`  | Apply the ATLAS matplotlib style globally             |
| `mh.atlas.label()`       | Place official ATLAS label with status, lumi, com     |
| `mh.histplot()`          | Plot 1D histograms (step, fill, errorbar, band, bar)  |
| `mh.hist2dplot()`        | Plot 2D histograms with optional colorbar             |
| `mh.comp.hists()`        | Compare two histograms with a ratio/pull panel        |
| `mh.comp.data_model()`   | Data vs stacked MC with comparison panel              |
| `mh.comp.comparison()`   | Standalone comparison panel (no main plot)             |
| `mh.mpl_magic()`         | Auto-fit y-axis for labels and legends                |
| `mh.add_text()`          | Place arbitrary text at named locations                |
| `mh.savelabels()`        | Generate plot variations (Preliminary, Final, WIP)    |
| `mh.subplots()`          | Multi-panel figure with automatic sizing              |

### ATLAS Label Categories

Label text follows ATLAS publication policy (identical to the ROOT
`atlasrootstyle` macros covered by the astyle skill):

| Status text           | Usage                                  |
| --------------------- | -------------------------------------- |
| `""`                  | Approved results in published papers   |
| `"Preliminary"`       | Conference results not yet in a paper  |
| `"Internal"`          | Results not for public distribution    |
| `"Simulation"`        | Simulation-only results (no real data) |
| `"Work in Progress"`  | Early-stage results, not for approval  |

### Supported Input Formats

`mh.histplot()` accepts any UHI-compatible histogram:

- **`hist.Hist`** -- error bars shown automatically when `Weight()` storage is
  used (has `.variances()`)
- **`uproot.TH1`** -- ROOT histograms read via uproot, plotted directly
- **`numpy.histogram` tuple** -- `(values, bin_edges)` from `np.histogram()`
- **Array-like** -- plain list or array of bin heights (bins auto-generated)

## Canonical Patterns

### Minimal ATLAS Histogram

```python
import matplotlib.pyplot as plt
import mplhep as mh
import numpy as np

mh.style.use("ATLAS")

fig, ax = plt.subplots()
mh.histplot(*np.histogram(np.random.normal(0, 1, 1000), bins=40), ax=ax)
mh.atlas.label("Internal", data=False, lumi=150, com=13)
mh.mpl_magic(soft_fail=True)
fig.savefig("plot.pdf")
```

### Plotting a hist.Hist Object

```python
import matplotlib.pyplot as plt
import hist
import mplhep as mh

mh.style.use("ATLAS")

h = hist.Hist(hist.axis.Regular(50, 0, 500, name="pt", label=r"$p_T$ [GeV]"))
h.fill(pt=jet_pts_gev, weight=event_weights)  # user-provided arrays

fig, ax = plt.subplots()
mh.histplot(h, ax=ax, histtype="errorbar", label="Data")
mh.atlas.label("Internal", data=True, lumi=150, com=13)
mh.mpl_magic(soft_fail=True)
```

### Stacked Backgrounds with Data Overlay

```python
mh.style.use("ATLAS")
fig, ax = plt.subplots()

mh.histplot(
    [h_bkg1, h_bkg2, h_signal],
    histtype="fill",
    stack=True,
    label=["Bkg 1", "Bkg 2", "Signal"],
    ax=ax,
)
mh.histplot(h_data, histtype="errorbar", label="Data", ax=ax, color="black")
ax.legend(loc="upper right")
mh.atlas.label("Internal", data=True, lumi=150, com=13)
mh.mpl_magic(soft_fail=True)
```

### Data/MC Comparison with Ratio Panel

```python
mh.style.use("ATLAS")

fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2, h_signal],
    stacked_labels=["Bkg 1", "Bkg 2", "Signal"],
    xlabel=r"$m_{jj}$ [GeV]",
    ylabel="Events",
)
mh.atlas.label("Internal", data=True, lumi=150, ax=ax_main)
mh.mpl_magic(soft_fail=True)
```

The default comparison is `split_ratio`. Other options: `ratio`, `pull`,
`difference`, `relative_difference`, `asymmetry`, `efficiency`.

### Two-Histogram Comparison

```python
fig, ax_main, ax_comp = mh.comp.hists(
    h1, h2,
    comparison="ratio",
    xlabel=r"$m_{jj}$ [GeV]",
    ylabel="Events",
    h1_label="Data",
    h2_label="MC",
)
mh.atlas.label("Internal", data=True, ax=ax_main)
mh.mpl_magic(soft_fail=True)
```

### Blinding a Signal Region

```python
mh.histplot(h_data, ax=ax, blind=(-1.0, 1.0), label="Data")

# Also works in comp functions:
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2],
    stacked_labels=["Bkg 1", "Bkg 2"],
    blind=(120, 130),
)
```

## Gotchas

- **Always call `mh.mpl_magic(soft_fail=True)` after `mh.atlas.label()`**: The
  ATLAS style requires this to auto-fit the y-axis around labels and legends.
  Other experiments (CMS, DUNE) do not need it.
- **Apply style at script top, not per-function**: `mh.style.use("ATLAS")` sets
  global `rcParams`. Call it once before creating any figures.
- **`plt.style.context()` is unreliable**: Due to matplotlib font-handling
  limitations, context managers do not work reliably with mplhep styles. Use
  `mh.style.use()` globally.
- **ATLAS luminosity format defaults to integer**: `lumi_format="{0:.0f}"`, so
  `lumi=140` renders as "140 fb^{-1}". Override with `lumi_format="{0:.1f}"` if
  decimal precision is needed.
- **Automatic error bars with `hist.Hist`**: When a histogram has
  `.variances()` (i.e. `Weight()` storage), `histplot` shows error bars
  automatically. Numpy histogram tuples do not carry variance information.
- **`mh.hist()` does not return UHI objects**: Unlike `mh.histplot()`, the
  convenience wrapper `mh.hist()` runs `np.histogram` internally and cannot be
  used with other mplhep histogram functions.
- **All ATLAS energy/momentum values are in MeV** in the detector/analysis
  framework, but plot axis labels conventionally show GeV or TeV. Divide by 1000
  before filling histograms.
- **Style is a dict**: Access as `mh.style.ATLAS` to inspect or extend
  rcParams. Customize via `mh.style.use([mh.style.ATLAS, {"font.size": 14}])`.

## Interop

- **astyle (ROOT)**: The astyle skill covers the ROOT `atlasrootstyle` macros
  (`SetAtlasStyle`, `ATLASLabel`, `myText`). Use mplhep for matplotlib-based
  ATLAS plots and `atlasrootstyle` for ROOT/PyROOT-based plots. The label
  categories and publication policy rules are identical across both tools.
- **hist**: `mh.histplot()` accepts `hist.Hist` objects natively. Use `hist` for
  histogram creation, slicing, and rebinning; pass directly to mplhep for
  plotting.
- **uproot**: `mh.histplot()` accepts `uproot.TH1` objects directly -- read ROOT
  files with uproot and plot without conversion.
- **coffea**: Coffea processors accumulate `hist.Hist` objects which plot
  directly with mplhep.
- **boost-histogram**: `mh.histplot()` accepts `bh.Histogram` via UHI.
- **Other experiment styles**: mplhep also supports CMS (`mh.style.use("CMS")`),
  LHCb (`mh.style.use("LHCb2")`), ALICE, and DUNE styles with matching label
  functions (`mh.cms.label()`, `mh.lhcb.label()`, etc.).

## Docs

https://mplhep.readthedocs.io/

For detailed reference beyond the upstream docs, consult the bundled files:

- **`references/atlas-label-options.md`** -- Full ATLAS label parameter
  reference, label positions, text placement, and savelabels workflow
- **`references/comparison-plots.md`** -- All comparison types with formulas,
  data/MC patterns, blinding syntax, and custom multi-panel layouts
