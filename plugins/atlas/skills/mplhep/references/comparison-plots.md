# Comparison Plots Reference

## Comparison Types

All comparison functions in `mh.comp` accept a `comparison` parameter with the
following options:

| Type                  | Formula                                                                  |
| --------------------- | ------------------------------------------------------------------------ |
| `ratio`               | h1 / h2                                                                  |
| `split_ratio`         | h1 / h2 (uncertainties of h1 and h2 shown separately)                    |
| `pull`                | (h1 - h2) / sqrt(sigma_h1^2 + sigma_h2^2)                                |
| `difference`          | h1 - h2                                                                  |
| `relative_difference` | (h1 - h2) / h2                                                           |
| `asymmetry`           | (h1 - h2) / (h1 + h2)                                                    |
| `efficiency`          | h1 / h2 (with proper uncertainty propagation from arXiv:physics/0701199) |

## mh.comp.hists() -- Two-Histogram Comparison

Compare two histograms and produce a main plot with a comparison panel below:

```python
fig, ax_main, ax_comp = mh.comp.hists(
    h1,
    h2,
    comparison="ratio",       # any comparison type from the table above
    xlabel="Observable [GeV]",
    ylabel="Events",
    h1_label="Data",
    h2_label="MC",
)
mh.atlas.label("Internal", data=True, ax=ax_main)
mh.mpl_magic(soft_fail=True)
```

Returns a tuple of `(fig, ax_main, ax_comp)`.

## mh.comp.data_model() -- Data vs Model

Compare data to a model consisting of stacked and/or unstacked components:

### Stacked Histogram Components

```python
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

### Mixed Stacked and Unstacked

```python
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2],
    stacked_labels=["Bkg 1", "Bkg 2"],
    stacked_colors=["grey", "lightblue"],
    unstacked_components=[h_signal],
    unstacked_labels=["Signal"],
    unstacked_colors=["red"],
    xlabel="Observable [GeV]",
    ylabel="Events",
)
mh.atlas.label("Internal", data=True, lumi=150, ax=ax_main)
mh.mpl_magic(soft_fail=True)
```

### Function Components

Components can be callable functions instead of histograms:

```python
import scipy.stats

def f_signal(x):
    return 200 * scipy.stats.norm.pdf(x, loc=0.5, scale=3)

def f_bkg(x):
    return 500 * scipy.stats.norm.pdf(x, loc=-1.5, scale=4)

fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[f_bkg, f_signal],
    stacked_labels=["Background", "Signal"],
    xlabel="Observable [GeV]",
    ylabel="Events",
)
```

### Customizing the Comparison

```python
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2, h_signal],
    stacked_labels=["Bkg 1", "Bkg 2", "Signal"],
    comparison="pull",          # default is "split_ratio"
    model_uncertainty=False,    # remove MC uncertainty band
    xlabel="Observable [GeV]",
    ylabel="Events",
)
```

### Showing Only One Panel

```python
# Main plot only (no comparison panel)
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2],
    stacked_labels=["Bkg 1", "Bkg 2"],
    plot_only="ax_main",
    xlabel="Observable [GeV]",
    ylabel="Events",
)

# Comparison panel only
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2],
    stacked_labels=["Bkg 1", "Bkg 2"],
    plot_only="ax_comparison",
    xlabel="Observable [GeV]",
    ylabel="Events",
)
```

### Model Sum Line

```python
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2],
    stacked_labels=["Bkg 1", "Bkg 2"],
    model_sum_kwargs={"show": True, "label": "Total Model", "color": "violet"},
    xlabel="Observable [GeV]",
    ylabel="Events",
)
```

## mh.comp.comparison() -- Standalone Comparison Panel

Plot only the comparison panel without a main plot:

```python
fig, ax = plt.subplots()
mh.comp.comparison(
    h1,
    h2,
    comparison="ratio",
    xlabel="Observable [GeV]",
    h1_label="Data",
    h2_label="MC",
    ax=ax,
)
```

## mh.comp.get_comparison() -- Numerical Values

Get comparison values without plotting:

```python
values, lower_unc, upper_unc = mh.comp.get_comparison(
    h1, h2, comparison="ratio"
)
```

## Blinding in Comparisons

The `blind` parameter hides regions in both the main plot and the comparison
panel.

### Blinding Syntax

| Format                       | Description                     |
| ---------------------------- | ------------------------------- |
| `(-1.0, 1.0)`                | Value-based tuple               |
| `"-1j:1j"`                   | String with j suffix for values |
| `loc[-1.0:1.0]`              | loc slice notation              |
| `19`                         | Single bin index                |
| `"15:25"`                    | Range of bin indices            |
| `[18, 19, 20, 21, 22]`       | List of specific bin indices    |
| `[(-2.5, -1.5), (1.5, 2.5)]` | Multiple value-based regions    |
| `"5:1j"`                     | Mixed: index start, value end   |

### Blinding in comp.hists()

```python
fig, ax_main, ax_comp = mh.comp.hists(
    h1, h2,
    blind=(-1.0, 1.0),
    comparison="ratio",
    xlabel="Observable [GeV]",
    ylabel="Events",
    h1_label="Data",
    h2_label="MC",
)
```

### Blinding in comp.data_model()

```python
fig, ax_main, ax_comp = mh.comp.data_model(
    data_hist=h_data,
    stacked_components=[h_bkg1, h_bkg2],
    stacked_labels=["Bkg 1", "Bkg 2"],
    blind=(120, 130),
    xlabel=r"$m_{H}$ [GeV]",
    ylabel="Events",
)
```

## Custom Multi-Panel Layouts

### Using mh.subplots()

`mh.subplots()` creates multi-row figures with automatic sizing and spacing:

```python
fig, axes = mh.subplots(nrows=3)
# axes[0]: main plot
# axes[1], axes[2]: comparison panels
```

### Manual Multi-Panel Example

```python
fig, axes = mh.subplots(nrows=3)

# Main plot
mh.histplot(h_train_bkg, ax=axes[0], histtype="step", label="Bkg (train)")
mh.histplot(h_train_sig, ax=axes[0], histtype="step", label="Sig (train)")
mh.histplot(h_test_bkg, ax=axes[0], histtype="errorbar", label="Bkg (test)")
mh.histplot(h_test_sig, ax=axes[0], histtype="errorbar", label="Sig (test)")
axes[0].legend()

# Ratio panel for background
mh.comp.comparison(
    h_train_bkg, h_test_bkg,
    ax=axes[1],
    comparison="ratio",
    h1_label="Train",
    h2_label="Test",
)
axes[1].set_ylabel("Ratio")

# Pull panel for signal
mh.comp.comparison(
    h_train_sig, h_test_sig,
    ax=axes[2],
    comparison="pull",
    h1_label="Train",
    h2_label="Test",
)
axes[2].set_ylabel("Pull")
axes[-1].set_xlabel("BDT Score")

fig.align_ylabels()
mh.atlas.label("Simulation", data=False, ax=axes[0])
mh.mpl_magic(soft_fail=True)
```

## Histogram Types for histplot

| histtype     | Description                                          |
| ------------ | ---------------------------------------------------- |
| `"step"`     | Step line histogram (default)                        |
| `"fill"`     | Filled histogram                                     |
| `"errorbar"` | Data points with error bars                          |
| `"band"`     | Uncertainty band (useful for visualizing errors)     |
| `"bar"`      | Side-by-side bars when multiple histograms are given |
| `"barstep"`  | Side-by-side step bars for multiple histograms       |

## Normalization Options

| Parameter       | Effect                               |
| --------------- | ------------------------------------ |
| (default)       | Raw event counts                     |
| `density=True`  | Normalized so integral equals 1      |
| `binwnorm=True` | Divided by bin width (Events / unit) |

## Error Bar Control

| Parameter            | Effect                                      |
| -------------------- | ------------------------------------------- |
| `yerr=True`          | Automatic errors (Poisson or from variance) |
| `yerr=custom_array`  | Explicit error values                       |
| `w2method="sqrt"`    | sqrt of sum of weights squared              |
| `w2method="poisson"` | Poisson interval                            |
| `w2method=callable`  | Custom function `f(weights, variances)`     |

## Stacking and Sorting

```python
mh.histplot(
    [h1, h2, h3],
    stack=True,           # stack histograms
    sort="yield",         # sort by total yield (also: "label", "l_r")
    label=["A", "B", "C"],
    ax=ax,
)
```
