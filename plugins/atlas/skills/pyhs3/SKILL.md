---
name: pyhs3
description: >-
  Use when reading, writing, or validating binned and/or unbinned statistical
  models in the HS3 (HEP Statistics Serialization Standard) JSON format:
  converting between HistFactory (HiFa) JSON and HS3 schema, checking schema
  compliance, archiving workspaces for publication, or working with the
  standardized JSON format for ATLAS statistical models.
---

# pyhs3

## Overview

pyhs3 implements the HEP Statistics Serialization Standard (HS3) — a JSON schema
for describing statistical models in a backend-agnostic way. HS3 extends
HistFactory JSON with stricter schema validation and additional model types. For
ATLAS analyses, pyhs3 is used to archive workspaces in a publication-ready
format and to validate workspaces against the HS3 standard.

## When to Use

- Archiving a statistical workspace for publication (HEPData, ATLAS open data)
- Validating that a workspace is HS3-compliant
- Reading HS3-format workspaces from published ATLAS results
- Working with models that go beyond standard HistFactory (custom PDFs)

## Key Concepts

| Concept           | Notes                                         |
| ----------------- | --------------------------------------------- |
| HS3 JSON          | JSON serialization of HS3 spec                |
| `pyhs3.Workspace` | Reads HS3 JSON, validates against schema      |
| `pyhs3.to_hifa`   | Convert HS3 workspace to HiFa-compatible dict |
| `pyhs3.from_hifa` | Convert HistFactory workspace to HS3 format   |

## Canonical Patterns

**Validate a HiFa workspace against HS3 schema**:

```python
import pyhs3, json

with open("workspace.json") as f:
    spec = json.load(f)

# Convert hifa format to HS3 and validate
hs3_spec = pyhs3.from_hifa(spec)
ws = pyhs3.Workspace(hs3_spec)   # raises if invalid
print("Workspace is HS3-compliant")
```

**Read a published HS3 workspace**:

```python
import pyhs3, json

with open("atlas_result_hs3.json") as f:
    hs3_spec = json.load(f)

ws = pyhs3.Workspace(hs3_spec)
hifa_spec = pyhs3.to_hifa(hs3_spec)

import pyhf
model = pyhf.Workspace(hifa_spec).model()
```

**Save a cabinetry workspace in HS3 format**:

```python
import cabinetry, pyhs3, json

workspace = cabinetry.workspace.build(config)
hs3_workspace = pyhs3.from_hifa(workspace)

with open("workspace_hs3.json", "w") as f:
    json.dump(hs3_workspace, f, indent=2)
```

**Check schema version**:

```python
print(pyhs3.__version__)        # pyhs3 library version
print(hs3_spec.get("version"))  # HS3 schema version in the file
```

## HS3 vs HiFa JSON

| Feature               | HiFa JSON     | HS3 JSON                  |
| --------------------- | ------------- | ------------------------- |
| Schema                | pyhf-specific | Standardized              |
| Backend-agnostic      | pyhf only     | Designed for any backend  |
| Metadata              | Minimal       | Rich (authors, doi, etc.) |
| Custom PDFs           | No            | Yes (type-tagged)         |
| HEPData compatibility | Partial       | Full                      |

## Gotchas

- **HS3 is stricter than HistFactory JSON**: A valid HiFa workspace may not be
  HS3-compliant; `pyhs3.from_hifa` may reject unusual modifier combinations.
- **Version drift**: The HS3 standard is evolving; check the version tag in the
  file matches what pyhs3 expects.
- **Round-trip fidelity**: `from_hifa` → `to_hifa` should reproduce the
  original, but floating-point formatting may differ; compare numerically not
  textually.

## Interop

- **pyhf**: `pyhs3.to_hifa()` / `pyhs3.from_hifa()` — the primary conversion
  interface
- **cabinetry**: build workspace with cabinetry, then convert to HS3 for
  archiving
- **HEPData**: HS3 JSON is the accepted format for ATLAS result uploads

## Docs

https://pyhs3.readthedocs.io/en/latest/
