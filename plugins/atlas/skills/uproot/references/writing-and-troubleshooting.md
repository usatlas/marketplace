# uproot Writing & Troubleshooting — Deep Reference

Read this reference when writing ROOT files (RNTuples, TTrees, or histograms)
from Python, or diagnosing a common uproot error.

## Table of Contents

- [Write ROOT files](#write-root-files)
- [Troubleshooting](#troubleshooting)

## Write ROOT files

Uproot now writes RNTuples by default when using the dict-like syntax. Use
`mkrntuple` to write an RNTuple (supports any structure representable as an
Awkward Array, including jagged and nested fields). Use `mktree` to explicitly
write a TTree (flat and one-level-jagged branches only).

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
    # or since it is default via dict-like
    # f["reco"] = data

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
