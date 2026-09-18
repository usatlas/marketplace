# pyhf Advanced Workflows

Read this reference when asymptotic CLs results look unreliable and you need
toy-based hypothesis tests, when producing a Brazil-band or pull plot for a
note/paper, or when building a full multi-channel (signal + control region) fit
end-to-end.

## Table of Contents

- [Toy-Based Hypothesis Test](#toy-based-hypothesis-test)
- [Brazil Band Visualization](#brazil-band-visualization)
- [Pull Plot](#pull-plot)
- [Worked Example: ttbar search with one CR](#worked-example-ttbar-search-with-one-cr)

## Toy-Based Hypothesis Test

Use when asymptotics break down (e.g. low-statistics bins, boundary effects):

```python
CLs_obs, CLs_exp = pyhf.infer.hypotest(
    1.0, data, model, test_stat="qtilde",
    return_expected_set=True,
    calctype="toybased", ntoys=5_000, track_progress=True,
)
```

## Brazil Band Visualization

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

## Pull Plot

Requires the `minuit` optimizer backend for parameter uncertainties:

```python
pyhf.set_backend("numpy", "minuit")
result = pyhf.infer.mle.fit(data, model, return_uncertainties=True)
bestfit, errors = result.T

pulls = pyhf.tensorlib.concatenate([
    (bestfit[model.config.par_slice(k)] - model.config.param_set(k).suggested_init)
    / model.config.param_set(k).width()
    for k in model.config.par_order if model.config.param_set(k).constrained
])
```

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

## Docs

- https://pyhf.readthedocs.io/en/latest/
- https://pyhf.github.io/pyhf-tutorial/
