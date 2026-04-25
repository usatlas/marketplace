# Advanced Workspace Building

## Declaring Observables with SetXaxis

Instead of using a histogram to declare a channel's observable, use
`SetXaxis` directly:

```python
w["pdfs/simPdf/SR"].SetXaxis("obsName", "obs title", nBins, low, high)
w["pdfs/simPdf/SR/samples"].Add("bkg")
```

Both approaches create an initial `SimpleDensity` factor for the sample.

## Factor Types

Factors are the building blocks of samples. Two categories:
observable-dependent and observable-independent. Conventionally,
observable-independent factors become the **coefficients** of a sample
(`coefs()`), while observable-dependent factors remain inside the sample
itself.

### Basic Factor Types

| Type    | Obs-dependent | Parameterized | RooFit class          | Description                               |
| ------- | ------------- | ------------- | --------------------- | ----------------------------------------- |
| Const   | No            | No            | `RooConstVar`         | Pre-specified constant                    |
| Norm    | No            | Yes           | `RooRealVar`          | Floatable normalization parameter         |
| Simple  | Yes           | No            | `RooHistFunc`         | Histogram of bin yields                   |
| Density | Yes           | No            | `RooBinWidthFunction` | Special Simple factor where value = 1/binWidth |
| Shape   | Yes           | Yes           | `ParamHistFunc`       | Per-bin individual norm factors            |

### Varied Factor Types

Factors can be made parameter-dependent by defining **variations** at
points in a variation space with interpolation/extrapolation rules.

| Type    | Description                                         | RooFit class                          |
| ------- | --------------------------------------------------- | ------------------------------------- |
| Varied  | General parameterized factor with variations        | `PiecewiseInterpolation`              |
| Overall | Varied factor where variations are const factors    | `FlexibleInterpVar` or `PiecewiseInterpolation` |
| Histo   | Varied factor where variations are simple factors   | `PiecewiseInterpolation`              |
| Func    | Generic parametric function                         | `RooFormulaVar`                       |

### Creating and Multiplying Factors

```python
# Observable-dependent factor
w["pdfs/simPdf/SR/samples/bkg"].Multiply("myFactor", "shape")

# Observable-independent (coefficient)
w["pdfs/simPdf/SR/samples/bkg"].coefs().Multiply("mu_bkg", "norm")
```

If a factor with the same name already exists in the workspace, the type
argument is ignored and the existing factor is reused. This enables
factor sharing across samples and channels.

## Interpolation and Extrapolation Codes

Varied factors use an interpolation code to determine how the factor is
computed between and beyond the defined variation points.

For a varied factor with nominal variation f₀(x) and up/down variations
f_{i+}(x)/f_{i−}(x) for parameter θᵢ:

- **Additive** codes: f(x|θ) = f₀(x) + Σᵢ I(θᵢ; f_{i−}, f₀, f_{i+})
- **Multiplicative** codes: f(x|θ) = f₀(x) · Πᵢ I(θᵢ; f_{i−}/f₀, 1,
  f_{i+}/f₀)

| Code | Name                                        | Recommended for       |
| ---- | ------------------------------------------- | --------------------- |
| 0    | Additive piecewise linear                   | **Not recommended** (derivative discontinuities) |
| 1    | Multiplicative piecewise exponential        | **Not recommended**   |
| 4    | Additive poly interp + linear extrap        | **Histo factors**     |
| 5    | Multiplicative poly interp + exponential extrap | **Overall factors** (interpCode=4 in FlexibleInterpVar) |
| 6    | Multiplicative poly interp + linear extrap  | Norm factors that must not have roots outside \|θ\|<1 |

Codes 4 and 5 use a 6th-order polynomial in the \|θ\|<1 region, matched
to 0th/1st/2nd derivatives at the boundaries.

### Checking and Changing Interpolation Codes

```python
w["pdfs/simPdf/SR/samples/sampleName/sampleName"].printAllInterpCodes()
w["pdfs/simPdf/SR/samples/sampleName/sampleName"].setAllInterpCodes(4)
```

## Factor vs Sys

When any parameter of a parameter-dependent factor also has a
**constraint term**, the word "factor" is replaced by "sys":

- ShapeFactor → ShapeSys
- NormFactor with constraint → NormSys (effectively)

Promote a factor to a sys by adding a constraint:

```python
w["pdfs/simPdf"].pars()["npName"].Constrain("gaussian(0,1)")
w["pdfs/simPdf"].pars()["npName"].Constrain("normal")  # alias
```

### Log-normal Constraints

Replace the parameter with its exponentiated version, then apply a
normal constraint:

```python
w["pdfs/simPdf"].pars()["npName"].Replace(
    "expr::expo_npName('exp(npName)', npName)"
)
w["pdfs/simPdf"].pars()["npName"].Constrain("normal")
```

## MC Statistical Uncertainties

When a histogram with non-zero bin errors is added as a sample, xRooFit
automatically creates a **ShapeSys** with Poisson-constrained γ
parameters for MC statistical uncertainties. This ShapeSys is nominally
shared between all samples in the channel.

### Controlling MC Stat Behavior

- **Suppress**: zero out bin errors before adding the histogram
- **Control prefix**: `hBkg.SetOption("statPrefix=stat_SR_bkg")` (default
  prefix: `stat_<channelName>`)
- **Separate per sample**: any sample with its own NormFactor should have
  its own separate ShapeSys (or none) rather than sharing, because the
  normalization factor is not accounted for in the Poisson constraint
  calculation otherwise

### Variation Histograms

Variation histograms passed to `Vary()` **must have zero bin errors**.
Non-zero bin errors on variations create "errors-on-errors" which are
not fully supported.

## Creating Datasets

### From Histogram

```python
hData.SetName("obsData")
w["pdfs/simPdf/channelName"].datasets().Add(hData)
```

### Bin-by-Bin

```python
w["pdfs/simPdf/channelName"].SetBinData(binNumber, value, "obsData")
```

The dataset name defaults to `"obsData"` if unspecified.
