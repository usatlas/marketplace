---
name: pyhf
description: >-
  Use when building or running a HistFactory statistical model in Python:
  creating a pyhf workspace from JSON, defining signal and background samples
  with systematic modifiers (normfactor, histosys, staterror), running a profile
  likelihood fit, computing CLs exclusion limits or discovery significance,
  patching workspaces, or converting between HistFactory XML and pyhf JSON
  format.
---

# pyhf

## Overview

pyhf implements the HistFactory statistical model in pure Python
(NumPy/JAX/PyTorch backends). A workspace is a JSON document describing
histograms, samples, and systematic modifiers; pyhf builds a differentiable
likelihood from it and provides frequentist inference tools. It is the preferred
fitting framework for new ATLAS analyses.

## When to Use

- Building a profile likelihood fit for a search or measurement
- Computing CLs exclusion limits on a signal model
- Computing discovery significance (q₀ test statistic)
- Patching or combining HistFactory workspaces
- Validating a HistFactory XML workspace from TRExFitter/HistFitter

## Key Concepts

| Concept               | Notes                                                        |
| --------------------- | ------------------------------------------------------------ |
| `pyhf.Workspace`      | JSON schema-validated workspace object                       |
| `pyhf.Model`          | Differentiable likelihood built from a workspace             |
| Modifier types        | `normfactor`, `histosys`, `normsys`, `staterror`, `shapesys` |
| `pyhf.infer.hypotest` | CLs hypothesis test                                          |
| `pyhf.infer.mle.fit`  | Maximum likelihood fit                                       |
| Backends              | `numpy` (default), `jax`, `pytorch`, `tensorflow`            |

## Workspace JSON Structure

```json
{
  "channels": [
    {
      "name": "SR",
      "samples": [
        {
          "name": "signal",
          "data": [10.0, 15.0, 8.0],
          "modifiers": [
            { "name": "mu_sig", "type": "normfactor", "data": null },
            {
              "name": "JES",
              "type": "histosys",
              "data": {
                "hi_data": [11.0, 16.5, 8.8],
                "lo_data": [9.0, 13.5, 7.2]
              }
            }
          ]
        },
        {
          "name": "ttbar",
          "data": [100.0, 80.0, 40.0],
          "modifiers": [
            { "name": "mu_ttbar", "type": "normfactor", "data": null },
            {
              "name": "JES",
              "type": "histosys",
              "data": {
                "hi_data": [110.0, 88.0, 44.0],
                "lo_data": [90.0, 72.0, 36.0]
              }
            },
            {
              "name": "staterror_SR",
              "type": "staterror",
              "data": [3.16, 2.83, 2.0]
            }
          ]
        }
      ]
    }
  ],
  "observations": [{ "name": "SR", "data": [115.0, 95.0, 48.0] }],
  "measurements": [
    {
      "name": "measurement",
      "config": {
        "poi": "mu_sig",
        "parameters": [{ "name": "mu_ttbar", "bounds": [[0.5, 2.0]] }]
      }
    }
  ],
  "version": "1.0.0"
}
```

## Canonical Patterns

**Load workspace and build model**:

```python
import json, pyhf

with open("workspace.json") as f:
    spec = json.load(f)

ws = pyhf.Workspace(spec)
model = ws.model()
data = ws.data(model)
```

**Background-only fit (best-fit NPs)**:

```python
result = pyhf.infer.mle.fit(data, model)
bestfit_pars, fit_obj = result
print("Best-fit NPs:", dict(zip(model.config.par_names, bestfit_pars)))
```

**CLs upper limit on signal strength**:

```python
obs_limit, exp_limits, _ = pyhf.infer.intervals.upper_limits.upper_limit(
    data, model, scan=np.linspace(0, 5, 51), return_expected_set=True
)
print(f"Observed: μ < {obs_limit:.2f}")
print(f"Expected: μ < {exp_limits[2]:.2f} (+1σ: {exp_limits[3]:.2f}, -1σ: {exp_limits[1]:.2f})")
```

**Discovery significance (q₀ test)**:

```python
p_value, test_stat = pyhf.infer.hypotest(
    0.0,  # test μ=0 (background-only hypothesis)
    data, model,
    test_stat="q0",
    return_expected=True,
)
significance = pyhf.tensorlib.abs(pyhf.tensorlib.normal_cdf(p_value))
```

**Patch a workspace (e.g., inject a new signal)**:

```python
patch = [
    {"op": "replace", "path": "/channels/0/samples/0/data", "value": [12.0, 18.0, 9.0]}
]
patched_ws = ws.model(patches=patch)
```

**JAX backend for gradient-based fits**:

```python
pyhf.set_backend("jax")
# All subsequent pyhf operations use JAX
```

## Modifier Reference

| Modifier     | JSON type                          | Use case                                |
| ------------ | ---------------------------------- | --------------------------------------- |
| `normfactor` | Free normalization                 | CR-driven background, signal strength μ |
| `histosys`   | Shape+norm from ±1σ templates      | JES, JER, generator comparisons         |
| `normsys`    | Normalization-only from log-normal | Luminosity, cross-section uncertainty   |
| `staterror`  | Per-bin MC statistical             | Barlow-Beeston lite                     |
| `shapesys`   | Per-bin free shape                 | Rarely used; use staterror instead      |

## Worked Example: ttbar search with one CR

```python
import json, pyhf, numpy as np

spec = {
    "channels": [
        {"name": "SR", "samples": [
            {"name": "sig", "data": [5., 8., 4.],
             "modifiers": [{"name": "mu", "type": "normfactor", "data": None}]},
            {"name": "bkg", "data": [50., 60., 30.],
             "modifiers": [
                 {"name": "mu_bkg", "type": "normfactor", "data": None},
                 {"name": "lumi", "type": "normsys", "data": {"hi": 1.015, "lo": 0.985}},
                 {"name": "staterror_SR", "type": "staterror", "data": [2.2, 2.4, 1.7]}
             ]}
        ]},
        {"name": "CR", "samples": [
            {"name": "bkg", "data": [200., 190., 180.],
             "modifiers": [
                 {"name": "mu_bkg", "type": "normfactor", "data": None},
                 {"name": "lumi", "type": "normsys", "data": {"hi": 1.015, "lo": 0.985}},
                 {"name": "staterror_CR", "type": "staterror", "data": [4.5, 4.4, 4.2]}
             ]}
        ]}
    ],
    "observations": [
        {"name": "SR", "data": [55., 68., 34.]},
        {"name": "CR", "data": [198., 192., 175.]}
    ],
    "measurements": [{"name": "fit", "config": {"poi": "mu",
        "parameters": [{"name": "mu_bkg", "bounds": [[0.5, 2.0]]}]}}],
    "version": "1.0.0"
}

ws = pyhf.Workspace(spec)
model = ws.model()
data = ws.data(model)

bestfit, _ = pyhf.infer.mle.fit(data, model, return_fitted_val=True)
obs_limit, *_ = pyhf.infer.intervals.upper_limits.upper_limit(
    data, model, scan=np.linspace(0, 10, 51)
)
print(f"Observed limit: μ < {obs_limit:.2f} @ 95% CL")
```

## Troubleshooting

| Symptom                                | Cause                                    | Fix                                                      |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------------------- |
| `pyhf.exceptions.InvalidSpecification` | JSON doesn't match HistFactory schema    | Run `pyhf.Workspace(spec)` and read the validation error |
| Fit converges to boundary              | Parameter bounded away from true minimum | Widen bounds in `measurements.config.parameters`         |
| `nan` in likelihood                    | Empty bin or division by zero            | Add small regularisation or merge bins                   |
| Expected limit varies wildly           | Too few Asimov toy statistics            | Check background yields — should be > 10 events/bin      |
| NP pulled strongly                     | Template inconsistent with data          | Inspect pre-fit data/MC in that region                   |

## Interop

- **cabinetry**: high-level wrapper that builds pyhf workspaces from config +
  histograms
- **pyhs3**: schema-compliant serialisation of pyhf workspaces
- **hist**: convert `Hist` objects to numpy arrays for workspace construction
- **TRExFitter**: can export HistFactory XML → convert with `pyhf xml2json`

## Docs

https://pyhf.readthedocs.io/en/latest/
