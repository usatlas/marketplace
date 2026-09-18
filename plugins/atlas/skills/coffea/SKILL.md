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

### Choosing a schema and discovering fields

NanoEvents fields are determined at runtime by the schema and the file content —
there is no static list. Before writing a processor against an unfamiliar file,
open it interactively with `NanoEventsFactory.from_root(..., mode="virtual")`
(the safe default — branches load lazily; `mode="eager"` on a full-size file can
expand to several GB in memory) and inspect `events.fields` /
`events.<collection>.fields`.

| File type                          | `schemaclass`    | Branch access style                       |
| ---------------------------------- | ---------------- | ----------------------------------------- |
| CP algorithm NTuple (TopCPToolkit) | `NtupleSchema`   | `events.recojet.pt`; systematics via loop |
| Flat NTuple (SimpleAnalysis)       | `BaseSchema`     | `events["jet_pt"]` verbatim               |
| DAOD_PHYSLITE                      | `PHYSLITESchema` | `events.Jets.pt` with behaviors           |
| CMS NanoAOD (reference/comparison) | `NanoAODSchema`  | `events.Jet.pt` with behaviors            |

See `references/nanoevents-schemas.md` for the full field-discovery workflow,
`preload`/`buffer_cache` performance tuning, and iterating `atlas-schema`
systematic variations.

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

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`references/nanoevents-schemas.md`** — Full field-discovery workflow
  (`eager` vs. `virtual` mode, inspecting
  `events.fields`/`events.<collection>.fields`, detecting jagged vs. flat
  branches), `NanoEventsFactory` performance tuning with
  `preload`/`buffer_cache`, and iterating `atlas-schema`
  `events.systematic_names` variations. Read when exploring an unfamiliar ROOT
  file's structure or optimizing NanoEvents load performance.
- **`references/execution-and-systematics.md`** — Scaling a processor to a
  `dask.distributed` cluster with `DaskExecutor`, applying object-level
  systematic smearing with `add_systematic` for JES/JER not already baked into
  the NTuple, and a worked two-region (SR/CR) histogram accumulation processor.
  Read when moving a processor from a laptop to a cluster or building custom
  object-level variations.

## Docs

https://coffea-hep.readthedocs.io/en/latest/

https://atlas-schema.readthedocs.io/en/latest/
