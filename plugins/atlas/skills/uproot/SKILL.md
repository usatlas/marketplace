---
name: uproot
description: >-
  Use when reading or writing ROOT files in Python without a ROOT installation,
  or when encountering issues opening TTrees, RNTuples, or histograms.
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

## Gotchas

- **ATLAS energy/momentum values are in MeV**: divide by 1000 before GeV-scale
  histograms or cuts.
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

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`references/read-recipes.md`** — Expression-based cuts and aliases,
  RNTuple-specific reads, histogram extraction
  (`to_numpy`/`to_boost`/`to_hist`), numpy/pandas export, multi-file
  concatenation, glob/remote (XRootD) file access, and a full worked NTuple →
  histogram pipeline. Read when the basic inspect/filter/read-into-awkward
  workflow above doesn't cover the case.
- **`references/writing-and-troubleshooting.md`** — Writing RNTuples, TTrees,
  and histograms back to ROOT files, plus a table of common uproot errors (key
  errors, jagged-array pitfalls, memory errors, remote-file stalls) and their
  fixes. Read when writing ROOT output or debugging an uproot exception.

## Docs

https://uproot.readthedocs.io/en/latest/
