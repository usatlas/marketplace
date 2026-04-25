---
name: setupatlas
description: >-
  Use when setting up the ATLAS software environment with setupATLAS or
  ATLASLocalRootBase, running asetup to configure an Athena or StatAnalysis
  release, using lsetup to set up ROOT, rucio, panda, scikit-hep, LCG views, or
  other ATLAS tools, using acm (AtlasACM) for cmake/git-based package management
  and compilation, managing ATLAS grid middleware (rucio, panda), or finding
  help contacts for ATLAS software support.
---

# setupATLAS

## Overview

`setupATLAS` is the entry point to the ATLAS Local Root Base (ATLR/ALRB), a
CVMFS-based framework that provides versioned ATLAS software releases and
individual tools. After running `setupATLAS`, the `asetup` and `lsetup` commands
become available.

## Getting the setupATLAS Command

On machines with CVMFS (lxplus, tier-3 sites):

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
# shorthand once configured in ~/.bashrc:
setupATLAS
```

On lxplus7/CentOS7 hosts that need EL9 containers:

```bash
setupATLAS -c el9
```

Documentation:
https://twiki.atlas-canada.ca/bin/view/AtlasCanada/ATLASLocalRootBase2

## lsetup — Setting Up Individual Tools

`lsetup` sets up one or more individual tools in the current shell. Tools can be
listed in sequence; use quotes for tools with version specifiers.

```bash
lsetup root              # latest ROOT
lsetup "root 6.32"       # specific ROOT version
lsetup rucio             # Rucio distributed data management client
lsetup panda             # PanDA client for grid job submission
lsetup pyami             # pyAMI ATLAS metadata interface
lsetup scikit            # scikit-hep Python ecosystem
lsetup "views LCG_104 x86_64-el9-gcc13-opt"   # full LCG release
lsetup xrootd            # XRootD data access protocol
lsetup xcache            # XRootD local proxy cache
lsetup lcgenv            # LCG environment tool
```

See all available versions with `lsetup <tool> -h` or `showVersions`.

| Tool       | Description                            | Docs / Contact                                                     |
| ---------- | -------------------------------------- | ------------------------------------------------------------------ |
| `asetup`   | Athena/StatAnalysis release setup      | https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/AtlasSetup |
| `root`     | ROOT data analysis framework           | https://root.cern                                                  |
| `rucio`    | Distributed data management client     | https://rucio-ui.cern.ch                                           |
| `panda`    | PanDA distributed analysis client      | https://panda-wms.readthedocs.io                                   |
| `pyami`    | ATLAS Metadata Interface Python client | https://atlas-ami.cern.ch                                          |
| `scikit`   | scikit-hep Python ecosystem            | https://scikit-hep.org                                             |
| `views`    | Full LCG software release              | `lsetup "views"` for list                                          |
| `xrootd`   | XRootD data access                     |                                                                    |
| `xcache`   | XRootD local proxy cache               | https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Xcache          |
| `lcgenv`   | LCG environment tool                   | https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Lcgenv          |
| `astyle`   | ATLAS ROOT style macros                | https://gitlab.cern.ch/atlas-publications-committee/atlasrootstyle |
| `eiclient` | Event Index client                     | https://twiki.cern.ch/twiki/bin/view/AtlasComputing/EventIndex     |

## asetup — ATLAS Software Releases

`asetup` configures a full ATLAS release (Athena, AnalysisBase, AnalysisTop,
StatAnalysis, etc.) in the current shell. Arguments can be separated by spaces
or commas.

```bash
# Stable releases
asetup StatAnalysis,0.7.3             # specific release
asetup AnalysisBase,24.2.2            # specific AnalysisBase release
asetup Athena,22.0.0                  # specific Athena stable release

# Latest releases
asetup StatAnalysis,0.7,latest        # latest nightly of branch
asetup --stable StatAnalysis,0.7,latest  # latest stable of branch
asetup Athena,main,latest             # latest Athena main nightly

# Nightly by date (rDD, rMM-DD, rYYYY-MM-DD)
asetup Athena,main,r07-07             # nightly from July 7

# Re-setup the last release saved in this directory
asetup                                # no args = restore last session

# Add a user script to be re-sourced on every restore
asetup source myPackage/setup.sh

# Undo an asetup (reset to original shell env)
asetup --reset

# Compiler/cmake only (no release)
asetup none,gcc14,cmakesetup          # e.g. for building StatAnalysis
```

Key environment variables set by `asetup`:

| Variable                   | Example value                            |
| -------------------------- | ---------------------------------------- |
| `AtlasProject`             | `Athena`, `AnalysisBase`, `StatAnalysis` |
| `AtlasVersion`             | `24.0.0`                                 |
| `AtlasBuildBranch`         | `main`, `24.0`, `0.7`                    |
| `AtlasReleaseType`         | `stable` or `nightly`                    |
| `BINARY_TAG` / `CMTCONFIG` | `x86_64-el9-gcc13-opt`                   |
| `TestArea`                 | current build directory path             |

User configuration can be stored in `~/.asetup` or `$PWD/.asetup` (INI format
with `[defaults]`, `[aliases]`, `[environment]`, `[epilog.sh]` sections). See
`references/asetup.md` for configuration file details.

Quick start: https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/AtlasSetup
Full reference:
https://twiki.cern.ch/twiki/bin/view/AtlasComputing/AtlasSetupReference

## acm — ATLAS Package Management

`acm` (AtlasACM) is the ATLAS cmake/git build tool. It wraps `asetup` and
manages source checkouts, compilation, and testing. Available automatically
after `setupATLAS`.

### Setup a release with a source area

```bash
mkdir source build && cd build
acmSetup --sourcearea=../source AnalysisBase,24.2,latest
# or from a GitLab repo:
acmSetup --sourcerepo=myuser/myrepo AthAnalysis,21.2.14
```

`acmSetup` calls `asetup`, creates `CMakeLists.txt` in the source area if
needed, configures the cmake project, and sources `setup.sh`.

### Subsequent setups (same release)

```bash
cd build && acmSetup   # re-sources the last setup
```

### Core acm workflow

```bash
# Add packages from athena (sparse clone first, then add)
acm sparse_clone_project athena          # sparse-checkout athena
acm add_pkg athena/Control/AthenaCommon  # include package in build

# Clone an entire private fork
acm clone_project will/MyAnalysis
acm add_pkg MyAnalysis/.*               # add all packages

# Compile
acm compile                             # build everything
acm compile_pkg MyPackage               # build single package

# Create a new skeleton analysis package
acm new_skeleton MyPackage              # creates algorithm + joboption
```

### Full acm command reference

| Command                           | Description                                       |
| --------------------------------- | ------------------------------------------------- |
| `acmSetup [opts] <release>`       | Set up release + source area                      |
| `acm compile`                     | Build project (cmake --build)                     |
| `acm compile_pkg <pkg>`           | Build a single package                            |
| `acm find_packages`               | Reconfigure cmake (wipes CMakeCache)              |
| `acm test <pkg>`                  | Run ctests for a package                          |
| `acm clean [-f]`                  | cmake clean; `-f` also reruns find_packages       |
| `acm clone_project <repo>`        | Clone a GitLab project into source area           |
| `acm sparse_clone_project athena` | Sparse-clone the athena project                   |
| `acm add_pkg <path>`              | Include package(s) in compilation                 |
| `acm exclude_pkg <path>`          | Exclude package(s) from compilation               |
| `acm add_pkg_clients <path>`      | Add all packages that depend on the given one     |
| `acm switch <branch/tag> <path>`  | Check out specific version of a package           |
| `acm new_pkg <name>`              | Create a new cmake package                        |
| `acm new_skeleton <name>`         | Create a skeleton analysis package with algorithm |
| `acmSetup --unset`                | Undo the current setup                            |

Contact: atlas-sw-acm-users@cern.ch

## rucio — Data Management

```bash
lsetup rucio
# Requires a valid VOMS proxy:
voms-proxy-init --voms atlas

rucio list-dids "user.myname:*"          # list your datasets
rucio download scope:dataset              # download a dataset
rucio upload --rse SITE_SCRATCHDISK scope:dataset file.root
rucio add-rule scope:dataset 1 SITE_SCRATCHDISK  # create replication rule
```

Contact: hn-atlas-dist-analysis-help@cern.ch WebUI: https://rucio-ui.cern.ch

## panda — Grid Job Submission

```bash
lsetup panda
pathena MyJobOptions.py --inDS scope:input_dataset --outDS user.me.output
prun --exec "my_command %IN" --inDS scope:input --outDS user.me.output
bigpanda  # monitoring at https://bigpanda.cern.ch
```

Contact: hn-atlas-dist-analysis-help@cern.ch Monitor: https://bigpanda.cern.ch
Docs: https://panda-wms.readthedocs.io

## pyami — Dataset Metadata

```bash
lsetup pyami
ami list datasets --project mc20_13TeV --type EVNT "*Ztautau*"
# Credentials stored in ~/.pyami/pyami.cfg
# Use --ignore-proxy to authenticate with username/password
```

Contact: atlas-bookkeeping@cern.ch

## Additional Commands

```bash
showVersions            # show installed software versions
queryC <name>           # find/query containers on CVMFS
installPip <pkg>        # install pip package into local area
installRpm <pkg>        # install RPM into local area
diagnostics             # diagnostic tools menu
advancedTools           # advanced tools menu
printMenu               # reprint the setupATLAS menu
helpMe                  # extended help with all tool documentation
```

## Gotchas

- **No `python` alias**: `asetup` breaks if a shell alias named `python` is
  defined. Remove it before calling `asetup`.
- **`lsetup` vs `asetup`**: Use `lsetup root` for standalone ROOT without a full
  release; use `asetup` when you need a compiled ATLAS release.
- **`views` for LCG releases**: Use `lsetup "views"` (no tool name) to list
  available LCG release names and platforms, then
  `lsetup "views LCG_104 x86_64-el9-gcc13-opt"` to configure one.
- **VOMS proxy required for rucio/panda**: Always run
  `voms-proxy-init --voms atlas` before grid operations.
- **EL9 containers on CentOS7**: Run `setupATLAS -c el9` to enter the EL9
  container on CentOS7 hosts for branches that require EL9.
- **Re-entering a release**: Inside a build directory configured with acm or
  asetup, re-sourcing with `asetup` or `acmSetup` (no arguments) re-applies the
  saved configuration.

## Support Contacts

| Domain                                        | Mailing list                        |
| --------------------------------------------- | ----------------------------------- |
| Distributed computing (rucio, panda, general) | hn-atlas-dist-analysis-help@cern.ch |
| Physics analysis tools (PAT)                  | hn-atlas-PATHelp@cern.ch            |
| Offline software                              | hn-atlas-offlineSWHelp@cern.ch      |
| ACM package management                        | atlas-sw-acm-users@cern.ch          |
| Atlantis event display                        | hn-atlas-AtlantisDisplay@cern.ch    |
| AMI bookkeeping                               | atlas-bookkeeping@cern.ch           |

## Additional Resources

- **`references/asetup.md`** — Complete asetup option reference, configuration
  file format, environment variables, saved session workflow, and platform
  string syntax.

## Docs

https://twiki.atlas-canada.ca/bin/view/AtlasCanada/ATLASLocalRootBase2
