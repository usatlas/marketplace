---
name: lcgenv
description: >-
  Use when setting up standalone LCG (CERN SFT) software packages via lcgenv or
  views: listing available LCG releases and platforms, configuring individual
  packages from a specific LCG release, setting up an entire LCG release at once
  with views, or combining LCG packages with other ATLAS tools like ROOT or
  rucio.
---

# lcgenv and views

## Overview

`lcgenv` and `views` are two mechanisms for setting up software from the LCG
(CERN SFT) stack distributed via CVMFS. `lcgenv` provides fine-grained control,
allowing individual packages and their dependencies to be configured from a
specific LCG release. `views` provides a coarse-grained alternative that sets up
an entire LCG release at once. Both are accessed via `lsetup` after running
`setupATLAS`.

## When to Use

- Setting up a specific Python, HEP, or math library from an LCG release without
  loading a full ATLAS release
- Listing available LCG releases, platforms, and packages
- Setting up multiple LCG packages with compatible versions from the same
  release
- Quickly activating an entire LCG release environment via views
- Combining LCG packages with standalone ATLAS tools (ROOT, rucio, etc.)

## Key Concepts

**LCG release**: A coordinated software stack (e.g., `LCG_104`) containing
versioned builds of ROOT, Python, Boost, and hundreds of other packages. Built
for specific platforms and distributed via `/cvmfs/sft.cern.ch`.

**Platform string**: `<arch>-<os>-<compiler>-<mode>`, e.g.,
`x86_64-el9-gcc13-opt`. Determines which binary build to use.

**lcgenv vs views**:

| Aspect      | lcgenv                         | views                 |
| ----------- | ------------------------------ | --------------------- |
| Granularity | Individual packages            | Entire LCG release    |
| Speed       | Slower (resolves dependencies) | Faster (single setup) |
| Flexibility | Pick only what you need        | All-or-nothing        |
| Use case    | Minimal environment, mixing    | Full LCG stack needed |

## Canonical Patterns

### List available LCG releases

```bash
lsetup "lcgenv"
```

### List platforms for a release

```bash
lsetup "lcgenv -p LCG_104"
```

### List packages available in a release

```bash
lsetup "lcgenv -p LCG_104 x86_64-el9-gcc13-opt"
```

### Set up a single package

```bash
lsetup "lcgenv -p LCG_104 x86_64-el9-gcc13-opt pyanalysis"
```

This configures the package and all its dependencies in the current shell.

### Set up multiple packages

Each package must be a separate quoted `lcgenv` invocation:

```bash
lsetup \
  "lcgenv -p LCG_104 x86_64-el9-gcc13-opt pygraphics" \
  "lcgenv -p LCG_104 x86_64-el9-gcc13-opt pyanalysis"
```

### Combine with other lsetup tools

```bash
lsetup \
  "lcgenv -p LCG_104 x86_64-el9-gcc13-opt pyanalysis" \
  "root 6.32" \
  rucio
```

### List available LCG views releases

```bash
lsetup "views"
```

### Set up a full LCG release with views

```bash
lsetup "views LCG_104 x86_64-el9-gcc13-opt"
```

This activates the entire software stack (ROOT, Python, Boost, etc.) from the
specified release in one command.

### Check which package version is in a release

```bash
lsetup "lcgenv -p LCG_104 x86_64-el9-gcc13-opt" | grep -i boost
```

The output lists all available packages with their versions; grep to find a
specific one.

### Common packages available via lcgenv

| Package      | Description                           |
| ------------ | ------------------------------------- |
| `pyanalysis` | Python analysis stack (numpy, etc.)   |
| `pygraphics` | Plotting libraries (matplotlib, etc.) |
| `Boost`      | Boost C++ libraries                   |
| `eigen`      | Eigen linear algebra library          |
| `hdf5`       | HDF5 data format library              |
| `fftw`       | Fast Fourier Transform library        |

## Gotchas

- **`-p` flag required for lcgenv**: The release must be specified with `-p`
  (e.g., `lcgenv -p LCG_104`), not as a positional argument.
- **Quoting is mandatory**: `lsetup` arguments with spaces must be quoted —
  `lsetup "lcgenv -p LCG_104 x86_64-el9-gcc13-opt pkg"`, not
  `lsetup lcgenv -p LCG_104 ...`.
- **views is all-or-nothing**: Unlike lcgenv, views does not support selecting
  individual packages — it loads everything from the release.
- **CVMFS access required**: Both tools read from `/cvmfs/sft.cern.ch`. Ensure
  CVMFS is mounted and accessible.
- **Platform must match the host**: Using a platform string that does not match
  the running OS (e.g., `slc6` on an EL9 host) produces broken environments.
  Check with `cat /etc/os-release` if unsure.
- **Do not mix lcgenv and views in the same shell**: Setting up a views release
  and then overlaying lcgenv packages from a different release can cause library
  conflicts.
- **Older release names**: Historical releases may use `slc6` or `centos7` in
  platform strings; current platforms use `el9`.

## Interop

- **setupATLAS**: `lsetup` must be available before using `lcgenv` or `views`.
  Run `setupATLAS` first. See the setupatlas skill.
- **ROOT**: `lsetup "root 6.32"` sets up ROOT independently. Use lcgenv only
  when a specific LCG-bundled ROOT version is needed.
- **asetup**: Full ATLAS releases already include LCG packages. Do not layer
  lcgenv on top of an asetup environment — use one or the other.
- **scikit-hep**: `lsetup scikit` provides the scikit-hep ecosystem
  independently of LCG. Use lcgenv when a specific LCG-coordinated version is
  required.

## Docs

- lcgenv: https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Lcgenv
- views: Self-documenting via `lsetup "views"` (lists releases and platforms)
- LCG releases: https://lcginfo.cern.ch
