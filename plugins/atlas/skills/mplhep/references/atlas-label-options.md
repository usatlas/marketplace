# ATLAS Label Options Reference

## mh.atlas.label() Full Parameter Reference

```python
mh.atlas.label(
    status,                   # "Internal", "Preliminary", "Simulation", "Work in Progress", or ""
    data=True,               # whether real data is shown (affects luminosity line)
    lumi=150,                # integrated luminosity in fb⁻¹
    com=13,                  # center-of-mass energy in TeV
    year="2023",             # data-taking year (optional)
    lumi_format="{0:.0f}",   # luminosity number format (ATLAS default: integer)
    loc=0,                   # label position (0--4)
    ax=ax,                   # matplotlib axis (defaults to current)
    llabel="...",            # custom left label (overrides status)
    rlabel="...",            # custom right label (overrides lumi/com)
    supp="arXiv:2024.12345", # supplementary material reference
)
```

## Label Positions (loc parameter)

| loc | Description                                                   |
| --- | ------------------------------------------------------------- |
| 0   | Above axes (default) -- left-aligned, outside the plot frame  |
| 1   | Top-left corner, single line -- compact inline format         |
| 2   | Top-left corner, multiline -- stacked label lines             |
| 3   | Split layout -- experiment name above, secondary text inside  |
| 4   | ATLAS-specific -- luminosity placed below the main label      |

### Position Examples

```python
# Default (above axes)
mh.atlas.label("Preliminary", data=True, lumi=150, com=13, loc=0)

# Compact single-line in corner
mh.atlas.label("Preliminary", data=True, lumi=150, com=13, loc=1)

# Multiline in corner
mh.atlas.label("Preliminary", data=True, lumi=150, com=13, loc=2)

# Split: "ATLAS" above axes, rest in corner
mh.atlas.label("Preliminary", data=True, lumi=150, com=13, loc=3)

# ATLAS-specific layout with luminosity below
mh.atlas.label("Preliminary", data=True, lumi=150, com=13, loc=4)
```

## Common ATLAS Label Configurations

### Standard Internal Plot

```python
mh.atlas.label("Internal", data=True, lumi=150, com=13)
mh.mpl_magic(soft_fail=True)
```

### Conference Preliminary

```python
mh.atlas.label(
    "Preliminary",
    data=True,
    year="2023",
    lumi=150,
    com=13,
    lumi_format="{0:.0f}",
)
mh.mpl_magic(soft_fail=True)
```

### Published Paper (No Status Text)

```python
mh.atlas.label("", data=True, lumi=140, com=13)
mh.mpl_magic(soft_fail=True)
```

### Simulation-Only

```python
mh.atlas.label("Simulation", data=False, com=13)
mh.mpl_magic(soft_fail=True)
```

### Fully Custom Labels

Override the default layout with `llabel` and `rlabel`:

```python
mh.atlas.label(llabel="Left Label", rlabel="Right Label")
mh.mpl_magic(soft_fail=True)
```

### With Supplementary Material Reference

```python
mh.atlas.label(
    "Preliminary",
    data=True,
    lumi=150,
    com=13,
    supp="arXiv:2024.12345",
)
mh.mpl_magic(soft_fail=True)
```

## Text Placement Utilities

### mh.add_text()

Place arbitrary text at named locations on the axis:

```python
txt_obj = mh.add_text("Custom annotation", loc="upper left", ax=ax)
```

**loc string options**: `"upper left"`, `"upper right"`, `"lower left"`,
`"lower right"`, `"over left"`, `"over right"`, `"under left"`,
`"under right"`

Alternative positioning via `x` and `y` keyword arguments:

- **x**: `"left_in"`, `"left"`, `"left_out"`, `"right_in"`, `"right"`,
  `"right_out"`
- **y**: `"top_in"`, `"top_out"`, `"bottom_in"`, `"bottom_out"`

```python
mh.add_text("Custom text", x="right_in", y="top_in", ax=ax)
```

### mh.append_text()

Append text relative to an existing text object:

```python
txt = mh.add_text("Primary text", loc="upper right", ax=ax)
mh.append_text("Secondary info", txt, loc="below")
```

**Relative positions**: `"above"`, `"below"`, `"left"`, `"right"`

## Saving Label Variations with mh.savelabels()

Automatically generate multiple versions of a plot with different label text:

```python
# Produces: plot.pdf, plot_pas.png, plot_supp.png, plot_wip.png
mh.savelabels("plot.pdf")

# Custom variations
mh.savelabels("plot", labels=[("Internal", "internal.pdf"), ("", "final.pdf")])
```

## Style Customization

### Inspect ATLAS Style Dictionary

```python
import mplhep as mh
print(mh.style.ATLAS)
```

### Extend with Custom rcParams

```python
mh.style.use([mh.style.ATLAS, {"font.size": 14, "axes.linewidth": 1.5}])
```

### Reset to Default

```python
mh.style.use()
```
