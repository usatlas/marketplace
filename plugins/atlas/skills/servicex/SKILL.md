---
name: servicex
description: >-
  Use when querying ATLAS data remotely via ServiceX: fetching branches from
  ROOT NTuples with the Uproot backend, writing FuncADL queries against
  DAOD_PHYS or DAOD_PHYSLITE, selecting datasets by Rucio name or EOS path,
  delivering data as awkward arrays, using servicex_analysis_utils helpers,
  debugging ServiceX cache or backend issues, or initializing ServiceX with
  servicex init.
---

# ServiceX

## Overview

ServiceX is a data delivery service for ATLAS: you submit a query against a
dataset (identified by Rucio name or EOS path), and ServiceX runs the
transformation on CERN infrastructure and streams results back as files you can
load into Python. It eliminates the need to download full data files locally
before analysis.

ServiceX supports two query backends:

| Backend     | Best for                            | Speed  |
| ----------- | ----------------------------------- | ------ |
| `UprootRaw` | ROOT NTuples / flat data structures | Fast   |
| `FuncADL`   | xAOD derivations (PHYSLITE / PHYS)  | Slower |

**Start with `UprootRaw`** unless you specifically need xAOD object access.

## When to Use

- Fetching specific branches from ROOT NTuples stored in Rucio or EOS
- Extracting columns from DAOD_PHYS or DAOD_PHYSLITE without downloading full
  xAOD files
- Iterating quickly on object selection before committing to a full NTuple
  production
- Analysis facility workflows where ATLAS grid access is not available locally
- ATLAS Open Data workflows (atlasopenmagic-mcp provides dataset containers)

## Setup

**Install required packages:**

```bash
pip install servicex servicex-analysis-utils awkward matplotlib
# For FuncADL xAOD queries only:
pip install func_adl_servicex_xaodr25
```

**Initialize the client (one-time per environment):**

```bash
servicex init
```

This launches a wizard: select your analysis facility, follow the sign-in link,
copy the token from the page, and paste it when prompted. Accept the default
downloads directory. You'll see "Configuration Complete" when done.

## Key Concepts

| Concept                   | Notes                                                                     |
| ------------------------- | ------------------------------------------------------------------------- |
| `deliver(spec)`           | Main entry point — returns `{sample_name: [Path, ...]}` of result files   |
| `ServiceXSpec` / `Sample` | Wrap dataset + query + options into a typed spec object                   |
| `dataset.Rucio(...)`      | Dataset stored in Rucio (GRID); pass the full DID string                  |
| `dataset.FileList([...])` | Dataset accessible via URL (EOS, xrootd, https)                           |
| `query.UprootRaw([...])`  | Uproot backend: select branches and cuts from a ROOT tree                 |
| `FuncADLQueryPHYSLITE`    | FuncADL backend: LINQ-style queries against ATLAS xAOD derivations        |
| `NFiles=1`                | Limit files for testing — always use `NFiles=1` in development            |
| `ignore_local_cache=True` | Forces re-delivery; use when debugging stale results                      |
| `to_awk(results)`         | From `servicex_analysis_utils` — loads result files into an awkward array |

## Canonical Patterns

### Uproot Backend (NTuples — recommended starting point)

```python
from servicex import deliver, ServiceXSpec, Sample, dataset, query
from servicex_analysis_utils import to_awk

# Dataset in Rucio:
ntuple_dataset = dataset.Rucio("user.atlas:my-ntuple-dataset.root")
# Or from EOS:
# ntuple_dataset = dataset.FileList(["root://eospublic.cern.ch//eos/path/to/file.root"])

uproot_query = query.UprootRaw([{
    "treename": "reco",
    "filter_name": ["jet_pt", "jet_eta", "met"],
    "cut": "(jet_pt > 20000)"   # cuts use branch names directly, in native units
}])

spec = ServiceXSpec(
    Sample=[
        Sample(
            Name="my_sample",
            Dataset=ntuple_dataset,
            Query=uproot_query,
            NFiles=1,           # always 1 during development
        )
    ]
)

results = deliver(spec)

# Load into awkward array
arr = to_awk(results)["my_sample"]
jet_pt_GeV = arr["jet_pt"] / 1000.0  # convert MeV → GeV
```

### FuncADL Backend (xAOD / PHYSLITE)

```python
from servicex import deliver, ServiceXSpec, Sample, dataset
from servicex_analysis_utils import to_awk
from func_adl_servicex_xaodr25 import FuncADLQueryPHYSLITE

rucio_dataset = dataset.Rucio(
    "mc23_13p6TeV:mc23_13p6TeV.801167.Py8EG_A14NNPDF23LO_jj_JZ2"
    ".deriv.DAOD_PHYSLITE.e8514_e8528_a911_s4114_r15224_r15225_p6697"
)

base_query = FuncADLQueryPHYSLITE()

# Two-Select pattern: first collect objects, then extract columns
jet_query = (
    base_query
    .Select(lambda e: {"jets": e.Jets()})
    .Select(lambda c: {
        "jet_pt":  c.jets.Select(lambda j: j.pt() / 1000.0),  # GeV
        "jet_eta": c.jets.Select(lambda j: j.eta()),
    })
)

spec = ServiceXSpec(
    Sample=[
        Sample(
            Name="jet_pt_fetch",
            Dataset=rucio_dataset,
            Query=jet_query,
            NFiles=1,
        )
    ]
)

results = deliver(spec)
arr = to_awk(results)["jet_pt_fetch"]
```

### Multiple Samples in One Call

```python
spec = ServiceXSpec(
    Sample=[
        Sample(Name="signal",  Dataset=dataset.Rucio(sig_did),  Query=query, NFiles=5),
        Sample(Name="ttbar",   Dataset=dataset.Rucio(tt_did),   Query=query, NFiles=5),
    ]
)
results = deliver(spec)
sig_arr  = to_awk(results)["signal"]
ttbar_arr = to_awk(results)["ttbar"]
```

### Working with Result Files Directly

For large datasets that don't fit in memory, use the file paths from `deliver`:

```python
file_paths = [str(p) for p in results["my_sample"]]
# Then open with uproot, RDataFrame, etc.
import uproot
for path in file_paths:
    with uproot.open(path) as f:
        arr = f["reco"].arrays()
```

### Cache Bypass

```python
results = deliver(spec, ignore_local_cache=True)
```

### CLI `--n-files` Pattern

```python
import typer
app = typer.Typer()

@app.command()
def main(n_files: int = typer.Option(1, "-n", "--n-files", help="Files to process (0=all)")):
    spec = ServiceXSpec(
        Sample=[Sample(Name="data", Dataset=ds, Query=q, NFiles=n_files or None)]
    )
    results = deliver(spec)
```

## FuncADL: Filtering and Multiple Collections

**Object-level filter (reduce data shipped):**

```python
query = (FuncADLQueryPHYSLITE()
    .Select(lambda e: {"jets": e.Jets().Where(lambda j: j.pt() / 1000.0 > 30.0)})
    .Select(lambda c: {"jet_pt": c.jets.Select(lambda j: j.pt() / 1000.0)})
)
```

**Event-level filter:**

```python
query = (FuncADLQueryPHYSLITE()
    .Where(lambda e: e.Jets().Where(lambda j: j.pt() / 1000.0 > 30.0).Count() >= 2)
    .Select(lambda e: {"n_jets": e.Jets().Count()})
)
```

**Multiple collections (electrons + muons):**

```python
query = (FuncADLQueryPHYSLITE()
    .Select(lambda e: {
        "ele": e.Electrons().Where(lambda e: e.pt() / 1000.0 > 30.0),
        "mu":  e.Muons().Where(lambda m: abs(m.eta()) < 2.5),
    })
    .Select(lambda c: {
        "ele_pt":  c.ele.Select(lambda e: e.pt() / 1000.0),
        "ele_eta": c.ele.Select(lambda e: e.eta()),
        "mu_pt":   c.mu.Select(lambda m: m.pt() / 1000.0),
        "mu_eta":  c.mu.Select(lambda m: m.eta()),
    })
)
```

Any collection accessed in the second `Select` must be passed through from the
first. Never nest a dictionary inside another dictionary — that causes a crash.

## Query Backend Selection

| Situation                                       | Use                    |
| ----------------------------------------------- | ---------------------- |
| Dataset name contains `PHYSLITE`                | `FuncADLQueryPHYSLITE` |
| Dataset name contains `DAOD_PHYS`               | `FuncADLQueryPHYS`     |
| ATLAS OpenData (usually has "OpenData" in name) | `FuncADLQueryPHYSLITE` |
| Working with ROOT NTuples / flat trees          | `query.UprootRaw`      |
| Not sure — start here                           | `query.UprootRaw`      |

For `FuncADLQueryPHYS` (non-PHYSLITE derivations), calibrations run
automatically. Pass `calibrated=False` to a collection to skip calibration, but
note that PHYSLITE has no uncalibrated objects.

## PHYSLITE vs PHYS

| Feature            | PHYSLITE                                  | PHYS                                    |
| ------------------ | ----------------------------------------- | --------------------------------------- |
| Size               | ~10× smaller                              | Full derivation                         |
| Object collections | `AnalysisJets`, `AnalysisElectrons`, etc. | `AntiKt4EMPFlowJets`, `Electrons`, etc. |
| CP recommendations | Default CP tools configured               | Requires manual tool setup              |
| Availability       | Most mc20/mc23 campaigns                  | All campaigns                           |

## xAOD Object Names (PHYSLITE)

| Object    | FuncADL accessor         |
| --------- | ------------------------ |
| Jets      | `e.Jets()`               |
| Electrons | `e.Electrons()`          |
| Muons     | `e.Muons()`              |
| Taus      | `e.TauJets()`            |
| Photons   | `e.Photons()`            |
| MET       | `e.MissingETContainer()` |

## Gotchas

- **Units are MeV in xAOD**: `j.pt()` returns MeV. Divide by 1000 before any
  GeV-scale comparisons or histograms.
- **Units in UprootRaw cuts are native**: NTuple branch cuts use whatever units
  are in the tree (often MeV for ATLAS NTuples — check your sample).
- **Cache is aggressive**: If you fix a query bug but get the same result, use
  `ignore_local_cache=True`. Do not use `ignore_cache=True` (old API, no-op).
- **`NFiles=None` means all files**: `NFiles=0` behavior is undefined — use
  `None` for full dataset or a positive integer for testing.
- **Call `deliver` once**: Put all samples in one `ServiceXSpec`. Multiple
  `deliver` calls waste round trips.
- **No awkward in FuncADL queries**: Use `Select` / `Where` instead — awkward
  functions are not available inside the lambda DSL.
- **PHYSLITE vs PHYS collection names differ**: Using the wrong collection name
  (e.g. `AntiKt4EMPFlowJets` on PHYSLITE) returns empty results silently.
- **FuncADL requires `func_adl_servicex_xaodr25`**: Install separately; not
  included in the base `servicex` package.
- **Transform failures**: "Transform completed with failures" errors need the
  user to click the provided link — only the job owner can see the logs. If you
  see this after fixing type errors, involve the user.

## Worked Example — UprootRaw Histogram

```python
from servicex import deliver, ServiceXSpec, Sample, dataset, query
from servicex_analysis_utils import to_awk
import awkward as ak
import matplotlib.pyplot as plt

ntuple_dataset = dataset.Rucio("user.atlas:my-displaced-signal.root")

uproot_query = query.UprootRaw([{
    "treename": "reco",
    "filter_name": ["truth_alp_decayVtxX", "truth_alp_decayVtxY",
                    "truth_alp_pt", "truth_alp_eta",
                    "jet_EMFrac_NOSYS", "jet_pt_NOSYS"],
    "cut": "(num(jet_pt_NOSYS) < 2) & any((truth_alp_pt > 20) & (abs(truth_alp_eta) < 0.8))"
}])

results = deliver(ServiceXSpec(
    Sample=[Sample(Name="signal", Dataset=ntuple_dataset, Query=uproot_query, NFiles=1)]
))

arr = to_awk(results)["signal"]
displacement = (arr["truth_alp_decayVtxX"]**2 + arr["truth_alp_decayVtxY"]**2)**0.5

fig, axes = plt.subplots(1, 2, figsize=(9, 4))
axes[0].hist(ak.flatten(arr["jet_EMFrac_NOSYS"]), bins=50, range=[0, 1])
axes[0].set_xlabel("EM Fraction")
axes[1].hist(ak.flatten(displacement), bins=50, range=[0, 5000], color="g")
axes[1].set_xlabel("Decay Vertex Displacement (mm)")
plt.tight_layout()
plt.show()
```

## Troubleshooting

| Symptom                                | Likely Cause                         | Fix                                     |
| -------------------------------------- | ------------------------------------ | --------------------------------------- |
| Same result after query fix            | Cached result returned               | Add `ignore_local_cache=True`           |
| Empty array for a collection           | Wrong collection name for derivation | Check PHYSLITE vs PHYS names            |
| `ModuleNotFoundError: func_adl...`     | FuncADL package not installed        | `pip install func_adl_servicex_xaodr25` |
| `ModuleNotFoundError: servicex_anal..` | Utils package missing                | `pip install servicex-analysis-utils`   |
| "Transform completed with failures"    | C++ error in backend                 | Involve user — only they can see logs   |
| "Method xxx not found on object"       | Wrong accessor for this derivation   | Check xAOD object schema for your type  |
| `servicex init` not found              | CLI not installed                    | `pip install servicex` then retry       |

## Interop

- **servicex_analysis_utils**: `to_awk(results)` is the standard way to load
  ServiceX output into an awkward array for in-memory analyses
- **uproot**: For local ROOT files, use uproot directly — ServiceX only adds
  value for remote or large datasets
- **awkward**: Results from `to_awk` are `ak.Array` — use awkward operations for
  filtering, flattening, and array math
- **Rucio/AMI**: Use `ami-mcp` or `rucio-mcp` to find dataset DIDs before
  querying ServiceX
- **atlasopenmagic-mcp**: Provides ATLAS Open Data dataset identifiers ready for
  use with `dataset.Rucio(...)` or `dataset.FileList([...])`

## Docs

- ServiceX client: https://servicex.readthedocs.io/en/latest/
- FuncADL xAOD R25: https://github.com/iris-hep/func_adl_servicex_xaodr25
- tryservicex.org tutorial: https://tryservicex.org
- servicex-analysis-utils: https://github.com/iris-hep/servicex_analysis_utils
