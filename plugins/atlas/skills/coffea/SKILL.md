---
name: coffea
description: >-
  Use when writing a columnar ATLAS analysis with coffea: defining a NanoEvents
  or custom processor, running over multiple files with dask-awkward or
  iterative executor, accumulating histograms with hist, applying scale factors
  and systematic weights, or migrating a for-loop event analysis to a coffea
  processor pattern.
---

# coffea

## Overview

coffea is a columnar analysis toolkit built on awkward-array and hist. It
provides a `Processor` abstraction that separates analysis logic from execution:
the same processor runs locally (iterative), in parallel on a laptop (futures),
or on the grid (dask + Parsl/HTCondor). coffea is heavily used at CMS but is
fully usable for ATLAS analyses — the key difference is that ATLAS NTuples are
read with uproot, not the NanoAOD schema layer.

## When to Use

- Writing a reproducible, batched analysis that must scale to many files
- Accumulating histograms from multiple samples and systematics in a single pass
- Analyses at Coffea-Casa or other ATLAS analysis facilities that pre-configure
  dask clusters
- When you want the coffea `Processor` pattern to separate "what to compute"
  from "how to parallelize"

## Key Concepts

| Concept                                            | Notes                                                                                                                                                      |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Processor`                                        | Class with `process(events)` → dict of accumulators                                                                                                        |
| `hist.Hist`                                        | The standard histogram accumulator inside coffea processors                                                                                                |
| `NanoEventsFactory`                                | Reads ROOT files into a schema-driven awkward record array with optional behavior mixins                                                                   |
| `BaseSchema`                                       | Verbatim branch access, no behaviors; correct choice for flat ATLAS NTuples (AnalysisTop, SimpleAnalysis)                                                  |
| `PHYSLITESchema`                                   | ATLAS DAOD_PHYSLITE derivation; provides Lorentz-vector behaviors on electrons, muons, jets                                                                |
| `NanoAODSchema`                                    | CMS NanoAOD format; not suited for ATLAS files                                                                                                             |
| `NtupleSchema`                                     | `atlas-schema` package; best choice for CP algorithm NTuples (TopCPToolkit, EasyJet, AnalysisTop)                                                          |
| `uproot.dask()`                                    | Produces dask-awkward arrays from ROOT files; feeds a dask executor                                                                                        |
| `coffea.dataset_tools`                             | Helpers for building file sets and running with dask                                                                                                       |
| `Runner` / `IterativeExecutor` / `FuturesExecutor` | Current, supported APIs (v2026.x); `Runner` wraps an executor and dispatches a processor over a fileset; `apply_to_fileset` is the dask-native alternative |
| `weight` / `Weights`                               | `coffea.analysis_tools.Weights` manages multiple scale factor weights                                                                                      |
| `PackedSelection`                                  | Bitwise selection mask; fast AND/OR over boolean arrays                                                                                                    |

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

### NanoEvents schema selection and field discovery

NanoEvents fields are determined at runtime by the schema and the file content —
there is no static list. Before writing a processor against an unfamiliar file,
discover its structure interactively:

```python
import awkward as ak
from coffea.nanoevents import NanoEventsFactory, BaseSchema, PHYSLITESchema
from atlas_schema.schema import NtupleSchema  # pip/conda-forge: atlas-schema

# ── CP algorithm NTuple (TopCPToolkit, EasyJet, AnalysisTop) ─────────────────
events = NanoEventsFactory.from_root(
    {"ntuple.root": "analysis"},   # tree name varies; check with uproot.open
    schemaclass=NtupleSchema,
    metadata={"dataset": "ttbar"},
    entry_stop=1000,               # limit rows for interactive exploration
    mode="eager",
).events()

# ── ATLAS flat NTuple without atlas-schema ────────────────────────────────────
events = NanoEventsFactory.from_root(
    {"ntuple.root": "reco"},
    schemaclass=BaseSchema,
    metadata={"dataset": "ttbar"},
    entry_stop=1000,
    mode="eager",
).events()

# ── ATLAS DAOD_PHYSLITE ───────────────────────────────────────────────────────
events = NanoEventsFactory.from_root(
    {"physlite.root": "CollectionTree"},
    schemaclass=PHYSLITESchema,
    metadata={"dataset": "ttbar"},
    entry_stop=1000,
    mode="eager",
).events()
```

Inspect available fields at each level before writing analysis code:

```python
# Top-level collections / branches
print(events.fields)
# e.g. NtupleSchema:   ['recojet', 'truthjet', 'met', 'weight', 'truth', 'trigPassed', ...]
# e.g. BaseSchema:     ['jet_pt', 'jet_eta', 'el_pt', 'mu_pt', 'met_met', ...]
# e.g. PHYSLITESchema: ['Jets', 'Electrons', 'Muons', 'MissingET', ...]

# Sub-fields of a collection (NtupleSchema / PHYSLITESchema)
print(events.recojet.fields)       # ['pt', 'eta', 'phi', 'e', 'jvt', ...]
print(events.Jets.fields)          # ['pt', 'eta', 'phi', 'e', 'charge', ...]

# Awkward type — tells you whether a branch is flat or jagged
print(events.recojet.pt.type)      # var * float32  ← jagged (one per jet per event)
print(events["met_met"].type)      # float32        ← flat (one per event, BaseSchema)

# How many objects per event (jagged branches)
print(ak.num(events.recojet, axis=1))  # [4, 3, 5, ...]

# NtupleSchema: list systematic variations present in the file
print(events.systematic_names)     # ['NOSYS', 'JET_JER__1up', 'JET_JER__1down', ...]
```

Schema summary for ATLAS work:

| File type                          | `schemaclass`    | Branch access style                       |
| ---------------------------------- | ---------------- | ----------------------------------------- |
| CP algorithm NTuple (TopCPToolkit) | `NtupleSchema`   | `events.recojet.pt`; systematics via loop |
| Flat NTuple (SimpleAnalysis)       | `BaseSchema`     | `events["jet_pt"]` verbatim               |
| DAOD_PHYSLITE                      | `PHYSLITESchema` | `events.Jets.pt` with behaviors           |
| CMS NanoAOD (reference/comparison) | `NanoAODSchema`  | `events.Jet.pt` with behaviors            |

### atlas-schema: iterating systematic variations

`NtupleSchema` exposes every systematic variation stored in the NTuple. Use
`events.systematic_names` (includes `"NOSYS"` for nominal) and index the events
object to get a variation-specific view with consistent collection names:

```python
from atlas_schema.schema import NtupleSchema
from coffea.processor import ProcessorABC
import awkward as ak, hist

class SystematicsProcessor(ProcessorABC):
    def process(self, events):
        h = hist.Hist(
            hist.axis.StrCategory([], growth=True, name="variation"),
            hist.axis.Regular(50, 0, 500, name="jet_pt", label=r"Leading jet $p_T$ [GeV]"),
            storage=hist.storage.Weight(),
        )

        for variation in events.systematic_names:
            ev = events[variation]         # variation-specific view; same field names
            lj_pt = ak.firsts(ev.recojet.pt) / 1000.0   # MeV → GeV
            mask = ~ak.is_none(lj_pt)
            weight = ev.weight.mc[mask] if hasattr(ev, "weight") else ak.ones_like(lj_pt[mask])
            h.fill(variation=variation, jet_pt=ak.to_numpy(lj_pt[mask]), weight=ak.to_numpy(weight))

        return {"h_jet_pt": h}

    def postprocess(self, accumulator):
        return accumulator
```

## Gotchas

- **Schema selection matters for ATLAS**: CP algorithm NTuples (TopCPToolkit,
  EasyJet) use `NtupleSchema` from `atlas-schema`; DAOD_PHYSLITE uses
  `PHYSLITESchema`; other flat NTuples use `BaseSchema`. Setting `schema=None`
  in `Runner` or `apply_to_fileset` disables NanoEvents entirely and passes raw
  uproot arrays. Branches are flat or jagged `vector<float>` under `BaseSchema`,
  not behavior-augmented — no `.pt`, `.eta` shorthand unless you use
  `PHYSLITESchema` or `NtupleSchema`.
- **NanoEvents fields are runtime-dynamic**: the available fields depend on the
  schema and the file content. Always call `events.fields` and
  `events.<collection>.fields` in a notebook before writing a processor to avoid
  `AttributeError` on non-existent branches.
- **All ATLAS branches are in MeV**: divide by 1000 before GeV histograms.
- **Two valid execution patterns**: `Runner` +
  `IterativeExecutor`/`FuturesExecutor` is the processor-based API for
  synchronous or threaded execution; `apply_to_fileset` + dask is the
  recommended path for cluster-scale runs. Both are supported in recent versions
  (v2026.x). Check yours with `import coffea; print(coffea.__version__)`.
- **`process()` must return a dict or a nested dict**: accumulators are merged
  across chunks by the framework.
- **`postprocess()` is called once** after all chunks are merged — use it for
  normalization, not per-chunk computation.

## Interop

- **uproot**: `uproot.dask()` produces dask-awkward arrays for coffea
  processors; `uproot.iterate` for non-dask mode.
- **awkward**: All event data inside processors is `ak.Array`; use `ak.firsts`,
  `ak.pad_none`, `ak.fill_none` for jagged branches.
- **hist**: The standard accumulator type; fill inside `process()`, merge
  automatically across chunks.
- **vector**: `vector.register_awkward()` adds four-vector methods to awkward
  records before passing to a processor.
- **atlas-schema**: `NtupleSchema` from the `atlas-schema` package structures CP
  algorithm NTuples into collections and exposes `events.systematic_names` /
  `events[variation]` for systematic iteration; install with
  `pip install atlas-schema` or `pixi add atlas-schema` (conda-forge).
- **Coffea-Casa**: ATLAS analysis facility at University of Chicago that
  pre-configures a dask cluster for ATLAS users.

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

| Issue                                                | Cause                                   | Fix                                                         |
| ---------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------- |
| `AttributeError: 'dict' has no attribute 'metadata'` | NanoEventsFactory used with flat NTuple | Use `schema=None` or `BaseSchema`; access branches directly |
| `KeyError: treename`                                 | Wrong tree name in fileset              | Check with `uproot.open(file).keys()`                       |
| Dask graph never computes                            | `dask.compute()` not called             | Call `dask.compute(to_compute)` explicitly                  |
| Histograms don't accumulate across files             | Returning a new `hist.Hist` per chunk   | Use `StrCategory(growth=True)` and rely on `accumulate`     |
| `None` values after `ak.firsts`                      | Events with zero jets                   | Wrap with `ak.fill_none(arr, default_value)`                |
| Memory spike on dask worker                          | `step_size` too large                   | Reduce `step_size` in `preprocess`                          |
| `IterativeExecutor` is slow on many files            | Serial execution                        | Switch to `FuturesExecutor(workers=4)` locally              |

## Docs

https://coffea-hep.readthedocs.io/en/latest/

https://atlas-schema.readthedocs.io/en/latest/
