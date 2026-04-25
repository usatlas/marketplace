---
name: pyhf
description: >-
  Use when building or running a HistFactory statistical model in Python:
  creating a pyhf workspace from JSON, defining signal and background samples
  with systematic modifiers (normfactor, histosys, normsys, staterror, lumi,
  shapefactor), running a profile likelihood fit, computing CLs exclusion limits
  or discovery significance, patching or combining workspaces with PatchSet,
  converting between HistFactory XML and pyhf JSON via the CLI, or using pyhf
  simplemodels for quick hypothesis tests.
---

# pyhf

## Overview

pyhf implements the HistFactory statistical model in pure Python with swappable
tensor backends (NumPy, JAX, PyTorch). A workspace is a self-contained JSON
document describing channels, samples, modifiers, observations, and
measurements; pyhf builds a differentiable likelihood from it and provides
frequentist inference tools (profile likelihood fits, CLs limits, discovery
significance). It is the preferred fitting framework for new ATLAS analyses.

## When to Use

- Building a profile likelihood fit for a search or measurement
- Computing CLs exclusion limits on a signal model
- Computing discovery significance (q₀ test statistic)
- Patching, combining, or reinterpreting HistFactory workspaces
- Validating a HistFactory XML workspace from TRExFitter/HistFitter
- Quick hypothesis tests with `pyhf.simplemodels`
- Converting between HistFactory XML and pyhf JSON via CLI

## Key Concepts

| Concept                   | Notes                                                 |
| ------------------------- | ----------------------------------------------------- |
| `pyhf.Workspace`          | JSON schema-validated workspace object                |
| `pyhf.Model`              | Differentiable likelihood built from a workspace      |
| `pyhf.PatchSet` / `Patch` | Named collection of JSON patches for reinterpretation |
| `pyhf.simplemodels`       | Convenience constructors for common model topologies  |
| Modifier types            | `normfactor`, `histosys`, `normsys`, `staterror`,     |
|                           | `shapesys`, `lumi`, `shapefactor`                     |
| `pyhf.infer.hypotest`     | CLs hypothesis test (asymptotic or toy-based)         |
| `pyhf.infer.mle.fit`      | Maximum likelihood fit                                |
| `pyhf.infer.intervals`    | Upper limit scans (linear grid or TOMS 748)           |
| Backends                  | `numpy` (default), `jax`, `pytorch`                   |
| Test statistics           | `q0`, `qmu`, `qmu_tilde`, `tmu`, `tmu_tilde`          |

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

**Quick model with simplemodels (no JSON needed)**:

```python
import pyhf

model = pyhf.simplemodels.uncorrelated_background(
    signal=[5.0, 10.0], bkg=[50.0, 60.0], bkg_uncertainty=[7.0, 12.0]
)
data = pyhf.tensorlib.astensor([55.0, 65.0]) + model.config.auxdata
```

**Background-only fit (best-fit NPs)**:

```python
bestfit_pars = pyhf.infer.mle.fit(data, model)
print("Best-fit NPs:", dict(zip(model.config.par_names, bestfit_pars)))

bestfit_pars, twice_nll = pyhf.infer.mle.fit(
    data, model, return_fitted_val=True
)
```

**CLs upper limit on signal strength**:

```python
import numpy as np

obs_limit, exp_limits, (scan, results) = pyhf.infer.intervals.upper_limits.upper_limit(
    data, model, scan=np.linspace(0, 5, 51), return_expected_set=True, return_results=True
)
print(f"Observed: μ < {obs_limit:.2f}")
print(f"Expected: μ < {exp_limits[2]:.2f} (+1σ: {exp_limits[3]:.2f}, −1σ: {exp_limits[1]:.2f})")
```

**Discovery significance (q₀ test)**:

```python
from scipy.stats import norm

p_obs, p_exp = pyhf.infer.hypotest(
    0.0, data, model, test_stat="q0", return_expected=True
)
significance = norm.isf(float(p_obs))
print(f"Observed p-value: {float(p_obs):.4e}, significance: {significance:.2f}σ")
```

**Patch a workspace (JSON Patch)**:

```python
patch = [
    {"op": "replace", "path": "/channels/0/samples/0/data", "value": [12.0, 18.0, 9.0]}
]
patched_model = ws.model(patches=patch)
```

**PatchSet for reinterpretation over signal grid**:

```python
patchset = pyhf.PatchSet(patchset_json)
print(patchset)  # lists available signal points

patched_ws = patchset.apply(ws, "signal_500_100")
model = patched_ws.model()
data = patched_ws.data(model)
```

**Brazil band visualization**:

```python
import matplotlib.pyplot as plt
import numpy as np
import pyhf.contrib.viz.brazil

poi_values = np.linspace(0, 5, 51)
results = [
    pyhf.infer.hypotest(
        mu, data, model, return_expected_set=True
    )
    for mu in poi_values
]

fig, ax = plt.subplots()
pyhf.contrib.viz.brazil.plot_results(poi_values, results, ax=ax)
```

**JAX backend for gradient-based fits**:

```python
pyhf.set_backend("jax")
```

**CLI commands**:

```bash
pyhf xml2json config/analysis.xml --output-file workspace.json
pyhf json2xml workspace.json --output-dir xml_output/
pyhf cls workspace.json                    # run CLs limit
pyhf cls workspace.json --backend jax      # with specific backend
pyhf inspect workspace.json                # print workspace summary
pyhf patchset apply ws.json patchset.json --name "signal_500_100"
pyhf digest workspace.json                 # SHA256 digest for reproducibility
```

## Modifier Reference

| Modifier      | JSON `data` field                      | Constraint    | Use case                                 |
| ------------- | -------------------------------------- | ------------- | ---------------------------------------- |
| `normfactor`  | `null`                                 | Unconstrained | Signal strength μ, CR-driven background  |
| `histosys`    | `{"hi_data": [...], "lo_data": [...]}` | Gaussian(α)   | JES, JER, generator comparisons          |
| `normsys`     | `{"hi": float, "lo": float}`           | Gaussian(α)   | Luminosity, cross-section uncertainty    |
| `staterror`   | `[abs_unc_per_bin]`                    | Gaussian(γ)   | MC statistical (Barlow–Beeston lite)     |
| `shapesys`    | `[abs_unc_per_bin]`                    | Poisson(γ)    | Uncorrelated per-bin shape               |
| `lumi`        | `null`                                 | Gaussian(λ)   | Luminosity (global, set via measurement) |
| `shapefactor` | `null`                                 | Unconstrained | Data-driven shape (free per-bin γ)       |

## Measurement Configuration

Override parameter defaults in `measurements[].config.parameters`:

```json
{
  "name": "fit",
  "config": {
    "poi": "mu",
    "parameters": [
      {
        "name": "lumi",
        "auxdata": [1.0],
        "sigmas": [0.017],
        "bounds": [[0.915, 1.085]],
        "inits": [1.0]
      },
      { "name": "mu_bkg", "bounds": [[0.5, 2.0]] },
      { "name": "some_np", "fixed": true }
    ]
  }
}
```

Available overrides: `inits` (initial values), `bounds` (parameter limits),
`auxdata` (constraint central values), `sigmas` (constraint widths), `fixed`
(hold constant during fit).

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

bestfit, twice_nll = pyhf.infer.mle.fit(data, model, return_fitted_val=True)
print(f"Best-fit mu: {bestfit[model.config.poi_index]:.3f}")

obs_limit, exp_limits = pyhf.infer.intervals.upper_limits.upper_limit(
    data, model, scan=np.linspace(0, 10, 51), return_expected_set=True
)
print(f"Observed limit: μ < {obs_limit:.2f} @ 95% CL")
print(f"Expected: {exp_limits[2]:.2f} (+1σ: {exp_limits[3]:.2f}, −1σ: {exp_limits[1]:.2f})")
```

## Troubleshooting

| Symptom                                | Cause                                    | Fix                                                      |
| -------------------------------------- | ---------------------------------------- | -------------------------------------------------------- |
| `pyhf.exceptions.InvalidSpecification` | JSON doesn't match HistFactory schema    | Run `pyhf.Workspace(spec)` and read the validation error |
| Fit converges to boundary              | Parameter bounded away from true minimum | Widen bounds in `measurements.config.parameters`         |
| `nan` in likelihood                    | Empty bin or division by zero            | Add small regularisation or merge bins                   |
| Expected limit varies wildly           | Background yields too low                | Ensure > 10 events/bin for asymptotic approximation      |
| NP pulled strongly                     | Template inconsistent with data          | Inspect pre-fit data/MC in that region                   |
| `InvalidPatchSet` on apply             | Workspace digest mismatch                | Regenerate patches against the current workspace version |

## Gotchas

- `histosys` `hi_data`/`lo_data` are **absolute** event rates, not relative
  shifts from nominal.
- `normsys` `hi`/`lo` are **scale factors** (e.g. 1.1 / 0.9), not absolute
  rates.
- Modifiers sharing the same `name` share the same underlying parameter — this
  is how correlated systematics across samples work.
- `staterror` is per-channel: one parameter set per channel, aggregated across
  all samples that declare it in that channel.
- `shapesys` or `staterror` with zero nominal rate or zero uncertainty →
  parameter allocated but fixed to 1 (multiplicative identity).
- Channel and sample names must be unique; duplicates raise
  `InvalidSpecification` at construction time.
- JAX uses 32-bit floats by default; add
  `jax.config.update("jax_enable_x64", True)` before importing pyhf to avoid
  precision loss in fits.
- Set the backend **before** building the model; switching backends mid-fit is
  not supported.
- All ATLAS energy and momentum values are in **MeV**.

## Interop

- **atlas:cabinetry**: high-level wrapper that builds pyhf workspaces from
  config + histograms
- **atlas:pyhs3**: schema-compliant serialisation of pyhf workspaces
- **atlas:hist**: convert `Hist` objects to numpy arrays for workspace
  construction
- **atlas:trexfitter**: can export HistFactory XML → convert with
  `pyhf xml2json`
- **atlas:iminuit**: HEP-standard optimizer usable as pyhf backend via
  `pyhf.set_backend("numpy", "minuit")`

## Docs

https://pyhf.readthedocs.io/en/latest/
