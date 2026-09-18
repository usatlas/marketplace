# coffea NanoEvents Schemas and Data Access — Deep Reference

Read this reference when discovering the structure of an unfamiliar ROOT file,
choosing between `mode="eager"` and `mode="virtual"`, tuning
`NanoEventsFactory` performance with `preload`/`buffer_cache`, or iterating
over `atlas-schema` systematic variations.

## Table of Contents

- [NanoEvents schema selection and field discovery](#nanoevents-schema-selection-and-field-discovery)
- [NanoEventsFactory performance options](#nanoeventsfactory-performance-options)
- [atlas-schema: iterating systematic variations](#atlas-schema-iterating-systematic-variations)

## NanoEvents schema selection and field discovery

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
| ----------------------------------- | ---------------- | ----------------------------------------- |
| CP algorithm NTuple (TopCPToolkit) | `NtupleSchema`   | `events.recojet.pt`; systematics via loop |
| Flat NTuple (SimpleAnalysis)       | `BaseSchema`     | `events["jet_pt"]` verbatim               |
| DAOD_PHYSLITE                      | `PHYSLITESchema` | `events.Jets.pt` with behaviors           |
| CMS NanoAOD (reference/comparison) | `NanoAODSchema`  | `events.Jet.pt` with behaviors            |

## NanoEventsFactory performance options

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

## atlas-schema: iterating systematic variations

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
