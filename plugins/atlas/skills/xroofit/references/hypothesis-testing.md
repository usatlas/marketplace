# Advanced Hypothesis Testing

## Hypothesis Spaces

A **hypothesis space** (hypoSpace) is defined by selecting which parameters
define the hypotheses to test. Assign parameters to axes of the hypoSpace (one
parameter per axis) or fix them to specific values.

Examples:

- Higgs search: mass parameter on x-axis, signal strength on y-axis
- SUSY search: two mass parameters on axes, signal strength fixed to 1

## Test Statistics

All test statistics are variants of the profile likelihood ratio:

t_μ = −2 ln(L(μ,ν̂̂,θ) / L(μ̂,ν̂,θ))

### Available Test Statistics

| Name       | Symbol | Use case     | Description                                                                |
| ---------- | ------ | ------------ | -------------------------------------------------------------------------- |
| `tmu`      | t_μ    | Two-sided    | Full PLR, no capping                                                       |
| `qmu`      | q_μ    | Upper limits | One-sided capped-above: 0 if μ̂ ≥ μ                                         |
| `qmutilde` | q̃_μ    | Upper limits | One-sided capped-above + lower-bounded: accounts for physical boundary μ_L |
| `q0`       | q₀     | Discovery    | One-sided capped-below: 0 if μ̂ ≤ 0                                         |
| `u0`       | u₀     | Discovery    | Uncapped: −t₀ if μ̂ ≤ 0, else t₀                                            |

`qmutilde` is the default for upper limits. `u0` has become popular for
discovery in recent years.

## HypoPoint Quantities

Each scanned point in the hypoSpace is a **hypoPoint** with computable
quantities:

| Method (results have `.value()` and `.error()`) | Description                                     |
| ----------------------------------------------- | ----------------------------------------------- |
| `pNull_asymp()`                                 | Observed p_null from asymptotic formulae        |
| `pNull_asymp(n)`                                | n-sigma expected p_null                         |
| `pAlt_asymp()`                                  | Observed p_alt from asymptotic formulae         |
| `pAlt_asymp(n)`                                 | n-sigma expected p_alt (= Φ(n) by construction) |
| `pCLs_asymp()`                                  | pNull/pAlt (observed)                           |
| `pCLs_asymp(n)`                                 | pNull(n)/pAlt(n) (n-sigma expected)             |
| `ts_asymp()`                                    | Observed test statistic value                   |
| `ts_asymp(n)`                                   | n-sigma Asimov test statistic value             |

Replace `_asymp` with `_toys` for toy-based values.

## HypoPoint Fits

| Method                 | Description                                                                      |
| ---------------------- | -------------------------------------------------------------------------------- |
| `ufit()`               | Unconditional fit to observed data (PLR denominator)                             |
| `cfit_null()`          | Conditional fit with POI at null hypothesis values (PLR numerator)               |
| `cfit_alt()`           | Conditional fit with POI at alt hypothesis values (needed for Asimov generation) |
| `cfit_lbound()`        | Conditional fit with POI at lower bound μ*L (needed for q̃*μ if μ̂ < μ_L)          |
| `asimov().ufit()`      | Unconditional fit to Asimov dataset (for asymptotic formulae)                    |
| `asimov().cfit_null()` | Null conditional fit to Asimov dataset                                           |

## Full Verbose Limit-Setting Example

```python
import ROOT
XRF = ROOT  # or: XRF = ROOT.Experimental.XRooFit

fileName  = "path/to/workspace.root"
pdfName   = "simPdf"
channels  = "*"         # comma-separated; exclude VRs
dsName    = "obsData"   # "" for Asimov
poiName   = ""          # "" to auto-infer
asimovVal = 0           # POI value for Asimov dataset
scanMin   = 0
scanMax   = 10
scanN     = 0           # 0 = auto-scan
scanType  = "cls visualize"
constPars = ""          # "*" for stat-only
tsType    = XRF.xRooFit.TestStatistic.qmutilde
nSigmas   = [0, 1, 2, -1, -2, float('nan')]  # NaN = observed

w = XRF.xRooNode(fileName)
if poiName == "":
    poiName = w.poi()[0].GetName()
if constPars != "":
    w.pars().reduced(constPars).setAttribAll("Constant")
w.pars()[poiName].setVal(asimovVal)

hs = w[pdfName].reduced(channels).nll(dsName).hypoSpace(
    poiName, tsType
)
hs.scan(scanType, scanN, scanMin, scanMax, nSigmas)
limits = hs.limits()

print(limits)
hasNaN = False
for nSigma, lim in dict(limits).items():
    if ROOT.TMath.IsNaN(lim.value()):
        hasNaN = True
if hasNaN:
    hs.Print()  # inspect status codes

# Save result to workspace
outFile = "result.root"
w.Add(hs.result())
w.SaveAs(outFile)
w.Browse()  # hypoSpace appears under "scans" folder
```

### Key Parameters

- **`channels`**: comma-separated channel list; use `reduced()` to exclude
  validation regions
- **`nSigmas`**: `float('nan')` requests the observed limit; integers request
  expected ±N sigma limits
- **`limits()`**: returns `std::map` keyed by `"-2"`, `"-1"`, `"0"`, `"1"`,
  `"2"` (expected) and `"obs"` (observed); each value has `.value()` and
  `.error()`

## Toy-Based Limits

Replace `scanType` to use toys instead of asymptotic formulae:

```python
scanType = "cls toys=1000.1"  # 1000 null + 100 alt toys per point
scanType = "cls toys=1000"    # 1000 null + 1000 alt toys per point
scanType = "cls toys"         # auto: 100-toy blocks until 2σ
                              # confidence on pCLs, max 10k
```

### Inspecting Toy Distributions

```python
hs.Print()    # list hypoPoints
hs[4].Draw()  # draw test statistic distribution for 5th point
```

For capped test statistics (all except `u0`), check for toys with ts < 0. These
indicate unconditional fits that did not converge on the true minimum — often
caused by setting tolerance too high.

## Limit-Setting Troubleshooting

### Common Failure Modes

1. **Scan range too large**: hypoPoints far from the data cause fits to fail
   (status=1, covariance forced positive-definite). Narrow the scan range.

2. **Problematic nuisance parameter**: use `constPars` to hold groups constant
   and isolate which NP causes failures. Use `w.pars().Print()` and
   `w.floats().Print()` to inspect.

3. **status=3 (EDM above threshold)**: increase Tolerance (up to ~10). If
   post-Hesse EDM warnings appear with strategy 0, increase to strategy 2.

4. **NaN limits**: print the hypoSpace (`hs.Print()`) to inspect which
   hypoPoints had non-zero status codes.

### Limit-Setting Checklist

Before running limits, answer these questions:

- What are the hypoSpace parameters and their values/axes?
- What hypoPoints are being tested?
- What p-value type: pNull (CLs+b) or pCLs (CLs)?
- How are p-values interpolated across the hypoSpace? (xRooFit uses log-linear
  along POI axis)
- What PLR test statistic variant?
- Toys or asymptotic formulae?
- What is the uncertainty on each p-value?
- Did any fits fail?

## Discovery Significance

Scan a single point at the background-only hypothesis:

```python
hs = nll.hypoSpace("mu_sig", XRF.xRooFit.TestStatistic.u0)
hs.scan("pnull", 1, 0, 0)  # single point at mu=0

print("Observed p0:", hs[0].pNull_asymp())
print("Expected p0:", hs[0].pNull_asymp(0))   # under mu=1
print("Expected +1σ:", hs[0].pNull_asymp(1))
print("Expected -1σ:", hs[0].pNull_asymp(-1))

# Convert to significance
sig = ROOT.Math.gaussian_quantile_c(hs[0].pNull_asymp().value(), 1)
```
