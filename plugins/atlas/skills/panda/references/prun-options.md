# prun — Full Option Reference

prun submits arbitrary executables to the ATLAS grid via PanDA. It packages the
current working directory as a sandbox, optionally runs a build step, then
distributes analysis jobs across grid sites.

## Setup

```bash
setupATLAS
lsetup panda
voms-proxy-init --voms atlas
```

## Basic Syntax

```bash
prun --exec "command" --outDS user.<account>.<tag> [options]
```

## Execution Options

| Option             | Description                                                         |
| ------------------ | ------------------------------------------------------------------- |
| `--exec "cmd"`     | Execution string; supports `%IN`, `%OUT`, `%RNDM:base` placeholders |
| `--bexec "cmd"`    | Build step command (runs once before analysis jobs, e.g. `make`)    |
| `--noBuild`        | Skip build step; use for containers or pre-built code               |
| `--containerImage` | Docker image (`docker://...`) or CVMFS image for the worker node    |
| `--architecture`   | CPU/GPU spec; append `&nvidia` for GPU (e.g. `'&nvidia'`)           |

## Input/Output Options

| Option           | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| `--inDS`         | Input dataset (Rucio name); PanDA splits across jobs             |
| `--outDS`        | Output dataset; must match `user.<account>.<tag>`                |
| `--outputs`      | Comma-separated output file names to collect from the worker     |
| `--secondaryDSs` | Secondary input datasets; format: `NAME:nFiles:datasetName/`     |
| `--mergeOutput`  | Merge output files after all jobs complete                       |
| `--mergeScript`  | Custom merge script; `%OUT` placeholder for merged file name     |
| `--destSE`       | Destination RSE for output (default: closest to submission site) |

## Job Sizing Options

| Option            | Description                                       |
| ----------------- | ------------------------------------------------- |
| `--nJobs`         | Number of jobs (when no `--inDS`)                 |
| `--nFilesPerJob`  | Files per job (with `--inDS`)                     |
| `--nGBPerJob`     | GB per job (alternative to `--nFilesPerJob`)      |
| `--nEventsPerJob` | Events per job                                    |
| `--nFiles`        | Limit total input files (use for testing)         |
| `--maxWalltime`   | Max walltime per job, in hours; use for long jobs |

## Site and Resource Options

| Option           | Description                             |
| ---------------- | --------------------------------------- |
| `--site`         | Target specific site (e.g. `CERN-PROD`) |
| `--excludedSite` | Comma-separated sites to avoid          |
| `--memory`       | Required memory in MB per core          |
| `--nCore`        | Number of CPU cores per job             |

## ROOT and Software Options

| Option                | Description                                       |
| --------------------- | ------------------------------------------------- |
| `--rootVer`           | ROOT version; use `recommended` for latest stable |
| `--cmtConfig`         | CMT configuration tag                             |
| `--useAthenaPackages` | Include Athena packages in the sandbox            |

## Sandbox Options

| Option          | Description                                        |
| --------------- | -------------------------------------------------- |
| `--extFile`     | Additional files to include in the sandbox         |
| `--excludeFile` | Glob patterns of files to exclude from the sandbox |
| `--noCompile`   | Do not compile even if `--bexec` is set            |

## Placeholder Variables

Use these inside `--exec` strings. PanDA substitutes them at runtime on the
worker node.

| Placeholder    | Resolves to                                                   |
| -------------- | ------------------------------------------------------------- |
| `%IN`          | Comma-separated list of input file names for this job         |
| `%IN2`, `%IN3` | Files from secondary datasets (see `--secondaryDSs`)          |
| `%OUT`         | Output file name in merge step (use with `--mergeScript`)     |
| `%RNDM:base`   | Random seed derived from `base + jobID`; reproducible per job |
| `%SKIPEVENTS`  | Number of events to skip (for event-level splitting)          |
| `%MAXEVENTS`   | Maximum events for this job                                   |

## Examples

### Hello world (no input)

```bash
prun --exec "echo Hello > myout.txt" \
     --outDS user.$RUCIO_ACCOUNT.hello_test \
     --nJobs 3 \
     --outputs myout.txt
```

### Python script with input data

```bash
prun --exec "python analysis.py %IN" \
     --inDS data18_13TeV.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.analysis_v1 \
     --outputs hist.root \
     --nFilesPerJob 5
```

### C++ with build step

```bash
prun --exec "myanalysis %IN" \
     --bexec "make" \
     --inDS valid1.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.cpp_analysis \
     --outputs output.root \
     --rootVer recommended
```

### Docker container

```bash
prun --containerImage docker://atlas/analysisbase:25.2.20 \
     --exec "python analysis.py %IN" \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.container_run \
     --outputs hist.root \
     --noBuild
```

### GPU job

```bash
prun --containerImage docker://myimage:gpu \
     --exec "python train.py" \
     --outDS user.$RUCIO_ACCOUNT.gpu_training \
     --nJobs 1 \
     --noBuild \
     --architecture '&nvidia'
```

### Secondary datasets

```bash
prun --exec "myanalysis %IN %IN2" \
     --inDS primary.dataset/ \
     --secondaryDSs "IN2:3:secondary.dataset/" \
     --outDS user.$RUCIO_ACCOUNT.multi_input \
     --outputs output.root
```

### Random seeds for MC generation

```bash
prun --exec "generate.py --seed %RNDM:12345" \
     --outDS user.$RUCIO_ACCOUNT.mc_gen \
     --nJobs 100 \
     --outputs events.root
```

### Merge output

```bash
prun --exec "python analysis.py %IN" \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.merged \
     --outputs hist.root \
     --nFilesPerJob 10 \
     --mergeOutput
```

### Site selection

```bash
prun --exec "python analysis.py %IN" \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.site_test \
     --outputs hist.root \
     --site CERN-PROD \
     --excludedSite BNL-OSG2
```
