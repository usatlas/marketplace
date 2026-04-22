---
name: coffea
description: >-
    Use when writing a columnar ATLAS analysis with coffea: defining a
    NanoEvents or custom processor, running over multiple files with
    dask-awkward or iterative executor, accumulating histograms with hist,
    applying scale factors and systematic weights, or migrating a for-loop
    event analysis to a coffea processor pattern.
---

# coffea

## Overview

coffea is a columnar analysis toolkit built on awkward-array and hist. It provides a `Processor` abstraction that separates analysis logic from execution: the same processor runs locally (iterative), in parallel on a laptop (futures), or on the grid (dask + Parsl/HTCondor). coffea is heavily used at CMS but is fully usable for ATLAS analyses — the key difference is that ATLAS NTuples are read with uproot, not the NanoAOD schema layer.

## When to Use

- Writing a reproducible, batched analysis that must scale to many files
- Accumulating histograms from multiple samples and systematics in a single pass
- Analyses at Coffea-Casa or other ATLAS analysis facilities that pre-configure dask clusters
- When you want the coffea `Processor` pattern to separate "what to compute" from "how to parallelize"

## Key Concepts

| Concept | Notes |
|---|---|
| `Processor` | Class with `process(events)` → dict of accumulators |
| `hist.Hist` | The standard histogram accumulator inside coffea processors |
| `NanoEventsFactory` | Reads NanoAOD-style ROOT files with behavior mixins; not needed for flat ATLAS NTuples |
| `uproot.dask()` | Produces dask-awkward arrays from ROOT files; feeds a dask executor |
| `coffea.dataset_tools` | Helpers for building file sets and running with dask |
| `runner` | Deprecated (v0.7); coffea v2025+ uses `apply_to_fileset` + dask directly |
| `weight` / `Weights` | `coffea.analysis_tools.Weights` manages multiple scale factor weights |
| `PackedSelection` | Bitwise selection mask; fast AND/OR over boolean arrays |

## Canonical Patterns

### Minimal processor (ATLAS flat NTuple)

```python
import awkward as ak, hist
from coffea.processor import ProcessorABC, accumulate

class JetPtProcessor(ProcessorABC):
    def process(self, events):
        # events is an awkward record array from uproot.dask / iterate
        weight = events["weight_mc"] * events["weight_pileup"]

        lj_pt = ak.firsts(events["jet_pt"]) / 1000.0   # MeV → GeV
        mask  = ~ak.is_none(lj_pt) & (lj_pt > 25.0)

        h = hist.Hist(
            hist.axis.StrCategory([], growth=True, name="sample"),
            hist.axis.Regular(50, 0, 1000, name="pt", label=r"$p_T$ [GeV]"),
            storage=hist.storage.Weight(),
        )
        h.fill(
            sample=events.metadata["dataset"],
            pt=ak.to_numpy(lj_pt[mask]),
            weight=ak.to_numpy(weight[mask]),
        )
        return {"h_jet_pt": h}

    def postprocess(self, accumulator):
        return accumulator
```

### Run iteratively (small datasets / testing)

```python
import uproot
from coffea.processor import IterativeExecutor, Runner

fileset = {
    "ttbar": {"files": {"ntuples/ttbar.root": "reco"}, "metadata": {"dataset": "ttbar"}},
    "zjets": {"files": {"ntuples/zjets.root": "reco"}, "metadata": {"dataset": "zjets"}},
}

run = Runner(executor=IterativeExecutor(), schema=None)
output = run(fileset, treename="reco", processor_instance=JetPtProcessor())
```

### Run with dask (scale out)

```python
import uproot, dask
from coffea.dataset_tools import apply_to_fileset, max_chunks, preprocess

# Build preprocessed fileset (checks file accessibility, counts events)
available_files, _ = preprocess(
    fileset,
    step_size=100_000,
    skip_bad_files=True,
)

to_compute = apply_to_fileset(
    JetPtProcessor(),
    max_chunks(available_files, 300),
    uproot_options={"allow_read_errors_with_report": True},
)

output, reports = dask.compute(to_compute)
```

### Weights and scale factors

```python
from coffea.analysis_tools import Weights

def process(self, events):
    w = Weights(len(events))
    w.add("mc",     events["weight_mc"])
    w.add("pileup", events["weight_pileup"])
    w.add("btag",   events["weight_bTagSF_77"],
                    weightUp=events["weight_bTagSF_77_up"],
                    weightDown=events["weight_bTagSF_77_dn"])

    # nominal weight
    total = w.weight()

    # systematic variations
    btag_up   = w.weight("btag_up")
    btag_down = w.weight("btag_down")
```

### PackedSelection (fast multi-cut)

```python
from coffea.analysis_tools import PackedSelection

sel = PackedSelection()
sel.add("baseline", events["n_jets"] >= 4)
sel.add("btag",     events["n_bjets"] >= 2)
sel.add("met",      events["met_met"] > 200_000)    # MeV

sr_mask = sel.all("baseline", "btag", "met")
cr_mask = sel.all("baseline", "btag") & ~sel.all("met")
```

## Worked Example: Two-region histogram accumulation

```python
import awkward as ak, hist, numpy as np
from coffea.processor import ProcessorABC
from coffea.analysis_tools import Weights, PackedSelection

class TwoRegionProcessor(ProcessorABC):
    def process(self, events):
        w = Weights(len(events))
        w.add("mc",     events["weight_mc"])
        w.add("pileup", events["weight_pileup"])
        w.add("btag",   events["weight_bTagSF_77"])

        sel = PackedSelection()
        sel.add("jets4",  events["n_jets"] >= 4)
        sel.add("bjets2", events["n_bjets"] >= 2)
        sel.add("highMET", events["met_met"] > 200_000)

        lj_pt = ak.to_numpy(ak.fill_none(ak.firsts(events["jet_pt"]), 0.0)) / 1000.0

        axes = [
            hist.axis.StrCategory([], growth=True, name="region"),
            hist.axis.Regular(40, 0, 800, name="pt", label=r"Leading jet $p_T$ [GeV]"),
        ]
        h = hist.Hist(*axes, storage=hist.storage.Weight())

        for region, mask_fn in [
            ("SR", lambda s: s.all("jets4", "bjets2", "highMET")),
            ("CR", lambda s: s.all("jets4", "bjets2") & ~s.all("highMET")),
        ]:
            m = mask_fn(sel)
            h.fill(region=region, pt=lj_pt[m], weight=w.weight()[m])

        return {"h": h}

    def postprocess(self, accumulator):
        return accumulator
```

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `AttributeError: 'dict' has no attribute 'metadata'` | NanoEventsFactory used with flat NTuple | Use `schema=None` or `BaseSchema`; access branches directly |
| `KeyError: treename` | Wrong tree name in fileset | Check with `uproot.open(file).keys()` |
| Dask graph never computes | `dask.compute()` not called | Call `dask.compute(to_compute)` explicitly |
| Histograms don't accumulate across files | Returning a new `hist.Hist` per chunk | Use `StrCategory(growth=True)` and rely on `accumulate` |
| `None` values after `ak.firsts` | Events with zero jets | Wrap with `ak.fill_none(arr, default_value)` |
| Memory spike on dask worker | `step_size` too large | Reduce `step_size` in `preprocess` |
| `IterativeExecutor` is slow on many files | Serial execution | Switch to `FuturesExecutor(workers=4)` locally |

## Gotchas

- **ATLAS NTuples are not NanoAOD**: set `schema=None` when using `Runner`, or pass `uproot_options` that skip schema detection. Branches are flat or jagged `vector<float>`, not behavior-augmented.
- **All ATLAS branches are in MeV**: divide by 1000 before GeV histograms.
- **coffea v0.7 vs v2025+**: The `Runner`/`IterativeExecutor`/`FuturesExecutor` API changed significantly. v2025 uses `apply_to_fileset` + dask. Check which version is installed with `import coffea; print(coffea.__version__)`.
- **`process()` must return a dict or a nested dict**: accumulators are merged across chunks by the framework.
- **`postprocess()` is called once** after all chunks are merged — use it for normalization, not per-chunk computation.

## Interop

- **uproot**: `uproot.dask()` produces dask-awkward arrays for coffea processors; `uproot.iterate` for non-dask mode.
- **awkward**: All event data inside processors is `ak.Array`; use `ak.firsts`, `ak.pad_none`, `ak.fill_none` for jagged branches.
- **hist**: The standard accumulator type; fill inside `process()`, merge automatically across chunks.
- **vector**: `vector.register_awkward()` adds four-vector methods to awkward records before passing to a processor.
- **Coffea-Casa**: ATLAS analysis facility at University of Chicago that pre-configures a dask cluster for ATLAS users.

## Docs

https://coffea-hep.readthedocs.io/en/latest/
