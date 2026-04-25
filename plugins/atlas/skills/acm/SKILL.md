---
name: acm
description: >-
  Use when building ATLAS software with acm (AtlasACM): setting up a cmake build
  environment with acmSetup, compiling packages, cloning or sparse-cloning athena,
  adding or excluding packages from the build, creating skeleton analysis
  packages, running ctests, or troubleshooting cmake configuration issues.
---

# ACM (AtlasACM)

## Overview

ACM is the ATLAS cmake/git package management and compilation tool. It wraps
`asetup` and provides a command-line interface for managing source checkouts,
cmake builds, and testing on top of an ATLAS release. The two entry points are
`acmSetup` (configures a release with a source area) and `acm` (build, test,
and package management commands). ACM becomes available after running
`setupATLAS`.

## When to Use

- Setting up a cmake build environment for modifying or extending ATLAS packages
- Compiling a custom ATLAS analysis package against AnalysisBase, AthAnalysis,
  or Athena
- Sparse-cloning athena to patch or override individual packages
- Creating a new skeleton analysis package from scratch
- Running ctests for a specific package
- Managing multiple source packages in a single build

## Key Concepts

**Directory layout**: ACM expects a separation between source, build, and run
directories. The build directory is where `acmSetup` runs and where cmake
artifacts live. The source area holds cloned repositories and custom packages.

```text
project/
  source/     # cloned repos, custom packages
  build/      # acmSetup runs here, cmake output
  run/        # athena job execution
```

**acmSetup vs acm**: `acmSetup` initializes (or restores) the build
environment, linking a release to a source area. `acm` subcommands operate
within that environment to compile, test, and manage packages.

**Session persistence**: `acmSetup` saves its configuration. Running `acmSetup`
with no arguments inside a previously configured build directory re-applies the
saved environment.

**Environment variables**:

| Variable                   | Purpose                                                |
| -------------------------- | ------------------------------------------------------ |
| `SourceArea`               | Path to source code directory                          |
| `TestArea`                 | Path to build directory                                |
| `ACM_GITLAB_PATH_PREFIX`   | Git path prefix (default: `https://:@gitlab.cern.ch:8443/`) |

## Canonical Patterns

### Initial setup with a local source area

```bash
mkdir source build run
cd build
acmSetup --sourcearea=../source AnalysisBase,24.2,latest
```

### Setup from a GitLab repository

```bash
mkdir build && cd build
acmSetup --sourcerepo=myuser/myrepo --sourcebranch=my-branch AthAnalysis,21.2.14
```

### Restore setup in a new shell

```bash
cd build
acmSetup        # no arguments = restore saved session
```

### Sparse-clone athena and add a package

```bash
acm sparse_clone_project athena
acm add_pkg athena/Control/AthAnalysisBaseComps
acm compile
```

For a private fork, provide the GitLab user prefix:

```bash
acm sparse_clone_project athena myuser/athena
```

### Clone a full GitLab project

```bash
acm clone_project myuser/MyAnalysis
acm add_pkg MyAnalysis/.*        # regex adds all packages in the repo
acm compile
```

### Create and build a skeleton analysis package

```bash
acm new_skeleton MyPackage
acm compile
cd ../run
athena MyPackage/MyPackageAlgJobOptions.py
```

### Build a single package

```bash
acm compile_pkg MyPackage
```

### Run tests for a package

```bash
acm test MyPackage
```

### Clean and reconfigure

```bash
acm clean        # cmake clean
acm clean -f     # cmake clean + rerun find_packages (wipes CMakeCache)
```

### Full workflow example

```bash
mkdir source build run
cd build
acmSetup --sourcearea=../source AthAnalysis,21.2,latest
acm sparse_clone_project athena
acm add_pkg athena/Control/AthAnalysisBaseComps
acm new_skeleton MyPackage
acm compile
cd ../run
athena MyPackage/MyPackageAlgJobOptions.py
```

## Command Reference

| Command                           | Purpose                                           |
| --------------------------------- | ------------------------------------------------- |
| `acmSetup [opts] <release>`       | Set up release + source area                      |
| `acmSetup`                        | Restore previously saved session                  |
| `acmSetup --unset`                | Undo the current setup                            |
| `acm compile`                     | Build all packages (cmake --build)                |
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

## Gotchas

- **Run acmSetup inside the build directory**: `acmSetup` must be invoked from
  the build directory, not the source or run directory.
- **sparse_clone_project is mainly tested with athena**: Other repositories may
  not work correctly with the sparse checkout mechanism.
- **Run `acm clean -f` after switching releases**: Changing the base release
  without cleaning can cause stale cmake caches and link errors.
- **Sourceless setup**: If `acmSetup` is run without a valid `--sourcearea` or
  `--sourcerepo`, it performs a "sourceless" setup where `acm` subcommands are
  not available — only the base release environment is configured.
- **Docker container sessions**: When exiting a joined Docker container, the
  entire session terminates — save work before detaching.
- **find_packages wipes CMakeCache**: `acm find_packages` (and `acm clean -f`)
  delete CMakeCache.txt and reconfigure from scratch. This is intentional but
  can be surprising if custom cmake variables were set manually.

## Interop

- **setupATLAS**: `setupATLAS` must be sourced before `acmSetup` is available.
  See the setupatlas skill for environment bootstrap.
- **asetup**: `acmSetup` wraps `asetup` internally — avoid mixing direct
  `asetup` calls with `acmSetup` in the same shell.
- **athena**: After compiling with `acm`, run jobs with the `athena` command
  from the run directory.

## Docs

https://gitlab.cern.ch/atlas-sit/acm
