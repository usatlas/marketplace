# Advanced Fitting and Diagnostics

## Fit Configuration

The NLL function carries its own fit config. View the current settings with
`nll.Print()`. Settings can be passed as NLL options or changed after
construction.

### Fit Config Settings

| Setting               | NLL option                                     | Post-construction                                                | Description                                                                          |
| --------------------- | ---------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Tolerance             | `XRF.xRooFit.Tolerance(0.01)`                  | `nll.fitConfig().MinimizerOptions().SetTolerance(0.01)`          | Tolerance = 1000 × max EDM. Default 0.01 → max EDM of 1e-5. **Do not set above 10.** |
| Strategy              | `ROOT.RooFit.Strategy(-1)`                     | `nll.fitConfig().MinimizerOptions().SetStrategy(-1)`             | Starting Minuit strategy. -1 = use first in StrategySequence.                        |
| StrategySequence      | `XRF.xRooFit.StrategySequence("0s01s12s2s3m")` | `nll.fitConfigOptions().SetValue("StrategySequence", ...)`       | Retry sequence on failure. Numbers = strategy, s = rescan, m = minuit1.              |
| Hesse                 | `ROOT.RooFit.Hesse(True)`                      | `nll.fitConfig().SetParabErrors(True)`                           | Run Hesse after Migrad for accurate covariance.                                      |
| HesseStrategy         | n/a                                            | `nll.fitConfigOptions().SetValue("HesseStrategy", -1)`           | Starting Hesse strategy. -1 = first in HesseStrategySequence.                        |
| HesseStrategySequence | n/a                                            | `nll.fitConfigOptions().SetValue("HesseStrategySequence", "23")` | Retry sequence for Hesse algorithm.                                                  |

### Strategy Details

| Strategy | Method                               | Speed                 |
| -------- | ------------------------------------ | --------------------- |
| 0        | Iterative Hessian approximation      | Fastest               |
| 1        | Not advised as starting strategy     |                       |
| 2        | Hesse with forward finite-difference | Slower                |
| 3        | Hesse with central finite-difference | 4× cost of strategy 2 |

**General approach**: start with low strategy, increase tolerance until fits
converge, then increase strategy if the post-Hesse EDM exceeds the tolerance
threshold.

## Correlation Matrix

After fitting, always inspect the correlation matrix:

```python
fr.Draw("CORR COLZ TEXT")      # full correlation matrix
fr.Draw("CORR10 COLZ TEXT")    # top-10 off-diagonal correlations
```

Correlations above ~80% indicate potentially degenerate parameters where
different points in parameter space produce nearly identical model predictions.
The covariance matrix (and symmetric uncertainties) cannot be trusted when the
likelihood minimum is poorly defined due to degeneracy.

## Impact and Ranking

Impact measures how much a parameter of interest μ shifts when a nuisance
parameter ν is moved by its uncertainty and held constant:

Δ\_{ν±}μ = μ̂̂(ν=ν̂+Δ±ν) − μ̂

### Computing Impact

```python
# Exact impact (triggers conditional fits)
fr.impact("mu_sig", "alpha_JES", up=True)
fr.impact("mu_sig", "alpha_JES", up=True, prefit=True)

# Approximated from covariance matrix (no extra fits)
fr.impact("mu_sig", "alpha_JES", up=True, approx=True)
fr.impact("mu_sig", "alpha_JES", up=True, prefit=True, approx=True)
```

### Relationship to Correlation

Impact ranking is approximately the same as ranking correlation coefficients:

Δ\_{ν±}μ ≈ cov(μ,ν) / (±Δν) = corr(μ,ν) · (±Δμ)

## Conditional Uncertainties and Uncertainty Breakdowns

The conditional uncertainty on μ when holding ν constant at its post-fit value
is:

Δμ(ν=ν̂) ≈ √(cov(μ,μ) − cov(μ,ν)²/cov(ν,ν))

For multiple conditioned parameters, use the Schur complement of the covariance
matrix block decomposition.

### Computing Conditional Uncertainties

```python
cError = fr.conditionalError("mu_sig", "alpha_*,gamma_*",
                              up=True, approx=True)
```

Wildcards are supported in the parameter list.

### Stat/Syst/MC-stat Breakdown

```python
totErr = fr.floatParsFinal().find("mu_sig").getError()

# Statistical uncertainty (condition on all systematics)
statErr = fr.conditionalError("mu_sig", "alpha_*,gamma_*",
                               up=True, approx=True)
systErr = ROOT.TMath.Sqrt(totErr**2 - statErr**2)

# Further breakdown: model-syst vs mc-stat
statAndMCStatErr = fr.conditionalError("mu_sig", "alpha_*",
                                        up=True, approx=True)
modSystErr = ROOT.TMath.Sqrt(totErr**2 - statAndMCStatErr**2)
mcStatErr = ROOT.TMath.Sqrt(statAndMCStatErr**2 - statErr**2)
```

### Shifted Global Observables (Shifted GO) Method

A newer (2025) technique for systematic uncertainty breakdowns using quadrature
sum of covariance-approximated prefit impacts:

```python
systErr = ROOT.TMath.Sqrt(
    sum([
        pow(fr.impact("mu_sig", np.GetName(),
                       up=True, prefit=True, approx=True), 2)
        for np in w.np().reduced("alpha_*", "gamma_*")
    ])
)
```

## Conditional Fits

Perform conditional fits (holding parameters at specific values) using the fit
result:

```python
fr = nll.minimize()
cfr = fr.cfit("mu_sig=1.5")  # conditional fit with mu_sig fixed at 1.5
print(cfr.status(), cfr.covQual())
print(2 * (cfr.minNll() - fr.minNll()))  # 2×PLR value
```

## Profile Likelihood Scan (Manual)

Build a PLR scan manually using conditional fits:

```python
fr = nll.minimize()
g = ROOT.TGraph()
v = minVal
while v < maxVal:
    cfr = fr.cfit(f"mu_sig={v}")
    g.AddPoint(v, 2 * (cfr.minNll() - fr.minNll()))
    v += (maxVal - minVal) / (nPoints - 1)
g.Draw("ALP")
```

## Goodness of Fit (Extended)

xRooFit uses the **saturated model** to compute goodness-of-fit p-values. The
saturated model likelihood ratio test statistic is assumed χ²-distributed.

### Main-Term Only (Recommended for Observed Data)

```python
nll.mainTerm().getVal()     # current main-term NLL
nll.saturatedMainTerm()     # saturated main-term NLL
nll.mainTermNdof()          # nBins - nUnconstrained
nll.mainTermPgof()          # p-value
```

### Including Constraint Term (Valid for Toys Only)

The constraint term's global observable nominal values bias the p-value towards
larger values for observed data. Use this version only for toy datasets.

```python
nll.getVal()          # full NLL
nll.saturatedVal()    # saturated full NLL
nll.ndof()            # nBins + nGlobs - nFloats
nll.pgof()            # p-value
```
