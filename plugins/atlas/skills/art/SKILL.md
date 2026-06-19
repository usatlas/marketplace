---
name: art
description: >-
  Use when running or writing ART (ATLAS Release Tester) validation tests for
  ATLAS nightly builds, using art.py to run, list, or compare tests, debugging
  ART test failures in nightly CI, or understanding ATLAS release validation
  infrastructure.
---

# ART (ATLAS Release Tester)

## Overview

ART is the testing framework for ATLAS software releases. It runs validation
tests on nightly builds to verify that reconstruction, simulation, derivation,
and analysis workflows produce correct results across software updates. Test
results are published to the ART dashboard and used by release coordinators to
catch regressions before releases are tagged.

## When to Use

- Running validation tests for a package during ATLAS release development
- Writing new ART tests for a package being added or modified
- Investigating nightly test failures shown on the ART dashboard
- Comparing test outputs across nightlies to identify regressions
- Understanding which tests cover a given ATLAS package

## Key Concepts

**Nightly validation**: ART tests run automatically on every nightly build of
ATLAS projects (Athena, AthSimulation, AthGeneration, etc.). Failures block
release tagging until resolved.

**Per-package tests**: Tests are organized by package. Each package maintains
its own test scripts in the `test/` directory under the package source tree.
Test scripts follow the naming convention `test_<name>_<type>.{sh,py}` where
`<type>` is `grid` or `build`.

**Test artifacts**: ART archives output files (histograms, log files, metadata)
from each test run for comparison across nightlies. These artifacts enable
regression detection and performance monitoring.

**Test types** (the two valid `art-type` values):

| Type  | Description                                      |
| ----- | ------------------------------------------------ |
| grid  | Tests that run on the grid (batch-style, no TTY) |
| build | Tests that run locally during the build/CI phase |

## Canonical Patterns

### Setting Up the Environment

```bash
setupATLAS
asetup Athena,main,latest
```

ART tools (`art.py`) are available within the ATLAS release environment after
`asetup`.

### Running Tests

```bash
# See all art.py subcommands and their arguments
art.py --help

# List tests found under a package's test/ directory
art.py list <script_directory>

# Run tests locally (build-type), writing artifacts to an output directory
art.py run <script_directory> <output_directory>

# Run all CTest-registered tests for a package (includes build-type ART tests)
acm test MyPackage
```

The exact positional arguments to each `art.py` subcommand are best confirmed
with `art.py --help` / `art.py <subcommand> --help` inside the release, as they
have varied across ART versions.

### Writing a Shell-Based Test

Place test scripts in the package's `test/` directory. Name them
`test_<name>_<type>.sh` where `<type>` is `grid` or `build`:

```bash
#!/bin/bash
# art-description: Build PHYS and PHYSLITE derivations from ttbar AOD
# art-type: grid
# art-include: main/Athena
# art-input: mc21_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep
# art-input-nfiles: 1
# art-output: *.pool.root

set -e

Derivation_tf.py --CA \
    --inputAODFile ${ArtInFile} \
    --outputDAODFile art.pool.root \
    --formats PHYS PHYSLITE \
    --maxEvents -1
echo "art-result: $? derivation"
```

`art-result: <code> <label>` lines are parsed to determine pass/fail for each
step. Note `--reductionConf` (the old derivation transform option) has been
replaced by `Derivation_tf.py --CA ... --formats <FMT> [<FMT> ...]`.

### Writing a Python-Based Test

```python
#!/usr/bin/env python
# art-description: Unit test for MyAlgorithm configuration
# art-type: build

import sys

def test_config():
    from AthenaConfiguration.ComponentAccumulator import ComponentAccumulator
    ca = ComponentAccumulator()
    # ... configure and validate ...
    return 0

sys.exit(test_config())
```

### ART Header Directives

Test scripts use special comment headers to declare metadata:

| Directive          | Purpose                                                              |
| ------------------ | -------------------------------------------------------------------- |
| `art-description`  | Human-readable test description                                      |
| `art-type`         | Test category: `grid` or `build`                                     |
| `art-include`      | Branch/project the test runs in (e.g. `main/Athena`, or `*` for all) |
| `art-input`        | Input dataset name (for grid tests)                                  |
| `art-output`       | Output files to archive as artifacts (globs allowed)                 |
| `art-input-nfiles` | Number of input files to process                                     |
| `art-cores`        | Number of CPU cores to request                                       |
| `art-memory`       | Memory limit in MB                                                   |
| `art-athena-mt`    | Number of AthenaMT threads                                           |

### Checking Results on the Dashboard

Navigate to the ART dashboard to view nightly results, compare across builds,
and download test artifacts. Filter by project, branch, package, or test name.

## Gotchas

- **Clean environment**: ART tests run in a clean environment with no prior
  state. Do not assume files or environment variables from previous steps exist.
- **Exit codes matter**: Return 0 for success, non-zero for failure. The
  `art-result` line in the log is parsed to determine pass/fail status.
- **Grid constraints**: Grid-type tests cannot use interactive input, local file
  paths outside the sandbox, or network resources not available on worker nodes.
- **Timeouts**: Long-running tests are killed after the configured timeout.
  Break large workflows into smaller tests. `art-memory` and `art-cores` request
  resources but do not extend the timeout.
- **Artifact comparison**: ART diffs archived outputs against a reference
  nightly. Small numerical differences are expected — set tolerances
  appropriately in the comparison step.
- **All ATLAS energy/momentum values are in MeV**.

## Interop

- **setupATLAS / asetup**: ART requires a configured ATLAS release — see the
  setupatlas skill for environment setup.
- **acm**: `acm test MyPackage` runs CTest-registered tests for a package, which
  may include ART tests — see the acm skill.
- **Athena transforms**: Grid-type ART tests typically invoke Athena transforms
  (`Reco_tf.py`, `Sim_tf.py`, `Derivation_tf.py`) as their workflow.

| Domain                      | Contact                        |
| --------------------------- | ------------------------------ |
| ART framework and dashboard | hn-atlas-offlineSWHelp@cern.ch |
| Release validation          | hn-atlas-offlineSWHelp@cern.ch |

## Docs

https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/ART
