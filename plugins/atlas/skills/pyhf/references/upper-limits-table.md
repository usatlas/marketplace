# ATLAS Model-Independent Upper Limits Table

This reference covers the standard workflow for producing ATLAS results tables
with model-independent upper limits, background estimates with uncertainties,
discovery p-values, and CLb values — as seen in ATLAS search papers (e.g. Table
20 of SUSY-2018-05).

## Columns of a Standard Results Table

| Column                                                 | Meaning                                                           |
| ------------------------------------------------------ | ----------------------------------------------------------------- |
| Total Bkg.                                             | Background-only fit yield ± propagated uncertainty                |
| Data                                                   | Observed event count                                              |
| ⟨Aεσ⟩\_obs^95 \[fb]                                   | Observed 95% CL upper limit on visible cross-section              |
| S\_obs^95                                              | Observed 95% CL upper limit on number of signal events            |
| S\_exp^95                                              | Expected 95% CL upper limit (with ±1σ band)                      |
| CLb                                                    | Compatibility of observed data with signal hypothesis at μ = μ_95 |
| p(s=0) (Z)                                             | Discovery p-value and corresponding Gaussian significance         |

## Setup

```python
import json
import numpy as np
import pyhf
import pyhf.contrib.utils
import scipy.stats

pyhf.set_backend("numpy", "minuit")
```

## Loading Published Likelihoods from HEPData

```python
pyhf.contrib.utils.download(
    "https://doi.org/10.17182/hepdata.116034.v1/r34", "workspace_dir"
)

ws = pyhf.Workspace(spec)  # load from extracted JSON
model = ws.model()
data = ws.data(model)
```

## Background-Only Fit with Uncertainties

The background estimate comes from fixing the POI to zero and fitting the
nuisance parameters. Use `return_uncertainties=True` and
`return_correlations=True` to get the full fit result.

```python
pars_uncrt, corr = pyhf.infer.mle.fixed_poi_fit(
    0.0, data, model,
    return_uncertainties=True,
    return_correlations=True,
)
pars, uncrt = pars_uncrt.T
```

### Expected Yields Per Region

```python
expected = model.expected_actualdata(pars)
for region, count in zip(model.config.channels, expected):
    print(f"{region}: {count:.2f}")
```

### Error Propagation

Uncertainties on expected yields are computed by linearly propagating parameter
uncertainties through the model using the correlation matrix. This matches
ROOT's `RooAbsReal::getPropagatedError()`.

The error formula is:

    error²(x) = F_a(x) · Corr(a,a') · F_a'ᵀ(x)

where F_a(x) = (f(x, a+da) - f(x, a-da)) / 2.

Batched computation (efficient — avoids Python loop over parameters):

```python
npars = len(model.config.parameters)
model_batch = ws.model(batch_size=npars)
pars_batch = np.tile(pars, (npars, 1))

up_yields = model_batch.expected_actualdata(pars_batch + np.diag(uncrt))
dn_yields = model_batch.expected_actualdata(pars_batch - np.diag(uncrt))
variations = (up_yields - dn_yields) / 2

error_sq = np.einsum("il,ik,kl->l", variations, corr, variations)
errors = np.sqrt(error_sq)
```

Extract per-region results:

```python
region_idx = model.config.channels.index("DRInt_cuts")
bkg = expected[region_idx]
bkg_unc = errors[region_idx]
print(f"Total Bkg: {bkg:.0f} ± {bkg_unc:.0f}")
```

## Upper Limits (S\_obs^95 and S\_exp^95)

Compute the 95% CL upper limit on the number of signal events using CLs:

```python
mu_tests = np.linspace(15, 25, 10)
obs_limit, exp_limits, (scan, results) = (
    pyhf.infer.intervals.upper_limits.upper_limit(
        data, model,
        scan=mu_tests,
        level=0.05,
        return_results=True,
        return_expected_set=True,
    )
)

print(f"S_obs^95: {obs_limit:.1f}")
print(
    f"S_exp^95: {exp_limits[2]:.1f}"
    f" [{exp_limits[1] - exp_limits[2]:.1f},"
    f" +{exp_limits[3] - exp_limits[2]:.1f}]"
)
```

### Visible Cross-Section

Divide the observed limit by integrated luminosity:

```python
lumi_ifb = 140.0
print(f"<Aεσ>_obs^95: {obs_limit / lumi_ifb:.2f} fb")
```

The visible cross-section limit assumes negligible signal contamination in
control regions. It is model-independent in that no specific signal acceptance
or efficiency is assumed — only the product Aεσ is constrained.

## Discovery p-value and Significance

Test the background-only hypothesis (μ=0) using q₀:

```python
p0 = pyhf.infer.hypotest(0.0, data, model, test_stat="q0")
Z = scipy.stats.norm.isf(float(p0))
print(f"p(s=0): {float(p0):.2f} (Z={Z:.1f})")
```

Convention: p-value is capped at 0.5 in published tables.

## CLb

CLb measures compatibility of the observed data with the signal hypothesis at
the 95% CL signal strength (μ = μ\_95\_obs). It uses `return_tail_probs=True`:

```python
_, (_, CLb) = pyhf.infer.hypotest(
    obs_limit, data, model, return_tail_probs=True
)
print(f"CLb: {float(CLb):.2f}")
```

A small CLb indicates a downward fluctuation in data relative to the
signal+background hypothesis — the CLs prescription prevents erroneous
exclusion in this case by dividing by CLb.

## Assembling the Table

```python
region_idx = model.config.channels.index("DRInt_cuts")
print(
    f"| {model.config.channels[region_idx]} "
    f"| {expected[region_idx]:.0f} ± {errors[region_idx]:.0f} "
    f"| {data[region_idx]:.0f} "
    f"| {obs_limit / lumi_ifb:.2f} "
    f"| {obs_limit:.1f} "
    f"| {exp_limits[2]:.1f}"
    f" +{exp_limits[3] - exp_limits[2]:.1f}"
    f" {exp_limits[1] - exp_limits[2]:.1f} "
    f"| {float(CLb):.2f} "
    f"| {float(p0):.2f} ({Z:.1f}) |"
)
```

## Docs

- Tutorial:
  https://pyhf.github.io/pyhf-tutorial/UpperLimitsTable.html
- CLs prescription: DOI
  [10.1088/0954-3899/28/10/313](https://doi.org/10.1088/0954-3899/28/10/313)
- ATLAS visible cross-section conventions: ATL-PHYS-PUB-2022-017
