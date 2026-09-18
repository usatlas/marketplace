# uproot Additional Read Recipes — Deep Reference

Read this reference when the basic inspect/filter/read-into-awkward workflow in
SKILL.md doesn't cover the case: expression-based cuts, RNTuple-specific reads,
histogram extraction, numpy/pandas export, multi-file concatenation, remote/glob
file access, or a full end-to-end pipeline example.

## Table of Contents

- [Expressions, cuts, and aliases](#expressions-cuts-and-aliases)
- [Read an RNTuple](#read-an-rntuple)
- [Read histograms from a ROOT file](#read-histograms-from-a-root-file)
- [Read as numpy (flat branches only)](#read-as-numpy-flat-branches-only)
- [Read as pandas (flat branches only — no jagged)](#read-as-pandas-flat-branches-only--no-jagged)
- [Concatenate multiple files](#concatenate-multiple-files)
- [Glob patterns and remote files](#glob-patterns-and-remote-files)
- [Worked Example: Full NTuple → histogram pipeline](#worked-example-full-ntuple--histogram-pipeline)

## Expressions, cuts, and aliases

The first argument to `arrays()` accepts branch names, expression strings, or a
mix. `cut=` filters events. `aliases=` assigns friendlier names. Expression
evaluation is not yet supported for RNTuples.

```python
import uproot

with uproot.open("output.root:reco") as tree:
    # entry-level cut (Python expression; ATLAS values in MeV)
    arrays = tree.arrays(
        ["jet_pt", "met_met"],
        cut="n_jets >= 4 & met_met > 200000",
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

## Read an RNTuple

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

## Read histograms from a ROOT file

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

## Read as numpy (flat branches only)

```python
with uproot.open("output.root:reco") as tree:
    weights = tree["weight_mc"].array(library="np")   # 1-D numpy array
    pileup  = tree["weight_pileup"].array(library="np")
    total_weight = weights * pileup
```

## Read as pandas (flat branches only — no jagged)

```python
with uproot.open("output.root:reco") as tree:
    df = tree.arrays(["weight_mc", "weight_pileup", "met_met"], library="pd")
```

## Concatenate multiple files

```python
arrays = uproot.concatenate(
    ["sample_A.root:reco", "sample_B.root:reco"],
    ["jet_pt", "weight_mc"],
)
```

## Glob patterns and remote files

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
