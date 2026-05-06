# HistFitter Config API — Deep Reference

Read this reference when constructing or debugging a HistFitter config script.
It covers all classes in the HistFitter Python API with their key properties and
methods.

## Table of Contents

- [configMgr (singleton)](#configmgr-singleton)
- [fitConfig](#fitconfig)
- [Channel](#channel)
- [Sample](#sample)
- [Measurement](#measurement)
- [Object hierarchy](#object-hierarchy)
- [Weight and systematic propagation](#weight-and-systematic-propagation)
- [Input file management](#input-file-management)

## configMgr (singleton)

The global configuration manager. Import as:

```python
from configManager import configMgr
```

### Essential properties

| Property         | Type  | Description                                                |
| ---------------- | ----- | ---------------------------------------------------------- |
| `analysisName`   | str   | Name of the analysis (sets output directory)               |
| `inputLumi`      | float | Luminosity of input TTrees/histograms                      |
| `outputLumi`     | float | Target luminosity for scaled output                        |
| `nomName`        | str   | Suffix of nominal TTree name (e.g., `"_NoSys"`)            |
| `calculatorType` | int   | 0 = frequentist (toys), 2 = asymptotic (Asimov)            |
| `testStatType`   | int   | 3 = one-sided profile likelihood (LHC default)             |
| `nPoints`        | int   | Scan points for upper limit (default 20)                   |
| `nTOYs`          | int   | Number of toys; ≤0 means real data                         |
| `seed`           | int   | Random seed (0 = clock)                                    |
| `weights`        | tuple | Global weight branches applied to all samples              |
| `cutsDict`       | dict  | Maps region names to cut strings                           |
| `readFromTree`   | bool  | Set by `-t` flag; controls TTree→histogram step            |
| `histCacheFile`  | str   | Path to histogram cache ROOT file                          |
| `myFitType`      | enum  | Set by `-F` flag; `FitType.Background/Exclusion/Discovery` |
| `scanRange`      | tuple | Override UL scan range `(min, max)` if first fit fails     |
| `autoScan`       | bool  | Automatic scan range determination                         |
| `userArg`        | str   | Arbitrary string from `-u` CLI flag                        |

### Blinding

| Property                 | Default | Description                       |
| ------------------------ | ------- | --------------------------------- |
| `blindSR`                | False   | Replace SR data with bkg estimate |
| `blindCR`                | False   | Blind control regions             |
| `blindVR`                | False   | Blind validation regions          |
| `useSignalInBlindedData` | False   | Add signal MC to blinded data     |
| `keepSignalRegionType`   | False   | Prevent auto-switch SR→VR         |

### Pruning

| Property        | Default | Description                         |
| --------------- | ------- | ----------------------------------- |
| `prun`          | False   | Enable systematic pruning           |
| `prunThreshold` | 0.01    | Relative threshold for pruning      |
| `prunMethod`    | 2       | 1 = chi2 test, 2 = bin-by-bin check |

### Histogram recycling

| Property                 | Default | Description                               |
| ------------------------ | ------- | ----------------------------------------- |
| `useCacheToTreeFallback` | False   | Fall back to trees for missing histograms |
| `useHistBackupCacheFile` | False   | Use a backup cache file                   |
| `histBackupCacheFile`    | ""      | Path to backup histogram cache            |

### Key methods

```python
configMgr.setLumiUnits("fb-1")           # or "pb-1"
configMgr.addFitConfig("BkgOnly")        # returns fitConfig object
configMgr.addFitConfigClone(obj, "name") # clone an existing fitConfig
configMgr.addInput(filename, treename)   # propagates to all fitConfigs
configMgr.addInputs(filenames, treename) # bulk add
```

`addTopLevelXML()` is deprecated — use `addFitConfig()`.

## fitConfig

A single fit configuration (background-only, exclusion, or discovery). Created
via `configMgr.addFitConfig("Name")`.

### Key methods

```python
fc = configMgr.addFitConfig("Exclusion")

# Channels (regions)
cr = fc.addChannel("nJet", ["CR"], 4, 2, 6)
sr = fc.addChannel("met", ["SR"], 5, 400, 900)
vr = fc.addChannel("met", ["VR"], 5, 400, 900)

# Region assignment
fc.addSignalChannels([sr])
fc.addBkgConstrainChannels([cr])
fc.addValidationChannels([vr])

# Measurements
meas = fc.addMeasurement(name="NormalMeasurement", lumi=1.0, lumiErr=0.039)
meas.addPOI("mu_SIG")

# Samples
fc.addSamples([topSample, dataSample])   # list or single Sample
fc.getSample("Top")                       # retrieve by name

# Weights (propagated to channels and samples)
fc.setWeights(("w1", "w2"))
fc.addWeight("newWeight")
fc.removeWeight("oldWeight")

# Systematics (propagated to channels and samples)
fc.addSystematic(syst)

# Signal
fc.setSignalSample(sigSample)  # accepts Sample object or string name

# Input files
fc.addInput(filename, treename)
fc.addInputs(filenames, treename)

# Functions (preprocessor)
fc.addFunction("myFunc", "x[0]+x[1]", "mu_SIG,mu_Top")

# Cloning
newFc = fc.Clone("NewName")
```

### Deprecated methods

| Deprecated                    | Use instead                   |
| ----------------------------- | ----------------------------- |
| `setSignalChannels(ch)`       | `addSignalChannels(ch)`       |
| `setBkgConstrainChannels(ch)` | `addBkgConstrainChannels(ch)` |
| `setValidationChannels(ch)`   | `addValidationChannels(ch)`   |

### addChannel() details

```python
chan = fc.addChannel(variableName, regions, nBins, binLow, binHigh)
```

- For cut-and-count: `variableName="cuts"` — nBins is auto-set to
  `len(regions)`, binHigh adjusted to `nBins + binLow`
- The channel is automatically populated with all samples and systematics
  already added to the fitConfig
- Returns the Channel object for further configuration

## Channel

Represents a region (SR/CR/VR) with a specific binning.

### Constructor (via fitConfig.addChannel)

```python
chan = fc.addChannel(variableName, regions, nBins, binLow, binHigh)
```

### Key properties

| Property             | Type  | Description                                    |
| -------------------- | ----- | ---------------------------------------------- |
| `channelName`        | str   | `"<regions>_<variable>"` (auto-constructed)    |
| `variableName`       | str   | Observable to bin                              |
| `regions`            | list  | Region name(s) for this channel                |
| `nBins`              | int   | Number of bins                                 |
| `binLow` / `binHigh` | float | Bin range                                      |
| `useOverflowBin`     | bool  | Include overflow in last bin (default False)   |
| `useUnderflowBin`    | bool  | Include underflow in first bin (default False) |
| `blind`              | bool  | Per-channel blinding override                  |
| `hasStatConfig`      | bool  | Whether stat errors are configured             |
| `statErrorThreshold` | float | Threshold for Barlow-Beeston lite              |

### Key methods

```python
chan.addSample(sample)                   # add a Sample to this channel
chan.getSample("Top")                    # retrieve Sample by name
chan.hasSample("Top")                    # check if sample exists
chan.removeSample("Top")                 # remove a sample
chan.addData("hData_SR_obs_met")         # set data histogram name

# Discovery samples (cuts channels only)
chan.addDiscoverySamples(
    srList=["SR"],
    startValList=[1.],
    minValList=[0.],
    maxValList=[10000.],
    colorList=[kMagenta]
)

# Systematics (propagated to samples)
chan.addSystematic(syst)
chan.getSystematic("JES")

# Weights
chan.setWeights(("w1", "w2"))
chan.addWeight("newWeight")
chan.removeWeight("oldWeight")

# Input files
chan.addInput(filename, treename)
chan.addInputs(filenames, treename)

# Cosmetics
chan.title = "Signal Region"
chan.titleX = "E_{T}^{miss} [GeV]"
chan.titleY = "Events / bin"
chan.logY = True
chan.minY = 0.1
chan.maxY = 1e4
```

## Sample

Represents a physics process (MC sample or data).

### Constructor

```python
sam = Sample("Top", kGreen-9)    # name, color
```

### Key properties

| Property       | Type | Description                              |
| -------------- | ---- | ---------------------------------------- |
| `name`         | str  | Sample name                              |
| `color`        | int  | ROOT color for plotting                  |
| `isData`       | bool | True for data samples                    |
| `isQCD`        | bool | True for QCD (data-driven) samples       |
| `isDiscovery`  | bool | True for discovery dummy signal          |
| `normByTheory` | bool | Normalize by theory cross-section        |
| `statConfig`   | bool | Enable MC stat errors for this sample    |
| `normRegions`  | list | Regions for normalization `[(reg, var)]` |
| `normFactor`   | list | Normalization factors                    |
| `weights`      | list | Event weight branches                    |
| `cutsDict`     | dict | Per-region cuts for this sample          |
| `unit`         | str  | Units string (default "GeV")             |
| `noRenormSys`  | bool | True = skip renormalization of systs     |

### Key methods

```python
# Data / special flags
sam.setData()                            # mark as data
sam.setQCD(isQCD=True, qcdSyst="uncorr") # mark as QCD
sam.setDiscovery()                        # mark as discovery
sam.setNormByTheory()                     # normalize by theory xsec

# Normalization
sam.setNormFactor("mu_Top", 1., 0., 5.)  # clears existing, adds one
sam.addNormFactor("mu_Top2", 1., 0., 5.) # appends without clearing
sam.setNormRegions([("CR", "nJet")])      # regions for TF normalization

# MC stat errors
sam.setStatConfig(True)

# Weights
sam.setWeights(("w1", "w2"))              # override
sam.addWeight("newWeight")                # append
sam.removeWeight("oldWeight")             # remove
sam.addSampleSpecificWeight("sf_top")     # sample-only weight

# User-defined histograms (no TTrees needed)
sam.buildHisto([5.0, 3.2], "SR", "met", binLow=0.5, binWidth=1.)
sam.buildStatErrors([1.0, 0.8], "SR", "met")

# Systematics
sam.addSystematic(syst)
sam.getSystematic("JES")
sam.removeSystematic("JES")
sam.clearSystematics()
sam.replaceSystematic(old_syst, new_syst)
sam.getAllSystematicNames()

# Shape factors (bin-by-bin free parameters for data-driven estimates)
sam.addShapeFactor("SF_QCD")

# Input files
sam.addInput(filename, treename)
sam.addInputs(filenames, treename)

# Tree name control
sam.setPrefixTreeName("Top")              # prefix for TTree names
sam.setSuffixTreeName("_nominal")         # suffix for TTree names
sam.setOverrideTreename("custom_tree")    # full override

# Per-sample cuts
sam.setCutsDict({"CR": "topTag>0.8", "SR": "topTag>0.9"})

# Cloning
newSam = sam.Clone()
```

### setNormFactor vs addNormFactor

- `setNormFactor()` clears the existing list and adds one factor
- `addNormFactor()` appends to the existing list

Most analyses use `setNormFactor()` since each sample typically has one
normalization factor.

## Measurement

Defines the statistical model parameters (POI, constraints, fixed params).

### Constructor (via fitConfig.addMeasurement)

```python
meas = fc.addMeasurement(name="NormalMeasurement", lumi=1.0, lumiErr=0.039)
```

### Key properties

| Property     | Type  | Description                         |
| ------------ | ----- | ----------------------------------- |
| `name`       | str   | Measurement name                    |
| `lumi`       | float | Luminosity value                    |
| `lumiErr`    | float | Relative luminosity error           |
| `binLow`     | int   | Lower bin (default 0)               |
| `binHigh`    | int   | Upper bin (default 50)              |
| `exportOnly` | bool  | True = build workspace only, no fit |
| `poiList`    | list  | Parameters of interest              |

### Key methods

```python
meas.addPOI("mu_SIG")

# Fix a parameter to a constant value
meas.addParamSetting("Lumi", True, 1.0)      # const=True, val=1.0
meas.addParamSetting("alpha_JES", False)       # floating (default)

# Constraint terms
meas.addConstraintTerm("alpha_ISR", "Gaussian")
meas.addConstraintTerm("gamma_stat_SR_0", "Poisson")
meas.addConstraintTerm("mu_BKG", "LogNormal", 0.1)  # with relUnc
meas.addConstraintTerm("mu_BKG", "Uniform")
meas.addConstraintTerm("mu_BKG", "NoConstraint")
```

Constraint types: `"Gaussian"`, `"Poisson"`, `"LogNormal"`, `"Uniform"`,
`"NoConstraint"`.

## Object hierarchy

```
configMgr (singleton)
├── fitConfig ("BkgOnly", "Exclusion", "Discovery")
│   ├── Measurement
│   │   ├── POI list
│   │   ├── param settings
│   │   └── constraint terms
│   ├── Channel (region)
│   │   ├── Sample
│   │   │   ├── Systematic objects
│   │   │   ├── normFactor
│   │   │   └── shapeFactor
│   │   └── data histogram
│   ├── Sample (shared across channels)
│   └── Systematic (shared across channels/samples)
└── global settings (weights, cutsDict, lumi, etc.)
```

## Weight and systematic propagation

Weights and systematics propagate **downward** through the hierarchy:

1. `configMgr.weights` → fitConfig → Channel → Sample
2. `fitConfig.addSystematic(syst)` → all owned Channels → all owned Samples
3. `channel.addSystematic(syst)` → all owned Samples
4. `sample.addSystematic(syst)` → only that sample

When adding a sample to a channel or fitConfig, existing weights and systematics
are automatically copied to the new sample (unless it already has them).

**Data, QCD, and Discovery samples** are excluded from weight/systematic
propagation.

The propagation only happens at **add time**. If you add a systematic to a
fitConfig after samples have been added, it propagates to existing channels and
samples. But if you add a sample after a systematic, the sample picks up the
systematic from its parent channel/fitConfig.

## Input file management

Input files propagate similarly to weights:

```python
# Global level — propagates to all fitConfigs, channels, samples
configMgr.addInput("bkg.root", "nominal")
configMgr.addInputs(["bkg1.root", "bkg2.root"], "nominal")

# fitConfig level — propagates to owned channels and samples
fc.addInput("signal.root", "nominal")

# Channel level — propagates to owned samples
chan.addInput("data.root", "data")

# Sample level — only this sample
sam.addInput("special.root", "mytree")
sam.addInputs(["file1.root", "file2.root"], "mytree")
```

Each level stores `InputTree(filename, treename)` objects in a set, ensuring
uniqueness. The tree name defaults to the sample's `prefixTreeName` (which
defaults to the sample name) if not specified.
