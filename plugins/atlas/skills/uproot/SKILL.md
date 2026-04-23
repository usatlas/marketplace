---
name: uproot
description: >-
  Use when reading or writing ROOT files in Python without a ROOT installation:
  opening TTrees with uproot.open, reading branches as awkward or numpy arrays,
  converting to pandas, iterating in batches over large files, writing new ROOT
  files or appending histograms, or diagnosing common uproot errors (key not
  found, cycle numbers, jagged branch shapes).
---

# uproot

## Overview

uproot reads and writes ROOT files in pure Python using NumPy and Awkward Array.
It does not require a ROOT installation and integrates directly with the
Scikit-HEP ecosystem (awkward, hist, vector). The primary use is extracting
TTree or RNTuple data into arrays for analysis; a secondary use is writing ROOT
files containing histograms, TTrees, or RNTuples. RNTuple is the modern
successor to TTree and can represent anything expressible as an Awkward Array,
including nested and variable-length structures.

## When to Use

- Reading ATLAS NTuple output (TopCPToolkit, FastFrames, AnalysisTop) into
  Python
- Inspecting a ROOT file's contents without invoking ROOT or C++
- Batch-iterating over files too large to load into memory at once
- Writing histogram output back to ROOT for TRExFitter or legacy tools
- Bridging ROOT data into the awkward / coffea / hist ecosystem

## Key Concepts

| Concept                                      | Notes                                                                                                                                              |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uproot.open(path)`                          | Opens one file; returns a `ReadOnlyDirectory`                                                                                                      |
| `uproot.open("file.root:tree")`              | Opens file and directly returns the named TTree                                                                                                    |
| `uproot.concatenate(files, filter_name=...)` | Reads multiple files at once into one array                                                                                                        |
| `uproot.iterate(files, ...)`                 | Yields batches (use for large datasets)                                                                                                            |
| `f.classnames()`                             | Maps every key in a directory to its ROOT class name (e.g. `'TTree'`, `'TH1F'`, `'ROOT::RNTuple'`)                                                 |
| `tree.typenames()`                           | Maps branch/field names to C++ types without reading any data                                                                                      |
| `tree.keys()`                                | Lists branch names in the TTree                                                                                                                    |
| `tree["branch"].array()`                     | Returns full branch as an awkward array                                                                                                            |
| `tree.arrays(["b1","b2"])`                   | Returns a dict-like awkward record array; also accepts expressions (e.g. `"sqrt(px**2+py**2)"`), though expression support is pending for RNTuples |
| `filter_name=`, `filter_typename=`           | TTree: select branches by name glob/regex or C++ type; `filter_branch=` accepts a lambda; use `filter_field=` for RNTuples                         |
| `entry_start` / `entry_stop`                 | Slice to a range of events                                                                                                                         |
| Cycle numbers                                | `key;1` suffix — uproot uses the highest cycle by default                                                                                          |
| `interpretation=`                            | TTree only: uproot auto-detects; override with e.g. `interpretation=uproot.AsStrings()`; RNTuples always have unambiguous interpretations          |

## Canonical Patterns

### Inspect a file

```python
import uproot

with uproot.open("output.root") as f:
    print(f.keys())               # top-level keys, e.g. ["reco;1", "h_pt;1"]
    print(f.classnames())         # {"reco;1": "TTree", "h_pt;1": "TH1F"}
    tree = f["reco"]
    print(tree.typenames())       # branch name → C++ type (no data read)
    print(tree.num_entries)       # event count
    tree.show()                   # prints name/typename/interpretation table (TTrees and RNTuples)
```

### Filter branches by name or type

Test filters with `keys()` before committing to a full read:

```python
import uproot

with uproot.open("output.root:reco") as tree:
    print(tree.keys(filter_name="jet_*"))            # glob
    print(tree.keys(filter_name="/^(jet|el)_pt$/"))  # regex
    print(tree.keys(filter_typename="float"))         # C++ type

    # apply the same filters when reading
    jet_arrays  = tree.arrays(filter_name="jet_*")
    float_arrays = tree.arrays(filter_typename="float")

    # filter by branch attribute (e.g. compression ratio)
    arrays = tree.arrays(filter_branch=lambda b: b.compression_ratio > 5)
```

### Read branches as awkward arrays

```python
import uproot, awkward as ak

with uproot.open("output.root:reco") as tree:
    arrays = tree.arrays(["jet_pt", "jet_eta", "el_pt", "weight_mc"])
    # arrays["jet_pt"] is a var-length jagged array: shape (n_events, var)
    leading_jet_pt = arrays["jet_pt"][:, 0]   # first jet per event (fails on empty events)
    leading_jet_pt = ak.firsts(arrays["jet_pt"])  # safe: None for events with 0 jets
```

### Expressions, cuts, and aliases

The first argument to `arrays()` accepts branch names, expression strings, or a
mix. `cut=` filters events. `aliases=` assigns friendlier names. Expression
evaluation is not yet supported for RNTuples.

```python
import uproot

with uproot.open("output.root:reco") as tree:
    # entry-level cut (Python expression; ATLAS values in MeV)
    arrays = tree.arrays(
        ["jet_pt", "met_met"],
        cut="n_jets >= 4 && met_met > 200000",
    )

    # compute derived quantities at read time
    arrays = tree.arrays("sqrt(jet_px**2 + jet_py**2)")

    # give expressions friendlier names; can cut on aliases
    arrays = tree.arrays(
        ["jet_pt_calc", "met_met"],
        aliases={"jet_pt_calc": "sqrt(jet_px**2 + jet_py**2)"},
        cut="jet_pt_calc > 25000",
    )
```

### Read an RNTuple

RNTuple uses "fields" instead of "branches" and `filter_field=` instead of
`filter_branch=`; everything else mirrors the TTree interface.

```python
import uproot

with uproot.open("output.root:reco") as rnt:
    print(rnt.keys())           # field names
    print(rnt.typenames())      # field name → C++ type
    rnt.show()                  # name/typename table

    # read specific fields
    arrays = rnt.arrays(["jet_pt", "weight_mc"])

    # filter fields with a lambda
    arrays = rnt.arrays(filter_field=lambda f: "jet" in f.name)
```

### Read histograms from a ROOT file

```python
import uproot

with uproot.open("histograms.root") as f:
    h = f["h_jet_pt"]              # TH1F, TH1D, etc.

    # export to numpy  →  (bin contents, edges)
    values, edges = h.to_numpy()

    # export to boost-histogram (manipulation, rebinning)
    bh_obj = h.to_boost()

    # export to hist (plotting with mplhep)
    hist_obj = h.to_hist()

# TH2 follows the same interface
with uproot.open("histograms.root") as f:
    h2 = f["h_jet_pt_vs_eta"]
    values, xedges, yedges = h2.to_numpy()
    bh2 = h2.to_hist()
```

### Read as numpy (flat branches only)

```python
with uproot.open("output.root:reco") as tree:
    weights = tree["weight_mc"].array(library="np")   # 1-D numpy array
    pileup  = tree["weight_pileup"].array(library="np")
    total_weight = weights * pileup
```

### Read as pandas (flat branches only — no jagged)

```python
with uproot.open("output.root:reco") as tree:
    df = tree.arrays(["weight_mc", "weight_pileup", "met_met"], library="pd")
```

### Batch iteration over large files

`step_size` accepts an entry count or a memory string; the memory form is more
portable across datasets with different branch counts. `report=True` yields a
`(batch, report)` pair with entry-range metadata per batch.

```python
import uproot, awkward as ak

for batch in uproot.iterate(
    "ntuples/*.root:reco",
    ["jet_pt", "jet_eta", "weight_mc"],
    step_size="100 MB",         # or an integer, e.g. 100_000 entries
):
    # process batch — awkward record array
    pass

# with per-batch entry range metadata
for batch, report in uproot.iterate(
    "ntuples/*.root:reco",
    ["jet_pt", "weight_mc"],
    step_size="100 MB",
    report=True,
):
    print(report)   # Report(<TTree ...>, global_entry_start, global_entry_stop)
    pass
```

### Concatenate multiple files

```python
arrays = uproot.concatenate(
    ["sample_A.root:reco", "sample_B.root:reco"],
    ["jet_pt", "weight_mc"],
)
```

### Glob patterns and remote files

```python
# local glob
arrays = uproot.concatenate("ntuples/*.root:reco", ["jet_pt"])

# remote via XRootD (requires fsspec-xrootd)
arrays = uproot.concatenate(
    "root://eosatlas.cern.ch//eos/atlas/ntuples/*.root:reco",
    ["jet_pt"],
)
```

## Worked Example: Full NTuple → histogram pipeline

```python
import uproot, awkward as ak, hist, numpy as np
import vector; vector.register_awkward()

h_jet_pt = hist.Hist(
    hist.axis.Regular(50, 0, 1000, name="pt", label=r"Leading jet $p_T$ [GeV]"),
    storage=hist.storage.Weight(),
)

for batch in uproot.iterate(
    "ntuples/*.root:reco",
    ["jet_pt", "weight_mc", "weight_pileup", "weight_bTagSF_77"],
    step_size=200_000,
):
    # combined event weight
    w = batch["weight_mc"] * batch["weight_pileup"] * batch["weight_bTagSF_77"]

    # safe leading jet pT in GeV
    lj_pt = ak.firsts(batch["jet_pt"]) / 1000.0   # MeV → GeV
    mask  = ~ak.is_none(lj_pt)                     # drop events with 0 jets

    h_jet_pt.fill(pt=ak.to_numpy(lj_pt[mask]), weight=ak.to_numpy(w[mask]))

import mplhep as hep, matplotlib.pyplot as plt
fig, ax = plt.subplots()
hep.histplot(h_jet_pt, ax=ax)
hep.atlas.label(ax=ax, data=False, lumi=139)
fig.savefig("leading_jet_pt.pdf")
```

## Writing ROOT files

Uproot now writes RNTuples by default. Use `mkrntuple` to write an RNTuple
(supports any structure representable as an Awkward Array, including jagged and
nested fields). Use `mktree` to explicitly write a TTree (flat and
one-level-jagged branches only).

```python
import uproot, numpy as np, awkward as ak, hist

# Write an RNTuple (default, modern format — supports jagged/nested structures)
with uproot.recreate("output.root") as f:
    n = 10_000
    data = {
        "jet_pt":    ak.Array([np.random.exponential(50_000, np.random.randint(0, 6)) for _ in range(n)]),
        "weight_mc": np.ones(n),
    }
    rntuple = f.mkrntuple("reco", data)

# Write a TTree (legacy format — flat and one-level-jagged branches only)
with uproot.recreate("output_ttree.root") as f:
    n = 10_000
    tree = f.mktree("reco", {"jet_pt": "f4", "weight_mc": "f8"})
    tree.extend({"jet_pt": np.random.exponential(50_000, n).astype("f4"),
                 "weight_mc": np.ones(n)})

# Write a histogram
h = hist.Hist(hist.axis.Regular(40, 0, 200))
h.fill(np.random.normal(100, 15, 5000))
with uproot.recreate("hists.root") as f:
    f["h_mass"] = h  # uproot can write hist.Hist directly
```

## Troubleshooting

| Issue                         | Cause                                                      | Fix                                                      |
| ----------------------------- | ---------------------------------------------------------- | -------------------------------------------------------- |
| `KeyError: "reco"`            | Tree name wrong; file has cycle `reco;1`                   | `f.keys()` to inspect; or `f["reco;1"]` explicitly       |
| `IndexError` on `array[:, 0]` | Some events have zero jets                                 | Replace with `ak.firsts(array)`                          |
| `NotAnNumpyCompatible`        | Branch is jagged (variable-length)                         | Use `library="ak"` (default) or iterate                  |
| `MemoryError`                 | File too large for single load                             | Switch to `uproot.iterate` with `step_size`              |
| Wrong branch shape            | Systematic tree (e.g. `reco_JES__1up`) has extra dimension | Read the correct tree by name                            |
| Remote file stalls            | XRootD not installed                                       | `pip install uproot[xrootd]` or `fsspec-xrootd`          |
| `UnicodeDecodeError`          | ROOT string branch with non-UTF8 content                   | Use `branch.array(interpretation=uproot.AsStrings(...))` |
| `None` values in awkward      | `ak.firsts` returns `None` for empty events                | Use `mask = ~ak.is_none(arr)` before numpy conversion    |

## Gotchas

- **All ATLAS branches are in MeV**: divide by 1000 before GeV-scale histograms
  or cuts.
- **Systematic trees**: TopCPToolkit writes one TTree per systematic variation
  (e.g. `reco_JES__1up`). You must loop over tree names explicitly — there is no
  automatic loop.
- **`ak.to_numpy` fails on None**: filter with `~ak.is_none()` or
  `ak.fill_none(arr, 0.0)` first.
- **`tree.arrays()` reads all events by default**: for files with millions of
  events use `iterate` or `entry_start`/`entry_stop`.
- **TTree writing is limited**: jagged-array TTrees are restricted to one level
  of variable-length lists. For richer nested structures, write an RNTuple
  instead using `file.mkrntuple(...)`.

## Interop

- **awkward**: `tree.arrays()` returns `ak.Array` by default; pass
  `library="np"` for flat branches.
- **vector**: `vector.register_awkward()` adds Momentum4D behavior to awkward
  records named `{pt,eta,phi,mass}`.
- **hist**: Fill `hist.Hist` objects from uproot arrays; uproot can also write
  `hist.Hist` objects to ROOT files.
- **coffea**: `uproot.dask()` produces dask-awkward arrays for coffea
  NanoAOD-style processors.
- **fsspec-xrootd**: Mount EOS or grid storage so that uproot `root://` paths
  work transparently.

## Docs

https://uproot.readthedocs.io/en/latest/
