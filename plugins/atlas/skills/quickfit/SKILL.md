---
name: quickfit
description: >-
  Use when fitting a RooWorkspace dataset with quickFit, generating an Asimov
  dataset with quickAsimov, computing asymptotic CLs limits with quickLimit,
  generating toy datasets with quickToy, rebinning datasets with quickRebin, or
  calculating nuisance parameter pulls with quickPull.
---

# quickFit

## Overview

quickFit is a suite of command-line tools for statistical operations on a
RooWorkspace. It provides rapid fitting, Asimov generation, CLs limit
computation, toy generation, dataset rebinning, and NP pull calculations. All
tools share a common interface and depend on ROOT and
[RooFitExtensions](https://gitlab.cern.ch/atlas_higgs_combination/software/RooFitExtensions).

quickFit is included in the StatAnalysis release (all executables available
after `asetup StatAnalysis,0.7,latest`). It can also be built standalone.

Repository: https://gitlab.cern.ch/atlas_higgs_combination/software/quickFit

## Standalone Installation

```bash
git clone ssh://git@gitlab.cern.ch:7999/atlas_higgs_combination/software/quickFit.git
cd quickFit
source setup_lxplus.sh   # sets up ROOT, cmake, boost from CVMFS
sh scripts/install_roofitext.sh   # install RooFitExtensions if not present
mkdir build && cd build
cmake ..
make && make install
cd ..
```

After the build, re-run `source setup_lxplus.sh` before using executables.

## quickFit — Fitting a Workspace

```bash
# Basic fit with floating POIs
quickFit -f ws.root -d dataset -p mu=1_-5_5

# Float mu_ggH, fix mu_VBF=2
quickFit -f ws.root -d dataset -p mu_ggH=1_-5_5,mu_VBF=2

# Fix all NPs matching ATLAS_* prefix
quickFit -f ws.root -d dataset -p mu=1_-5_5 -n "ATLAS_*"

# Run HESSE and MINOS on top of MIGRAD
quickFit -f ws.root -d dataset -p mu=1_-5_5 --hesse 1 --minos 1

# Save fit results to file
quickFit -f ws.root -d dataset -p mu=1_-5_5 -o output.root --savefitresult 1

# Parallel evaluation (multi-core or GPU)
quickFit --useModularL=true --numCPU=4 -f ws.root -d dataset -p mu=1_-5_5
quickFit --EvalBackend=cuda -f ws.root -d dataset -p mu=1_-5_5
```

### Parameter syntax (`-p`)

| Form | Meaning |
|---|---|
| `mu=1_-5_5` | Float `mu` with initial value 1, range [−5, 5] |
| `mu=2` | Fix `mu` at 2 |
| `mu_ggH=1_-5_5,mu_VBF=1_-5_5` | Multiple params, comma-separated |

### Key quickFit options

| Option | Description |
|---|---|
| `-f` | Input workspace ROOT file |
| `-w` | Workspace name (default: `combWS`) |
| `-m` | ModelConfig name (default: `ModelConfig`) |
| `-d` | Dataset name to fit |
| `-p` | POI/parameter configuration |
| `-n` | Fix NPs matching pattern |
| `-o` | Output ROOT file |
| `--savefitresult` | 0 = NLL only, 1 = full RooFitResult |
| `--hesse` | Run HESSE after MIGRAD (1=yes) |
| `--minos` | Run MINOS (1=yes) |
| `--useModularL` | Enable modular likelihood evaluation |
| `--numCPU` | Number of cores for parallel evaluation |
| `--EvalBackend` | Evaluation backend (`cpu`, `cuda`, etc.) |
| `--minTolerance` | Minimizer tolerance |

## quickAsimov — Generating Asimov Datasets

`quickAsimov` reads an XML card describing fit and Asimov generation actions.

```bash
quickAsimov -x card.xml -w combWS -m ModelConfig -d obsData
```

### XML card format

```xml
<!DOCTYPE Asimov SYSTEM 'asimovUtil.dtd'>
<Asimov InputFile="input.root" OutputFile="output.root" POI="mu">
  <Action Name="Prepare" Setup="" Action="nominalNuis:nominalGlobs"/>
  <Action Name="Fit" Setup="mu=1_0_5"
          Action="fit:matchglob:savesnapshot"
          SnapshotNuis="conditionalNuis_1"
          SnapshotGlob="conditionalGlob_1"/>
  <Action Name="asimovData_1" Setup="mu=1"
          Action="genasimov:nominalGlobs"/>
</Asimov>
```

### Action keywords (colon-separated in `Action` attribute)

| Keyword | Meaning |
|---|---|
| `fit` | Perform maximum likelihood fit |
| `genasimov` | Generate Asimov dataset (once per action list) |
| `savesnapshot` | Save parameter snapshot (once per action list) |
| `matchglob` | Match global observables to NP values (use with `reset`) |
| `reset` | Reset parameters to state before current action list |
| `raw` | Reset to state before any actions |
| `fixsyst` | Fix all constrained NPs |
| `float` | Float NPs fixed by `fixsyst` or `Setup` |
| `<snapshot name>` | Load a saved snapshot |

## quickLimit — Asymptotic CLs Limits

```bash
quickLimit -f ws.root -w combWS -m ModelConfig -d obsData -p mu -o limits.root
```

- Output: ROOT file with limit histograms + `.txt` file with numeric results.
- Only one POI is processed for limit setting; use the first listed with `-p`.
- Other POIs can still be configured via `-p` for fixing/floating.

## quickToy — Generating Toy Datasets

Requires snapshots already saved in the workspace (e.g. from `quickAsimov`).

```bash
quickToy -f ws.root -d toyData \
  -p mu=1,mu_ggH=1 \
  -s conditionalGlob_1,conditionalNuis_1 \
  -o output.root --seed 1
```

Use a different `--seed` for each independent toy.

## quickRebin — Rebinning a Dataset

Converts an unbinned dataset to a pseudo-binned one for faster fitting:

```bash
quickRebin -f output.root -d toyData -o output_binned.root -r 500
```

Creates `toyDatabinned` in the output file with 500 bins. Categories where
the number of entries is less than the bin count remain unbinned.

## quickPull — NP Pull to a POI

```bash
quickPull -f ws.root -w combWS -d combData \
  -p mu=1_0_5,mu_VBF=1 \
  --nui_param ATLAS_EG_RESOLUTION_ALL \
  --pull_POI mu \
  -o ATLAS_EG_RESOLUTION_ALL.root
```

## Gotchas

- **Custom classes**: If the workspace uses custom RooFit classes (from
  `RooFitExtensions` or local code), ensure `LD_LIBRARY_PATH` includes the
  library directory before opening the workspace, or the program will crash.
- **`matchglob` requires `reset`**: Always pair `matchglob` with `reset` at
  the end of the same action list to restore global observable values.
- **`genasimov` once per action list**: Including it more than once causes
  an error.
- **Workspace name defaults**: All tools default to `combWS`/`ModelConfig`;
  specify `-w` and `-m` explicitly if names differ.
- **ROOT ≥ 6.18 required**: Older ROOT versions are not supported.

## Interop

- **workspaceCombiner**: Produces combined workspaces that quickFit operates on.
- **xmlAnaWSBuilder / HistFactory**: Produces input workspaces; quickFit is the
  recommended fitting tool for these.
- **StatAnalysis**: All quickFit executables are available after
  `asetup StatAnalysis,0.7,latest`.
- **xRooFit**: Alternative Python/C++ API for fitting and limit setting built
  into ROOT within StatAnalysis.

## Support

Contact: quickFit-user@cern.ch

## Docs

https://gitlab.cern.ch/atlas_higgs_combination/software/quickFit
