# TRExFitter: Advanced Config Patterns & Troubleshooting

Read this reference when running Asimov/blind fits, parallelising the
histogram or ranking steps, correlating or decorrelating nuisance parameters,
writing a `NormFactor` `Expression`, tuning MC statistical uncertainties,
exporting a workspace to pyhf, or diagnosing a fit/limit failure.

## Asimov (Blind) Fit

```bash
# In Fit block: FitBlind: TRUE
trex-fitter f config.config "FitBlind=TRUE"
```

Or at the command line without editing the config:

```bash
trex-fitter f config.config "StatOnly=TRUE"   # stat-only cross-check
```

## Parallelising Steps

`h`/`n` (histogram step) and `r` (ranking) are embarrassingly parallel:

```bash
# Histogram step: split by region
trex-fitter h config.config "Regions=SR"
trex-fitter h config.config "Regions=CR_top"

# Ranking: split by NP index (0-based, nSteps total)
trex-fitter r config.config "LHscanStep=0:10"   # step 0 of 10
trex-fitter r config.config "LHscanStep=1:10"
```

## Correlate / Decorrelate NPs

```
% 100% correlation: share NuisanceParameter name
Systematic: "JES_1"
  NuisanceParameter: "JES"
  ...

Systematic: "JES_2"
  NuisanceParameter: "JES"
  ...

% Full decorrelation: unique NuisanceParameter per region
Systematic: "JES"
  NuisanceParameter: "JES_SR"
  Regions: SR

Systematic: "JES"
  NuisanceParameter: "JES_CR"
  Regions: CR_top
```

Or use the command-line option `DecorrSysts=JES` to split automatically.

## NormFactor Expression (W helicity example)

```
NormFactor: "norm_left"
  Expression: (1.-norm_long-norm_right):norm_long[0.687,0,1],norm_right[0.002,0,1]

NormFactor: "norm_long"
  Nominal: 0.687

NormFactor: "norm_right"
  Nominal: 0.002
```

`Expression` uses ROOT `TFormula` syntax: `<formula>:<param>[init,min,max],...`.

## MC Statistical Uncertainties

```
Job: "MyAnalysis"
  MCstatThreshold: 0.01       % add gamma only if rel. unc. > 1%
  MCstatConstraint: POISSON   % POISSON (default) or GAUSSIAN

Sample: "rare_bkg"
  SeparateGammas: TRUE        % per-sample gammas (ShapeSys, not OverallSys)
  UseMCstat: FALSE            % exclude this sample from shared gammas
```

Cap per-bin MC stat uncertainty at ~20%; larger values bias signal extraction.

## Exporting to pyhf

```bash
trex-fitter w config.config
pyhf xml2json --basedir output/MyAnalysis/RooStats \
    output/MyAnalysis/RooStats/MyAnalysis.xml > workspace.json
```

## Troubleshooting

| Symptom                                          | Likely cause                                     | Fix                                                                   |
| ------------------------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------- |
| MIGRAD does not converge                         | NaN/Inf in likelihood                            | `DebugLevel: 3`; inspect `Systematics/` plots for bad templates       |
| Hessian matrix not positive-definite             | Near-degenerate NPs or singular workspace        | Merge similar backgrounds; increase `SystPruningShape`                |
| Many NPs constrained (σ_post ≪ 1)                | Fit absorbing fluctuations via shape NPs         | Reduce bins; apply `Smoothing: 40`; check `Systematics/` folder       |
| Large NP pulls (\|pull\| > 2)                    | Template disagreement with data                  | Inspect `Systematics/` plots; introduce CR for that NP                |
| Limit result is `nan`                            | Fit failure in signal hypothesis                 | Run `f` step first; check `w` step warnings in log                    |
| Same results each run vary slightly              | `SetRandomInitialNPval` > 0 set in config        | Difference ≤ 0.01 on POI is acceptable; increase it only for testing  |
| `h` step very slow                               | No parallelisation                               | Split by `Regions=<list>` in parallel jobs                            |
| Empty-bin crash                                  | Zero-yield background bin                        | Merge backgrounds, rebin, or adjust selection; TRExFitter fills 1e-6  |
| Systematic one-sided (both up/dn same direction) | Generator stat fluctuations or genuine asymmetry | Use `Symmetrisation: ABSMEAN` or `MAXIMUM`; or `ONESIDEDPLUS/MINUS`   |
| `pyhf xml2json` fails                            | Expressions or multiple POIs not supported       | Manually edit JSON; expressions not in pyhf (tracked upstream issues) |
