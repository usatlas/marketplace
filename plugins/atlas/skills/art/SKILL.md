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

**Per-package tests**: Tests are organized by package. Each package maintains its
own test scripts in the `test/` directory under the package source tree.

**Test artifacts**: ART archives output files (histograms, log files, metadata)
from each test run for comparison across nightlies. These artifacts enable
regression detection and performance monitoring.

**Test types**:

| Type      | Description                                        |
| --------- | -------------------------------------------------- |
| Grid      | Tests that run on the grid (batch-style, no TTY)   |
| Build     | Tests that run during the build/CI phase           |
| Unit      | Fast unit tests for individual components          |

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
# List available tests for a package
art.py list MyPackage

# Run a specific test
art.py run MyPackage test_myworkflow.sh

# Run all tests for a package
acm test MyPackage

# Compare outputs across nightlies
art.py compare MyPackage test_myworkflow.sh
```

### Writing a Shell-Based Test

Place test scripts in the package's `test/` directory. Name them
`test_<testname>.sh`:

```bash
#!/bin/bash
# art-description: Validate reconstruction on ttbar sample
# art-type: grid
# art-input: mc21_13p6TeV.601229.PhPy8EG_A14_ttbar_hdamp258p75_SingleLep
# art-output: myOutput.pool.root

set -e

Reco_tf.py \
    --inputAODFile ${ArtInFile} \
    --outputDAODFile myOutput.pool.root \
    --reductionConf PHYS

# Validate output
art.py compare ref myOutput.pool.root
echo "art-result: $?"
```

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

| Directive           | Purpose                                    |
| ------------------- | ------------------------------------------ |
| `art-description`   | Human-readable test description            |
| `art-type`          | Test category: `grid`, `build`, or `unit`  |
| `art-input`         | Input dataset name (for grid tests)        |
| `art-output`        | Output files to archive as artifacts       |
| `art-input-nfiles`  | Number of input files to process           |
| `art-cores`         | Number of CPU cores to request             |
| `art-memory`        | Memory limit in MB                         |
| `art-athena-mt`     | Number of AthenaMT threads                 |

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
  Break large workflows into smaller tests or request additional time via
  `art-memory` and `art-cores`.
- **Artifact comparison**: Use `art.py compare` to diff outputs against a
  reference nightly. Small numerical differences are expected — set tolerances
  appropriately.
- **All ATLAS energy/momentum values are in MeV**.

## Interop

- **setupATLAS / asetup**: ART requires a configured ATLAS release — see the
  setupatlas skill for environment setup.
- **acm**: `acm test MyPackage` runs CTest-registered tests for a package,
  which may include ART tests — see the acm skill.
- **Athena transforms**: Grid-type ART tests typically invoke Athena transforms
  (`Reco_tf.py`, `Sim_tf.py`, `Derivation_tf.py`) as their workflow.

| Domain                        | Contact                          |
| ----------------------------- | -------------------------------- |
| ART framework and dashboard   | hn-atlas-offlineSWHelp@cern.ch   |
| Release validation            | hn-atlas-offlineSWHelp@cern.ch   |

## Docs

https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/ART
