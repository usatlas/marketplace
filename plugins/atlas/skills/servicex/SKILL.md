---
name: servicex
description: >-
  Use when querying ATLAS xAOD data remotely via ServiceX: writing func_adl
  queries against DAOD_PHYS or DAOD_PHYSLITE, selecting datasets by Rucio name
  or AMI tag, delivering data as awkward arrays, debugging ServiceX cache or
  backend issues, or choosing between PHYSLITE and PHYS backends for an
  analysis.
---

# ServiceX

## Overview

ServiceX is a data delivery service for ATLAS: you submit a `func_adl` query
against a dataset (identified by Rucio name), and ServiceX runs the selection on
CERN infrastructure and streams results back as awkward arrays. It eliminates
the need to download full xAOD files for analysis.

## When to Use

- Extracting columns from DAOD_PHYS or DAOD_PHYSLITE without downloading full
  xAOD
- Iterating quickly on object selection before committing to a full NTuple
  production
- Analysis facility workflows where ATLAS grid access is not available locally
- ATLAS Open Data workflows (atlasopenmagic-mcp provides the dataset containers)

## Key Concepts

| Concept                   | Notes                                                                  |
| ------------------------- | ---------------------------------------------------------------------- |
| `servicex.deliver(query)` | Main entry point — returns dict of `{sample_name: ak.Array}`           |
| `func_adl`                | Query DSL: `from_xaod("EventInfo").Select(...)`                        |
| PHYSLITE                  | Slimmed derivation — preferred; smaller, most CP-recommended variables |
| PHYS                      | Full DAOD — use when PHYSLITE lacks required variables                 |
| `ignore_cache=True`       | Forces re-delivery; use when debugging stale results                   |
| `max_files=N`             | Limit files for quick tests — always use `max_files=1` in development  |

## Canonical Patterns

**Minimal complete example — fetch jet pT from PHYSLITE**:

```python
import servicex
from func_adl_servicex import ServiceXSourceXAOD

dataset = "user.atlas:mc20a_DAOD_PHYSLITE_ttbar"   # Rucio dataset name

query = (
    ServiceXSourceXAOD(dataset, backend_name="xaod_uproot")
    .SelectMany("lambda e: e.Jets('AnalysisJets')")
    .Select("lambda j: {'pt': j.pt(), 'eta': j.eta(), 'phi': j.phi(), 'm': j.m()}")
    .AsPandasDF()   # or .AsAwkwardArray()
)

result = servicex.deliver(query, max_files=1)
```

**Async delivery for multiple samples**:

```python
import servicex, asyncio

queries = {"signal": query_sig, "ttbar": query_ttbar}
results = asyncio.run(servicex.deliver_async(queries, max_files=5))
```

**Control number of files from a Typer CLI**:

```python
import typer
app = typer.Typer()

@app.command()
def main(nfiles: int = typer.Option(0, help="Max files (0 = all)")):
    result = servicex.deliver(query, max_files=nfiles or None)
```

**Force fresh delivery (bypass cache)**:

```python
result = servicex.deliver(query, ignore_cache=True)
```

## PHYSLITE vs PHYS

| Feature            | PHYSLITE                                  | PHYS                                    |
| ------------------ | ----------------------------------------- | --------------------------------------- |
| Size               | ~10× smaller                              | Full derivation                         |
| Object collections | `AnalysisJets`, `AnalysisElectrons`, etc. | `AntiKt4EMPFlowJets`, `Electrons`, etc. |
| CP recommendations | Default CP tools configured               | Requires manual tool setup              |
| Availability       | Most mc20/mc23 campaigns                  | All campaigns                           |

When in doubt, start with PHYSLITE and switch to PHYS only if a required
variable is missing.

## xAOD Object Names (PHYSLITE)

| Object    | Collection name     |
| --------- | ------------------- |
| Jets      | `AnalysisJets`      |
| Electrons | `AnalysisElectrons` |
| Muons     | `AnalysisMuons`     |
| Taus      | `AnalysisTauJets`   |
| MET       | `AnalysisMET_Core`  |
| Photons   | `AnalysisPhotons`   |

## Gotchas

- **Cache is aggressive**: If you fix a bug in your query but get the same
  result, add `ignore_cache=True`.
- **PHYSLITE vs PHYS collection names differ**: `AnalysisJets` (PHYSLITE) vs
  `AntiKt4EMPFlowJets` (PHYS). Using the wrong name returns an empty result
  silently.
- **`max_files=0` vs `max_files=None`**: Behavior varies by ServiceX version —
  always use an explicit positive integer for testing or `None` for full
  dataset.
- **Backend selection**: The `backend_name` must match what's configured for
  your ServiceX instance. ATLAS instances typically have `xaod_uproot` and
  `xaod_cpp`.
- **Units**: ServiceX returns values in the xAOD native units — pT in MeV.
  Divide by 1000 before analysis.

## Interop

- **awkward**: `.AsAwkwardArray()` returns `ak.Array` directly — preferred over
  `.AsPandasDF()` for HEP workflows
- **Rucio/AMI**: Use `ami-mcp` or `rucio-mcp` to find dataset containers before
  querying
- **atlasopenmagic-mcp**: Use to get ATLAS Open Data dataset identifiers for
  ServiceX queries
- **uproot**: For local ROOT files, uproot is simpler and faster — ServiceX only
  makes sense for remote xAOD

## Docs

https://servicex.readthedocs.io/en/latest/
