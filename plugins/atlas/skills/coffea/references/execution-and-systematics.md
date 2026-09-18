# coffea Scale-Out Execution and Advanced Systematics — Deep Reference

Read this reference when scaling a processor to a Dask cluster, applying
object-level systematic variations that are not already baked into the NTuple,
or building a multi-region histogram accumulation processor.

## Table of Contents

- [Run with dask (scale out)](#run-with-dask-scale-out)
- [Object-level systematics](#object-level-systematics)
- [Worked Example: Two-region histogram accumulation](#worked-example-two-region-histogram-accumulation)

## Run with dask (scale out)

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

## Object-level systematics

For custom object smearing (e.g. JES/JER when not baked into the NTuple), use
`add_systematic` on a collection. This is separate from `NtupleSchema`
systematics, which are already in the file:

```python
import numpy as np

def jet_pt_scale(pt):
    # pt is jagged (events x jets); broadcasts to events x jets x 2, the last
    # axis holding [up, down]
    return (1.0 + np.array([0.05, -0.05], dtype="f4")) * pt[:, None]

events.Jet.add_systematic("PtScale", "UpDownSystematic", "pt", jet_pt_scale)

jet_pt_up   = events.Jet.systematics.PtScale.up.pt
jet_pt_down = events.Jet.systematics.PtScale.down.pt
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
