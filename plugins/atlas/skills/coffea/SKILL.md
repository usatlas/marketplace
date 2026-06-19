---
name: coffea
description: >-
  Use when writing a columnar ATLAS analysis with coffea: defining a NanoEvents
  or custom processor, running over ROOT files, accumulating histograms with
  hist, applying scale factors and systematic weights, or migrating a for-loop
  event analysis to a coffea processor pattern.
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

| Concept                                                             | Notes                                                                                                                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Processor`                                                         | Class with `process(events)` → dict of accumulators                                                                                                    |
| `hist.Hist`                                                         | The standard histogram accumulator inside coffea processors                                                                                            |
| `NanoEventsFactory`                                                 | Reads ROOT files into a schema-driven awkward record array with optional behavior mixins                                                               |
| `BaseSchema`                                                        | Verbatim branch access, no behaviors; correct choice for flat ATLAS NTuples (AnalysisTop, SimpleAnalysis)                                              |
| `PHYSLITESchema`                                                    | ATLAS DAOD_PHYSLITE derivation; provides Lorentz-vector behaviors on electrons, muons, jets                                                            |
| `NanoAODSchema`                                                     | CMS NanoAOD format; not suited for ATLAS files                                                                                                         |
| `NtupleSchema`                                                      | `atlas-schema` package; best choice for CP algorithm NTuples (TopCPToolkit, EasyJet, AnalysisTop)                                                      |
| `Runner` / `IterativeExecutor` / `FuturesExecutor` / `DaskExecutor` | `Runner` wraps an executor and dispatches a processor over a fileset; swapping the executor is the only change needed to go from a laptop to a cluster |
| `weight` / `Weights`                                                | `coffea.analysis_tools.Weights` manages multiple scale factor weights                                                                                  |
| `PackedSelection`                                                   | Bitwise selection mask; fast AND/OR over boolean arrays                                                                                                |

## Canonical Patterns

### Minimal processor (ATLAS flat NTuple)

```python
import awkward as ak, hist
from coffea.processor import ProcessorABC, accumulate

class JetPtProcessor(ProcessorABC):
    def process(self, events):
        # events is an awkward record array from uproot.iterate
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
from coffea.nanoevents import BaseSchema
from coffea.processor import IterativeExecutor, Runner

fileset = {
    "ttbar": {"files": {"ntuples/ttbar.root": "reco"}, "metadata": {"dataset": "ttbar"}},
    "zjets": {"files": {"ntuples/zjets.root": "reco"}, "metadata": {"dataset": "zjets"}},
}

run = Runner(executor=IterativeExecutor(), schema=BaseSchema)
output = run(fileset, treename="reco", processor_instance=JetPtProcessor())
```

### Run with dask (scale out)

Connect a `DaskExecutor` to a running `dask.distributed` cluster — the processor
code is identical to the iterative example; only the executor changes.

```python
from coffea.nanoevents import BaseSchema
from coffea.processor import Runner, DaskExecutor
from dask.distributed import Client

client = Client("tcp://scheduler:8786")   # or Client() for a local cluster

run = Runner(
    executor=DaskExecutor(client=client),
    schema=BaseSchema,
    savemetrics=True,
)
output, metrics = run(fileset, treename="reco", processor_instance=JetPtProcessor())
```

### Weights and scale factors

`Weights` accumulates per-event weights and propagates systematic variations.
Each `add()` call multiplies into the total; `weightUp`/`weightDown` register
named variations (suffixes `Up`/`Down` are appended automatically).

```python
from coffea.analysis_tools import Weights

def process(self, events):
    w = Weights(len(events))
    w.add("mc",     events["weight_mc"])
    w.add("pileup", events["weight_pileup"])
    w.add("btag",   events["weight_bTagSF_77"],
                    weightUp=events["weight_bTagSF_77_up"],
                    weightDown=events["weight_bTagSF_77_dn"])

    total     = w.weight()            # product of all nominal weights
    btag_up   = w.weight("btagUp")   # one systematic variation
    btag_down = w.weight("btagDown")

    print(w.variations)  # {'btagUp', 'btagDown', ...}
```

### Object-level systematics

For custom object smearing (e.g. JES/JER when not baked into the NTuple), use
`add_systematic` on a collection. This is separate from `NtupleSchema`
systematics, which are already in the file:

```python
import numpy as np

def jet_pt_scale(pt):
    # returns shape (n_events, 2) — axis-1 is [up, down]
    return (1.0 + np.array([0.05, -0.05], dtype="f4")) * pt[:, None]

events.Jet.add_systematic("PtScale", "UpDownSystematic", "pt", jet_pt_scale)

jet_pt_up   = events.Jet.systematics.PtScale.up.pt
jet_pt_down = events.Jet.systematics.PtScale.down.pt
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

Two `mode` values are used in ATLAS work:

- `"eager"` — all branches are fully loaded into memory at factory creation.
  **Only use for very small test files** (≲ a few thousand events): a single 1
  GB ROOT file can expand to several GB of RAM when decompressed and take over a
  minute to load. The examples below use `"eager"` so results are immediately
  visible in a notebook cell.
- `"virtual"` — branches are loaded lazily only when first accessed; this is the
  default and what `Runner` uses internally. Fine for interactive exploration
  too — `repr(events)` shows `?` for unloaded fields, but access works normally.
  Pass `access_log=[]` to track which branches are touched. Call
  `ak.materialize(events.<field>)` to force-load a specific branch when
  exploring.

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

### NanoEventsFactory performance options

`preload` and `buffer_cache` are available in `eager` and `virtual` modes:

```python
cache = {}   # any dict-like; LRU or Redis also work

events = NanoEventsFactory.from_root(
    {"ntuple.root": "reco"},
    schemaclass=BaseSchema,
    metadata={"dataset": "ttbar"},
    preload=["jet_pt", "jet_eta", "met_met"],  # bulk-fetch before processor loop
    buffer_cache=cache,  # stores raw numpy arrays; avoids re-decompressing on re-access
    mode="virtual",
).events()
```

`preload` accepts a list of branch names or a `filter_branch` callable (same
signature as `uproot`'s `tree.arrays`). `buffer_cache` is keyed by globally
unique strings; pass a shared cache instance across multiple factory calls to
amortise decompression cost across chunks.

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

| Issue                                                | Cause                                   | Fix                                                     |
| ---------------------------------------------------- | --------------------------------------- | ------------------------------------------------------- |
| `AttributeError: 'dict' has no attribute 'metadata'` | NanoEventsFactory used with flat NTuple | Use `BaseSchema`; access branches directly              |
| `KeyError: treename`                                 | Wrong tree name in fileset              | Check with `uproot.open(file).keys()`                   |
| Histograms don't accumulate across files             | Returning a new `hist.Hist` per chunk   | Use `StrCategory(growth=True)` and rely on `accumulate` |
| `None` values after `ak.firsts`                      | Events with zero jets                   | Wrap with `ak.fill_none(arr, default_value)`            |
| `IterativeExecutor` is slow on many files            | Serial execution                        | Switch to `FuturesExecutor(workers=4)` locally          |

## Gotchas

- **Schema selection matters for ATLAS**: CP algorithm NTuples (TopCPToolkit,
  EasyJet) use `NtupleSchema` from `atlas-schema`; DAOD_PHYSLITE uses
  `PHYSLITESchema`; other flat NTuples use `BaseSchema`. Always pass an explicit
  schema to `Runner` (its default is `NanoAODSchema`, which is CMS-specific and
  wrong for ATLAS). Branches are flat or jagged `vector<float>` under
  `BaseSchema`, not behavior-augmented — no `.pt`, `.eta` shorthand unless you
  use `PHYSLITESchema` or `NtupleSchema`.
- **NanoEvents fields are runtime-dynamic**: the available fields depend on the
  schema and the file content. Always call `events.fields` and
  `events.<collection>.fields` in a notebook before writing a processor to avoid
  `AttributeError` on non-existent branches.
- **All ATLAS branches are in MeV**: divide by 1000 before GeV histograms.
- **Two execution patterns for ATLAS**: `Runner` +
  `IterativeExecutor`/`FuturesExecutor` for local execution; `Runner` +
  `DaskExecutor(client=client)` to scale the same processor to a Dask
  Distributed cluster with zero processor-code changes — the processor receives
  the same materialized `ak.Array` objects in all cases, `hist.Hist` works
  throughout. Check your version with
  `import coffea; print(coffea.__version__)`.
- **`preload` / `buffer_cache`**: `preload` bulk-fetches named branches before
  the processor loop; `buffer_cache` stores raw numpy arrays to avoid
  re-decompressing on repeated access.
- **`process()` must return a dict or a nested dict**: accumulators are merged
  across chunks by the framework.
- **`postprocess()` is called once** after all chunks are merged — use it for
  normalization, not per-chunk computation.

## Interop

- **uproot**: `uproot.iterate` feeds data into coffea processors chunk by chunk.
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
- **Coffea-Casa**: analysis facility (e.g. the UNL/Nebraska deployment and
  ATLAS-flavoured instances) that pre-configures a dask cluster for users.

## Docs

https://coffea-hep.readthedocs.io/en/latest/

https://atlas-schema.readthedocs.io/en/latest/
