---
name: statanalysis
description: >-
  Use when setting up the ATLAS StatAnalysis software release with asetup,
  choosing the right StatAnalysis branch for a given ROOT version or OS, running
  statistical analysis tools included in StatAnalysis (xRooFit, TRExFitter,
  HistFitter, cabinetry, quickFit, quickstats, workspaceCombiner,
  xmlAnaWSBuilder, RooUnfold, CMSCombine), using StatAnalysis Docker images,
  building StatAnalysis from source, or using the StatChallenges framework to
  compare toolkit implementations.
---

# StatAnalysis

## Overview

StatAnalysis is an ATLAS software release that bundles all commonly-used
statistical analysis tools into a single, versioned environment managed by the
ATLAS build system (AtlasCmake). It provides a consistent ROOT version, Python,
and compiled external packages, available on CVMFS and as Docker images.

Repository: https://gitlab.cern.ch/atlas/StatAnalysis

## Branches and Platform Support

| Branch | ROOT version | Platform      | Status          |
| ------ | ------------ | ------------- | --------------- |
| 0.7    | 6.38         | EL9 only      | **Recommended** |
| 0.6    | 6.36         | EL9 only      | Phasing out     |
| 0.5    | 6.34         | EL9 only      | Phasing out     |
| 0.4    | 6.32         | EL9 only      | Deprecated      |
| 0.3    | 6.30         | EL9 + CentOS7 | Deprecated      |
| 0.2    | 6.28         | CentOS7 only  | Deprecated      |

Use branch 0.7 for all new work. CentOS7 nodes require either `lxplus7.cern.ch`
or `setupATLAS -c el9` to use the EL9 container.

## Setup on Servers with /cvmfs

Works on CERN lxplus, ATLAS analysis facilities (AF-US, AF-UK, etc.), SWAN, and
any tier-3 site with `/cvmfs/atlas.cern.ch` mounted.

```bash
# Make asetup available (on lxplus just run: setupATLAS)
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh --quiet

# Latest nightly of a branch
asetup StatAnalysis,0.7,latest

# Latest stable of a branch
asetup --stable StatAnalysis,0.7,latest

# Specific release
asetup StatAnalysis,0.7.3
```

After setup, `$STATCHALLENGES` is automatically set to the CVMFS challenges
directory.

## Setup via Docker

```bash
# Interactive session
docker run --pull always -it gitlab-registry.cern.ch/atlas/statanalysis:0.7

# With X11 forwarding (macOS)
xhost +${hostname}
docker run --pull always -e DISPLAY=host.docker.internal:0 -it \
    gitlab-registry.cern.ch/atlas/statanalysis:0.7
```

Tags follow the branch name (e.g. `0.7`, `0.7.3`, `main`).

## Using StatAnalysis in SWAN (Jupyter)

Create a setup script containing:

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
asetup StatAnalysis,0.7,latest
```

Use that script as the SWAN session setup script at https://swan.cern.ch.

## Included Tools

| Tool               | Description                                        | Usage after asetup                               |
| ------------------ | -------------------------------------------------- | ------------------------------------------------ |
| ROOT + RooFit      | Data analysis framework with statistical modelling | `import ROOT`                                    |
| xRooFit            | High-level RooFit API (see xroofit skill)          | `import ROOT as XRF`                             |
| TRExFitter         | HistFactory profile-likelihood fitter              | `trex-fitter <actions> config.config`            |
| HistFitter         | Predecessor to TRExFitter, still supported         | `HistFitter.py -w -f config.py`                  |
| cabinetry          | Python HistFactory builder and visualizer          | `import cabinetry`                               |
| quickFit           | Rapid workspace fitting utility                    | `quickFit -w ws.root`                            |
| quickstats         | Python statistical analysis tools                  | `import quickstats`                              |
| RooUnfold          | Unfolding package                                  | `import ROOT; ROOT.gSystem.Load("libRooUnfold")` |
| workspaceCombiner  | Combine HistFactory workspaces                     | `workspaceCombiner ...`                          |
| xmlAnaWSBuilder    | Build workspaces from XML configurations           |                                                  |
| CMSCombine         | CMS Combine tool (for combination studies)         |                                                  |
| CommonStatTools    | Common ATLAS statistical utilities                 |                                                  |
| BootstrapGenerator | Bootstrap uncertainty estimation                   |                                                  |
| RooFitExtensions   | Additional RooFit classes                          |                                                  |
| PyAnalysis tools   | numpy, scipy, matplotlib, pandas, uproot, etc.     | `import numpy`                                   |

## StatChallenges Framework

StatChallenges is a test suite for comparing statistical toolkit
implementations. It lives at `$STATCHALLENGES` after setup.

```bash
# List available challenge suites
pytest $STATCHALLENGES --ls

# See the requirements for a suite
pytest $STATCHALLENGES/suites/test_hist.py --help

# Run your implementation against a suite
pytest $STATCHALLENGES/suites/test_hist.py --impls my_impl.py

# Compare multiple implementations
pytest $STATCHALLENGES/suites/test_hist.py \
    --impls my_impl.py,xRooFit.py

# Use central release, no clone needed
setupATLAS && asetup StatAnalysis,latest,main
# $STATCHALLENGES already set to CVMFS directory
```

An implementation file defines a function with the exact signature required by
the suite (shown in `--help`). The function returns a dictionary of computed
quantities. To write a new suite, contribute to the `Challenges/suites/`
directory of the StatAnalysis repository.

## Building from Source

```bash
# Requires modern cmake and gcc (e.g. cmake 4.0+, gcc 14.x on CVMFS)
asetup none,gcc14,cmakesetup   # on CVMFS
git clone --recurse-submodules https://gitlab.cern.ch/atlas/StatAnalysis.git
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=../install ../StatAnalysis
make -j install
source ../install/setup.sh
```

Build time is ~1 hour for a full build. Use the tier1 Docker image to reduce to
~10 minutes when only changing packages other than ROOT:

```bash
docker run --pull always -it gitlab-registry.cern.ch/atlas/statanalysis:0.7_tier1
```

Control which components are built:

```bash
cmake -LAH ./ | grep ATLAS_BUILD_   # list build options
cmake -LAH ./ | grep STATANA_       # list version options
cmake -DATLAS_BUILD_ROOT=OFF ...    # skip ROOT build (use system ROOT)
```

## Gotchas

- **No `python` alias allowed**: `asetup` fails if a shell alias named `python`
  is defined. Remove any such alias before running `asetup`.
- **CentOS7 compatibility**: Branches 0.4+ are EL9-only. Use `setupATLAS -c el9`
  on CentOS7 hosts to enter the EL9 container, or use `lxplus7.cern.ch` only for
  the 0.2 branch.
- **KRB5 authentication for source builds**: The default checkout method uses
  Kerberos. Run `kinit` first, or add
  `-DCERN_GITLAB_PREFIX="ssh://git@gitlab.cern.ch:7999"` for SSH access.
- **macOS builds require openssl@1.1**: Python's ssl module depends on it.
  Install with `brew install openssl@1.1` and copy the pkg-config files.
- **All energies in MeV**: Histograms from ATLAS reconstruction have axes in MeV
  (1 GeV = 1000 MeV). Convert explicitly if needed.

## Interop

- **xRooFit**: Pre-compiled in all StatAnalysis releases; use
  `import ROOT as XRF`.
- **TRExFitter**: Available as `trex-fitter`; see the trexfitter skill.
- **pyhf / cabinetry**: Both available as Python packages; see the pyhf and
  cabinetry skills.
- **uproot / awkward**: Available for Python-based I/O without ROOT.

## Docs

https://gitlab.cern.ch/atlas/StatAnalysis
