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
TTree branches into arrays for analysis; a secondary use is writing lightweight
ROOT files containing histograms or flat NTuples.

## When to Use

- Reading ATLAS NTuple output (TopCPToolkit, FastFrames, AnalysisTop) into
  Python
- Inspecting a ROOT file's contents without invoking ROOT or C++
- Batch-iterating over files too large to load into memory at once
- Writing histogram output back to ROOT for TRExFitter or legacy tools
- Bridging ROOT data into the awkward / coffea / hist ecosystem

## Key Concepts

| Concept                                      | Notes                                                     |
| -------------------------------------------- | --------------------------------------------------------- |
| `uproot.open(path)`                          | Opens one file; returns a `ReadOnlyDirectory`             |
| `uproot.open("file.root:tree")`              | Opens file and directly returns the named TTree           |
| `uproot.concatenate(files, filter_name=...)` | Reads multiple files at once into one array               |
| `uproot.iterate(files, ...)`                 | Yields batches (use for large datasets)                   |
| `tree.keys()`                                | Lists branch names in the TTree                           |
| `tree["branch"].array()`                     | Returns full branch as an awkward array                   |
| `tree.arrays(["b1","b2"])`                   | Returns a dict-like awkward record array                  |
| `entry_start` / `entry_stop`                 | Slice to a range of events                                |
| Cycle numbers                                | `key;1` suffix — uproot uses the highest cycle by default |
| `interpretation`                             | uproot auto-detects; override with `library=`             |

## Canonical Patterns

### Inspect a file

```python
import uproot

with uproot.open("output.root") as f:
    print(f.keys())               # top-level keys, e.g. ["reco;1"]
    tree = f["reco"]
    print(tree.keys())            # branch names
    print(tree.num_entries)       # event count
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

### Filter at read time (cut_expression)

```python
with uproot.open("output.root:reco") as tree:
    arrays = tree.arrays(
        ["jet_pt", "met_met"],
        cut="n_jets >= 4 && met_met > 200000",   # ROOT C++ expression
    )
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

```python
import uproot, awkward as ak

for batch in uproot.iterate(
    "ntuples/*.root:reco",
    ["jet_pt", "jet_eta", "weight_mc"],
    step_size=100_000,          # events per batch
):
    # process batch — awkward record array
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

```python
import uproot, numpy as np, hist

# Write a TTree with flat branches
with uproot.recreate("output.root") as f:
    n = 10_000
    f["reco"] = {
        "jet_pt":   np.random.exponential(50_000, n),   # MeV
        "weight_mc": np.ones(n),
    }

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
- **uproot writes simple flat NTuples only**: jagged-array TTrees require PyROOT
  or ROOT.

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
