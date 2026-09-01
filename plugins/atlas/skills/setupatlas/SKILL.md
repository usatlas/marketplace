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

`setupATLAS` is the entry point to the ATLAS Local Root Base (ALRB), a
CVMFS-based framework that provides versioned ATLAS software releases and
individual tools. After running `setupATLAS`, the `asetup` and `lsetup` commands
become available.

## When to Use

- Setting up any ATLAS software on a server with `/cvmfs/atlas.cern.ch` mounted
  (lxplus, ATLAS analysis facilities, tier-3 sites, SWAN)
- Getting standalone access to ROOT, rucio, panda, pyami, scikit-hep, or LCG
  views via `lsetup` — without loading a full ATLAS release
- Configuring a full ATLAS, Athena, AnalysisBase, or StatAnalysis software
  release for development or analysis via `asetup`
- Managing source packages, building with cmake, and running tests via `acm`
- Submitting grid jobs or accessing distributed ATLAS data via rucio and panda
- Finding the right mailing list for ATLAS software support

## Key Concepts

**ALRB (ATLASLocalRootBase)**: A CVMFS-based layered environment at
`/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase`. Sourcing `atlasLocalSetup.sh`
bootstraps the environment and exposes `asetup` and `lsetup`. The `setupATLAS`
alias is a shorthand for this step once configured in `~/.bashrc`.

**Tool categories:**

| Tool category         | Command                      | Purpose                                          |
| --------------------- | ---------------------------- | ------------------------------------------------ |
| Environment bootstrap | `setupATLAS`                 | Sources ALRB, exposes asetup/lsetup              |
| Individual tools      | `lsetup <tool>`              | Standalone ROOT, rucio, panda, LCG views, etc.   |
| Full releases         | `asetup <project>,<version>` | Athena, AnalysisBase, StatAnalysis, etc.         |
| Build system          | `acm` / `acmSetup`           | cmake/git package management on top of a release |
| Grid tools            | `rucio`, `panda`             | Distributed data and job management              |

**Session persistence**: `asetup` saves the active session to
`$PWD/.asetup.save`. Running `asetup` with no arguments re-applies it in a new
shell. Use `asetup --printLast` to inspect saved state.

**Platform strings**: `<arch>-<os>-<compiler>-<mode>`, e.g.
`x86_64-el9-gcc13-opt`. Controlled via `--platform`, `--os`, `--gccversion`,
`--opt`/`--dbg` flags to `asetup`.

See `references/asetup.md` for the full asetup option reference, configuration
file format, and environment variables.

## Canonical Patterns

### Getting setupATLAS

On servers with `/cvmfs/atlas.cern.ch` mounted (lxplus, tier-3):

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh
# shorthand once configured in ~/.bashrc:
setupATLAS
```

On lxplus7/CentOS7 hosts that need an EL9 container:

```bash
setupATLAS -c el9
```

### Setting Up Individual Tools with lsetup

`lsetup` configures one or more tools in the current shell without loading a
full ATLAS release. Use quotes for tools with version specifiers.

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

### Configuring an ATLAS Release with asetup

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
`references/asetup.md` for details.

Quick start: https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/AtlasSetup
Full reference:
https://twiki.cern.ch/twiki/bin/view/AtlasComputing/AtlasSetupReference

### Package Management with acm

`acm` (AtlasACM) is the ATLAS cmake/git build tool that wraps `asetup` and
manages source checkouts, compilation, and testing.

```bash
# Set up a release with a source area
mkdir source build && cd build
acmSetup --sourcearea=../source AnalysisBase,24.2,latest
# or from a GitLab repo:
acmSetup --sourcerepo=myuser/myrepo AthAnalysis,21.2.14

# Restore setup in subsequent shells
cd build && acmSetup

# Add and compile packages
acm sparse_clone_project athena          # sparse-checkout athena
acm add_pkg athena/Control/AthenaCommon  # include package in build
acm clone_project myuser/MyAnalysis      # clone entire private fork
acm add_pkg MyAnalysis/.*               # add all packages
acm compile                             # build everything
acm compile_pkg MyPackage               # build single package
acm new_skeleton MyPackage              # create skeleton analysis package
```

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

### Grid Data Access (rucio, panda)

```bash
lsetup rucio
voms-proxy-init --voms atlas   # required before all grid operations

rucio list-dids "user.myname:*"          # list your datasets
rucio download scope:dataset              # download a dataset
rucio upload --rse SITE_SCRATCHDISK scope:dataset file.root
rucio add-rule scope:dataset 1 SITE_SCRATCHDISK  # create replication rule
```

Contact: hn-atlas-dist-analysis-help@cern.ch WebUI: https://rucio-ui.cern.ch

```bash
lsetup panda
pathena MyJobOptions.py --inDS scope:input_dataset --outDS user.me.output
prun --exec "my_command %IN" --inDS scope:input --outDS user.me.output
# bigpanda monitoring at https://bigpanda.cern.ch
```

Contact: hn-atlas-dist-analysis-help@cern.ch Monitor: https://bigpanda.cern.ch |
Docs: https://panda-wms.readthedocs.io

### Dataset Metadata with pyami

```bash
lsetup pyami
ami list datasets --project mc20_13TeV --type EVNT "*Ztautau*"
# Credentials stored in ~/.pyami/pyami.cfg
# Use --ignore-proxy to authenticate with username/password
```

Contact: atlas-bookkeeping@cern.ch

### Utility Commands

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

## Interop

- **StatAnalysis**: `asetup StatAnalysis,0.7,latest` gives access to xRooFit,
  TRExFitter, cabinetry, quickFit, and the full ATLAS statistics toolkit — see
  the statanalysis skill.
- **xRooFit**: Available in all StatAnalysis releases via `import ROOT as XRF` —
  see the xroofit skill.
- **pyhf / cabinetry**: Available as Python packages within StatAnalysis — see
  the pyhf and cabinetry skills.
- **XRootD / fsspec-xrootd**: `lsetup xrootd` provides standalone XRootD access
  for reading remote files — see the fsspec-xrootd skill for Python integration.
- **ATLAS analysis facilities**: setupATLAS is pre-configured on CERN lxplus,
  ATLAS AF-US, AF-UK, and SWAN; tier-3 sites that mount `/cvmfs/atlas.cern.ch`
  work identically.
- **af-uchicago MCP**: If the af-uchicago plugin is also installed, its bundled
  AF MCP Platform server (`atlas-af`) can serve Rucio (`rucio-atlas_*` tools),
  AMI (`ami_*` tools), and HTCondor queries directly — no `lsetup`/local VOMS
  proxy needed. Check `/mcp` first; it only works for users who have linked
  their identity at `https://mcp-portal.af.uchicago.edu/identities/` (see the
  af-uchicago skill), otherwise fall back to the CLI patterns above.

| Domain                                        | Mailing list                        |
| --------------------------------------------- | ----------------------------------- |
| Distributed computing (rucio, panda, general) | hn-atlas-dist-analysis-help@cern.ch |
| Physics analysis tools (PAT)                  | hn-atlas-PATHelp@cern.ch            |
| Offline software                              | hn-atlas-offlineSWHelp@cern.ch      |
| ACM package management                        | atlas-sw-acm-users@cern.ch          |
| Atlantis event display                        | hn-atlas-AtlantisDisplay@cern.ch    |
| AMI bookkeeping                               | atlas-bookkeeping@cern.ch           |

## Docs

https://twiki.atlas-canada.ca/bin/view/AtlasCanada/ATLASLocalRootBase2

### Reference Files

- **`references/asetup.md`** — Complete asetup option reference, configuration
  file format, environment variables, saved session workflow, and platform
  string syntax.
