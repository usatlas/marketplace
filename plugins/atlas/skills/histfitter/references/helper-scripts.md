# HistFitter Helper Scripts — Deep Reference

Read this reference when producing publication-quality tables, pull/ranking
plots, or upper limit results from a HistFitter workspace.

All scripts are in `$HISTFITTER/scripts/` and operate on the after-fit workspace
ROOT file typically found at:

```text
results/<analysisName>/<FitConfig>_combined_<MeasName>_model_afterFit.root
```

## Table of Contents

- [YieldsTable.py](#yieldstablepy)
- [SysTable.py](#systablepy)
- [SystRankingPlot.py](#systrankingplotpy)
- [UpperLimitTable.py](#upperlimittablepy)
- [Other useful scripts](#other-useful-scripts)
- [Workspace file naming](#workspace-file-naming)

## YieldsTable.py

Produces a LaTeX table of before/after-fit yields per sample and region.

### Usage

```bash
YieldsTable.py -s <samples> -c <channels> -w <workspace.root> -o <output.tex>
```

### Required arguments

| Flag | Argument    | Description                           |
| ---- | ----------- | ------------------------------------- |
| `-w` | `<file>`    | After-fit workspace ROOT file         |
| `-c` | `<chans>`   | Comma-separated list of channel names |
| `-s` | `<samples>` | Comma-separated list of sample names  |
| `-o` | `<file>`    | Output LaTeX filename                 |

### Optional arguments

| Flag | Description                                      |
| ---- | ------------------------------------------------ |
| `-b` | Show before-fit yields alongside after-fit       |
| `-S` | Show sum of all regions as an additional column  |
| `-B` | Blind mode: hide observed event counts           |
| `-P` | Per-bin yields (split bins into separate rows)   |
| `-a` | Use asymmetric errors from MINOS (default: True) |

### Python API

```python
from YieldsTable import latexfitresults

latexfitresults(
    filename="results/.../afterFit.root",
    regionList=["CR_nJet", "SR_cuts"],
    sampleList=["Top", "WZ", "Zjets"],
    dataname="obsData",   # dataset name in workspace
    showSum=False,         # add sum column
    doAsym=True,           # asymmetric errors
    blinded=False,         # hide observed data
    splitBins=False        # per-bin breakdown
)
```

### Channel name format

Channel names in the workspace follow the pattern `<regions>_<variable>`. For
example, `addChannel("nJet", ["CR"], 4, 2, 6)` creates channel `CR_nJet`. For
cut-and-count with multiple regions, `addChannel("cuts", ["SR1", "SR2"], ...)`
creates `SR1SR2_cuts`.

### Output

- A `.tex` file with the yields table
- A `.pickle` file (same basename) containing the numerical data for pull plots

## SysTable.py

Produces a LaTeX table of systematic uncertainty breakdown per source.

### Usage

```bash
SysTable.py -c <channel> -w <workspace.root> -o <output.tex> [options]
```

### Required arguments

| Flag | Argument | Description                        |
| ---- | -------- | ---------------------------------- |
| `-w` | `<file>` | After-fit workspace ROOT file      |
| `-c` | `<chan>` | Channel to compute systematics for |
| `-o` | `<file>` | Output LaTeX filename              |

### Optional arguments

| Flag          | Description                                |
| ------------- | ------------------------------------------ |
| `-s <sample>` | Per-sample breakdown (default: total PDF)  |
| `-%`          | Show relative uncertainties as percentages |
| `-m 2`        | Use Method 2 (refit with parameter fixed)  |
| `-b`          | Use before-fit result instead of after-fit |

### Two methods

**Method 1 (default):** For each nuisance parameter, set all other NPs constant
at their best-fit values. Propagate the uncertainty from just that one
parameter. This is fast but can miss correlations.

**Method 2 (`-m 2`):** For each nuisance parameter, refit the model with that
parameter fixed at its best-fit value. The difference in the total uncertainty
before and after fixing gives the impact. This properly accounts for
correlations but is slower (one fit per NP).

### Python API

```python
from SysTable import latexfitresults

latexfitresults(
    filename="results/.../afterFit.root",
    namemap={},             # group systematics: {"JES": ["alpha_JES*"]}
    region="SR_cuts",       # region for breakdown
    sample="",              # empty = total PDF, or specific sample name
    resultName="RooExpandedFitResult_afterFit",
    dataname="obsData",
    doAsym=True
)
```

### Grouping systematics

The `namemap` parameter groups related NPs:

```python
namemap = {
    "Jet energy scale": ["alpha_JES_Flavor", "alpha_JES_Pileup",
                          "alpha_JES_EtaIntercal"],
    "B-tagging": ["alpha_BTag_B0", "alpha_BTag_B1", "alpha_BTag_C"],
}
```

When a namemap is provided, each group gets a single row showing the quadrature
sum of the individual uncertainties.

## SystRankingPlot.py

Produces a "pull + impact" plot showing the pre/post-fit effect of each nuisance
parameter on the POI.

### Usage

```bash
SystRankingPlot.py -w <workspace.root> -f <regions> -p <poi> [options]
```

### Required arguments

| Flag               | Argument | Description                     |
| ------------------ | -------- | ------------------------------- |
| `-w/--workspace`   | `<file>` | After-fit workspace ROOT file   |
| `-f/--fit-regions` | `<regs>` | Comma-separated fit regions     |
| `-p/--parameter`   | `<poi>`  | POI name (default: `mu_signal`) |

### Optional arguments

| Flag            | Default        | Description                          |
| --------------- | -------------- | ------------------------------------ |
| `--param-title` | `#mu_{signal}` | ROOT TLatex title for the POI        |
| `-o/--output`   | `plots/`       | Output directory                     |
| `-n/--name`     | `ranking`      | Output file base name                |
| `--max-np`      | 20             | Max number of NPs to show            |
| `--stat`        | off            | Show stat-only uncertainty band      |
| `-i/--input`    | —              | Read from saved `.data` file         |
| `--post-fit`    | off            | Only show post-fit impacts           |
| `--atlas`       | `Internal`     | ATLAS label text                     |
| `--sqrts`       | 13             | sqrt(s) in TeV                       |
| `--lumi`        | 36.5           | Luminosity in fb⁻¹                   |
| `--minGamma`    | None           | Truncate gamma NPs with small impact |

### How it works

For each nuisance parameter (alpha, gamma):

1. Load the after-fit snapshot
2. Fix the NP at its best-fit value +1σ, refit → get shift on POI = pre-fit +1σ
   impact
3. Fix at −1σ, refit → pre-fit −1σ impact
4. Fix at post-fit value ±1σ, refit → post-fit impacts
5. Sort NPs by post-fit impact magnitude
6. Plot the top `--max-np` parameters

### Multi-process version

`SystRankingPlotMP.py` runs the refits in parallel using Python multiprocessing.
Same arguments as `SystRankingPlot.py` but significantly faster for analyses
with many NPs.

## UpperLimitTable.py

Calculates upper limits on signal strength and visible cross-section from a
model-independent (discovery) fit.

### Usage

```bash
UpperLimitTable.py -c <channel> -w <workspace.root> -l <lumi_fb> [options]
```

### Required arguments

| Flag | Argument | Description                                  |
| ---- | -------- | -------------------------------------------- |
| `-w` | `<file>` | After-fit workspace ROOT file                |
| `-c` | `<chan>` | Channel name for the upper limit calculation |
| `-l` | `<lumi>` | Luminosity in fb⁻¹ (for xsec conversion)     |

### Optional arguments

| Flag             | Default    | Description                            |
| ---------------- | ---------- | -------------------------------------- |
| `-p <poi>`       | `mu_SIG`   | Name of the POI                        |
| `-n <nToys>`     | 3000       | Number of toys (ignored if asymptotic) |
| `-N <nPoints>`   | 20         | Number of scan points for mu           |
| `-R <muRange>`   | 40         | Maximum value of mu to scan            |
| `-a`             | off        | Use asymptotic (Asimov) calculation    |
| `--wname <name>` | `combined` | Workspace name inside the ROOT file    |
| `-o <prefix>`    | ""         | Output file prefix                     |
| `--autoScan`     | off        | Auto-determine scan range              |

### Python API

```python
from UpperLimitTable import latexfitresults

latexfitresults(
    filename="results/.../afterFit.root",
    poiname="mu_SIG",
    lumiFB=139.0,
    nTOYS=3000,
    nPoints=20,
    muRange=40,
    asimov=False,
    wname="combined",
    outputPrefix="",
    autoScan=False
)
```

### Output columns

The table contains:

- Observed upper limit on signal events
- Expected upper limit (±1σ, ±2σ bands)
- Observed upper limit on visible cross-section (= N_obs / lumi)
- CLb (observed background compatibility)
- p₀ (discovery p-value) with significance Z

### Troubleshooting

- **All zeros**: scan range too wide or too narrow — try `--autoScan` or adjust
  `-R` and `-N`
- **Negative CLs**: numerical instability; increase toys or switch to asymptotic
- **`Cannot find POI`**: check that the workspace contains a variable matching
  `-p`; for discovery fits the POI is typically `mu_Discovery` or
  `mu_DiscoveryMode_SR`

## Other useful scripts

### PrintFitResult.py

Dumps all fit parameters (values, errors, correlations) to stdout:

```bash
PrintFitResult.py -w <workspace.root>
```

Useful for quick checks of fit convergence and parameter values.

### contourPlotter.py

Converts harvest output (JSON from signal grid scans) to exclusion contour
plots:

```bash
contourPlotter.py -i harvest.json -o contour.pdf
```

### harvestToContours.py

Extracts observed/expected contours from a harvest JSON file:

```bash
harvestToContours.py -i <harvest.json> -o <output.root>
```

### pull_maker.py

Creates pull distributions from toy fits for coverage studies.

### plotUpDown.py

Plots up/down systematic variations against the nominal for visual inspection.

## Producing exclusion contours

Steps to produce contours:

1. Run exclusion tests over all signal models with `-p`
2. Merge output hypotest files with hadd
3. Generate json files with `GenerateJSONOutput.py`
4. Produce contours with `harvestToContours.py`
5. Plot contours following example in `macros/Examples/contourPlotterExample/contourPlotterExample.py`

### GenerateJSONOutput.py

Converts hypostest ROOT files to json.

`GenerateJSONOutput.py -i <input_hypotest.root> -f "hypo_SU_%f_%f_0_10" -p "m0:m12"`

### harvestToContours.py

Extracts observed/expected contours from a harvest JSON file:

`harvestToContours.py -i <harvest.json> -o <output.root>`



## Workspace file naming

After running `HistFitter.py -t -w -f -F <type> config.py`, results are in:

```
results/<analysisName>/
├── <FitConfig>_combined_<MeasName>_model.root         # workspace
├── <FitConfig>_combined_<MeasName>_model_afterFit.root # after-fit
└── <FitConfig>_combined_<MeasName>_model_beforeFit.root # (if requested)
```

For the typical convention:

- Background-only:
  `results/MySearch/BkgOnly_combined_NormalMeasurement_model_afterFit.root`
- Exclusion:
  `results/MySearch/Exclusion_combined_NormalMeasurement_model_afterFit.root`
- Discovery:
  `results/MySearch/Discovery_combined_NormalMeasurement_model_afterFit.root`

All helper scripts use the after-fit file. Use `_beforeFit` variant with the
`-b` flag in SysTable.py or by passing
`resultName="RooExpandedFitResult_beforeFit"`.
