---
name: pyhs3
description: >-
  Use when reading, writing, or validating binned and/or unbinned statistical
  models in the HS3 (HEP Statistics Serialization Standard) JSON format: loading
  an HS3 workspace, validating schema compliance, building and evaluating a
  model (logpdf), serialising a workspace for publication, or working with the
  standardized JSON format for ATLAS statistical models.
---

# pyhs3

## Overview

pyhs3 is a pure-Python implementation of the HEP Statistics Serialization
Standard (HS3) — a JSON schema for describing statistical models in a
backend-agnostic way. A workspace is a single document made of `metadata`,
`distributions`, `functions`, `domains`, `parameter_points`, `data`,
`likelihoods`, and `analyses`. pyhs3 parses and validates that document with
pydantic, then compiles it (via PyTensor) into an evaluable model. HistFactory
models are expressed **natively** as HS3 distribution types
(`HistFactoryDistChannel` with `normsys`/`histosys`/`shapesys`/`staterror`
modifiers) — there is no separate "convert from pyhf" step. For ATLAS analyses,
pyhs3 is used to archive and validate publication-ready workspaces in the HS3
standard.

## When to Use

- Loading and validating an HS3-format workspace from a published ATLAS result
- Checking that a workspace dict is HS3-compliant (pydantic validation)
- Building a statistical model from HS3 JSON and evaluating its (log)pdf
- Serialising a workspace back to a dict for archiving (HEPData, ATLAS open
  data)
- Working with models that go beyond standard HistFactory (analytic/custom PDFs)

## Key Concepts

| Concept                      | Notes                                                                   |
| ---------------------------- | ----------------------------------------------------------------------- |
| HS3 JSON                     | Backend-agnostic JSON serialization of a statistical model              |
| `pyhs3.Workspace`            | Pydantic model; `Workspace(**spec)` validates on construction           |
| `Workspace.load(path)`       | Classmethod: load + validate an HS3 JSON file                           |
| `ws.model(target)`           | Compile a `Model` (target = domain index, name, or Analysis/Likelihood) |
| `model.logpdf(name, **pars)` | Evaluate log-pdf of a distribution by name                              |
| `model.pdf(name, **pars)`    | Evaluate pdf (strict: parameter values must be numpy arrays)            |
| `ws.model_dump()`            | Serialise the workspace back to a dict (pydantic)                       |
| `pyhs3.Model`                | Compiled model object exposing `logpdf`, `pdf`, `log_prob`              |
| `metadata.hs3_version`       | HS3 schema version recorded in the file                                 |

HistFactory pieces live under `pyhs3.distributions.histfactory` (e.g.
`HistFactoryDistChannel`) and the modifier classes (`NormSysModifier`,
`HistoSysModifier`, `ShapeSysModifier`, `StatErrorModifier`).

## Canonical Patterns

**Load and validate an HS3 workspace from a file**:

```python
import pyhs3

# Validates against the HS3 schema; raises WorkspaceValidationError if invalid
ws = pyhs3.Workspace.load("atlas_result_hs3.json")
print("Workspace is HS3-compliant")
```

**Build a workspace from an HS3 JSON-like dict**:

```python
import pyhs3

workspace_data = {
    "metadata": {"hs3_version": "0.2"},
    "distributions": [
        {"name": "model", "type": "gaussian_dist", "x": "x", "mean": "mu", "sigma": "sigma"}
    ],
    "parameter_points": [
        {"name": "default_values", "parameters": [
            {"name": "x", "value": 0.0},
            {"name": "mu", "value": 0.0},
            {"name": "sigma", "value": 1.0},
        ]}
    ],
    "domains": [
        {"name": "default_domain", "type": "product_domain", "axes": [
            {"name": "x", "min": -5.0, "max": 5.0},
            {"name": "mu", "min": -2.0, "max": 2.0},
            {"name": "sigma", "min": 0.1, "max": 3.0},
        ]}
    ],
}

ws = pyhs3.Workspace(**workspace_data)   # raises if invalid
```

**Compile a model and evaluate its log-pdf**:

```python
import numpy as np

model = ws.model(0)   # target 0 = first domain (legacy index path)

# logpdf takes the distribution name and parameter values as numpy arrays
pars = {par.name: np.array(par.value) for par in model.parameterset}
nll = -2 * model.logpdf("model", **pars)
print(f"nll: {float(nll):.8f}")
```

**Build the workspace from Python objects (instead of a dict)**:

```python
import pyhs3
from pyhs3.distributions import GaussianDist
from pyhs3.parameter_points import ParameterPoint, ParameterSet
from pyhs3.domains import ProductDomain
from pyhs3.metadata import Metadata

ws = pyhs3.Workspace(
    metadata=Metadata(hs3_version="0.2"),
    distributions=[GaussianDist(name="model", x="x", mean="mu", sigma="sigma")],
    parameter_points=[ParameterSet(name="default_values", parameters=[
        ParameterPoint(name="x", value=0.0),
        ParameterPoint(name="mu", value=0.0),
        ParameterPoint(name="sigma", value=1.0),
    ])],
    domains=[ProductDomain(name="default_domain", axes=[
        dict(name="x", min=-5.0, max=5.0),
        dict(name="mu", min=-2.0, max=2.0),
        dict(name="sigma", min=0.1, max=3.0),
    ])],
)
```

**Serialise a workspace for archiving (round-trip)**:

```python
import json

spec = ws.model_dump()        # back to a plain dict
with open("workspace_hs3.json", "w") as f:
    json.dump(spec, f, indent=2, default=str)

# Reconstruct from the serialised dict
ws_roundtrip = pyhs3.Workspace(**ws.model_dump())
```

**Check versions**:

```python
print(pyhs3.__version__)              # pyhs3 library version
print(ws.metadata.hs3_version)        # HS3 schema version recorded in the workspace
```

## Gotchas

- **No `from_hifa` / `to_hifa` functions**: pyhs3 does not import pyhf and does
  not provide pyhf↔HS3 converters. Build/validate HS3 directly. To go from a
  pyhf workspace to HS3, regenerate the model as HS3 distributions, or use a
  RooFit/ROOT exporter that emits HS3.
- **`Workspace` is a pydantic model**: construct with keyword fields
  (`Workspace(**spec)`), not a single positional dict. Invalid input raises a
  `WorkspaceValidationError` (or pydantic `ValidationError`).
- **`metadata` is required**: every workspace needs `metadata.hs3_version`.
- **`logpdf` / `pdf` are strict**: parameter values must be numpy arrays
  (`np.array(...)`). Use `logpdf_unsafe` / `pdf_unsafe` for automatic
  conversion.
- **`ws.model(target)` needs a target**: pass an integer domain index (legacy
  path), a likelihood/analysis name (string), or an `Analysis`/`Likelihood`
  object — there is no zero-argument `model()`.
- **Version drift**: the HS3 standard is evolving; confirm the `hs3_version` in
  the file matches what your installed pyhs3 supports.
- **JAX is optional**: `pyhs3.jaxify` / `JaxifiedGraph` require the `jax` extra
  (`pip install pyhs3[jax]`).

## HS3 vs HistFactory (HiFa) JSON

| Feature                | HiFa JSON (pyhf) | HS3 JSON                    |
| ---------------------- | ---------------- | --------------------------- |
| Schema                 | pyhf-specific    | Standardized                |
| Backend-agnostic       | pyhf only        | Designed for any backend    |
| Metadata               | Minimal          | Rich (version, attribution) |
| Custom / analytic PDFs | No               | Yes (type-tagged)           |
| Model types            | HistFactory only | HistFactory + analytic      |

HS3 represents HistFactory models with `HistFactoryDistChannel` distributions
and dedicated modifier types, so a HistFactory model is one _kind_ of HS3 model
rather than a foreign format that must be converted.

## Interop

- **pyhf**: HS3 and pyhf's HiFa JSON are distinct schemas; pyhs3 does not
  convert between them. Use pyhf for HiFa-format workspaces and inference.
- **cabinetry / ROOT**: produce a HistFactory model elsewhere, then express or
  export it as HS3 for archiving and validation with pyhs3.
- **HEPData**: HS3 JSON is an accepted format for ATLAS statistical-model
  uploads.

## Docs

https://pyhs3.readthedocs.io/en/latest/
