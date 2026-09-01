---
name: panda
description: >-
  Use when submitting ATLAS grid jobs with prun or pathena, monitoring tasks
  with pbook or BigPanDA, troubleshooting failed grid jobs, choosing between
  prun and pathena for distributed analysis, or configuring container-based or
  GPU grid submissions.
---

# PanDA (Production and Distributed Analysis)

## Overview

PanDA is the ATLAS workload management system for running analysis jobs on the
grid. Users interact with PanDA through three command-line tools: `prun` (run
arbitrary executables), `pathena` (run Athena/AnalysisBase jobs), and `pbook`
(monitor and manage submitted tasks). All three require a valid VOMS proxy and
the `panda` lsetup package.

## When to Use

- Submitting analysis code to the ATLAS grid for large-scale processing
- Running custom executables, scripts, or compiled binaries on grid workers
- Running Athena job options or transformations over grid datasets
- Monitoring, retrying, or killing submitted tasks
- Choosing between prun (generic) and pathena (Athena-specific) for a workflow
- Running containers or GPU-enabled jobs on grid sites

## Key Concepts

| Concept            | Notes                                                             |
| ------------------ | ----------------------------------------------------------------- |
| `prun`             | Submit arbitrary executables (C++, Python, shell) to the grid     |
| `pathena`          | Submit Athena job options or transformations to the grid          |
| `pbook`            | Bookkeeping: list, monitor, retry, kill tasks                     |
| `--outDS`          | Output dataset name; must match `user.<account>.<tag>` naming     |
| `--inDS`           | Input dataset (Rucio name); PanDA splits into per-job file groups |
| `--containerImage` | Run inside a Docker or CVMFS container on the worker node         |
| `--noBuild`        | Skip build step; use pre-built code or a container image          |
| BigPanDA           | Web interface at https://bigpanda.cern.ch for monitoring tasks    |
| Build job          | Compiles user code on the grid before running analysis jobs       |
| VOMS proxy         | Required authentication; `voms-proxy-init --voms atlas`           |

## Canonical Patterns

### Setup

```bash
setupATLAS
lsetup panda
voms-proxy-init --voms atlas
```

### prun: submit a simple job

```bash
prun --exec "echo Hello > myout.txt" \
     --outDS user.$RUCIO_ACCOUNT.hello_test \
     --nJobs 3 \
     --outputs myout.txt
```

### prun: process input data

Use `%IN` as a placeholder for input file names injected by PanDA.

```bash
prun --exec "python analysis.py %IN" \
     --inDS data18_13TeV.DAOD_PHYS.some_dataset/ \
     --outDS user.$RUCIO_ACCOUNT.analysis_output \
     --outputs hist.root \
     --nFilesPerJob 5
```

### prun: compiled C++ with build step

`--bexec` runs once before analysis jobs to compile code on the grid.

```bash
prun --exec "myanalysis %IN" \
     --bexec "make" \
     --inDS valid1.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.cpp_test \
     --outputs output.root \
     --rootVer recommended
```

### prun: container-based job

```bash
prun --containerImage docker://atlas/analysisbase:25.2.20 \
     --exec "python analysis.py %IN" \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.container_test \
     --outputs hist.root \
     --noBuild
```

### prun: GPU job

Append `&nvidia` to `--architecture` to request GPU-enabled sites.

```bash
prun --containerImage docker://myimage:latest \
     --exec "python train.py" \
     --outDS user.$RUCIO_ACCOUNT.gpu_training \
     --nJobs 1 \
     --noBuild \
     --architecture '&nvidia'
```

### pathena: job options

```bash
asetup AnalysisBase,25.2.20,here
lsetup panda

pathena MyAnalysisAlg_jobOptions.py \
     --inDS data18_13TeV.DAOD_PHYSLITE.some_dataset/ \
     --outDS user.$RUCIO_ACCOUNT.myanalysis_output
```

### pathena: transformation

Use `--trf` for Athena transform commands. Placeholders: `%IN` (input files),
`%OUT.suffix` (output with suffix), `%MAXEVENTS`, `%SKIPEVENTS`.

```bash
pathena --trf "Reco_trf.py inputAODFile=%IN outputNTUP=%OUT.NTUP.root maxEvents=%MAXEVENTS" \
     --inDS data18_13TeV.AOD.some_dataset/ \
     --outDS user.$RUCIO_ACCOUNT.reco_output \
     --nEventsPerJob 10000
```

### pathena: ComponentAccumulator config

```bash
pathena --trf "athena.py --CA MyConfig.py --evtMax=%MAXEVENTS --filesInput=%IN" \
     --inDS mc23.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.ca_output \
     --nEventsPerJob 5000
```

### pathena: test with limited files

Always limit files first to validate the workflow before full-scale submission.

```bash
pathena jobO.py \
     --inDS data18.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.test_run \
     --nFiles 2
```

### pbook: monitor and manage tasks

```bash
# List recent tasks
pbook show

# Show details for a specific task
pbook show 12345678

# Long format (includes job-level details)
pbook showl

# Retry failed jobs in a task
pbook retry 12345678

# Kill a running task
pbook kill 12345678

# Finish a task (set remaining undone jobs as failed)
pbook finish 12345678
```

### prun: secondary input datasets

Use `--secondaryDSs` to provide additional input datasets accessible via `%IN2`,
`%IN3`, etc.

```bash
prun --exec "myanalysis %IN %IN2" \
     --inDS primary.dataset/ \
     --secondaryDSs "IN2:3:secondary.dataset/" \
     --outDS user.$RUCIO_ACCOUNT.multi_input \
     --outputs output.root
```

The format is `NAME:nFilesPerJob:datasetName`. `%IN2` resolves to the files from
the secondary dataset.

### prun: merge output

```bash
prun --exec "python analysis.py %IN" \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.merged_output \
     --outputs hist.root \
     --nFilesPerJob 10 \
     --mergeOutput
```

`%OUT` is available inside `--mergeScript` to reference the merged output
filename.

## Worked Example: Grid analysis with prun

Submit a Python analysis script that processes DAOD_PHYSLITE files, produces
histograms, and merges output.

```bash
# 1. Setup
setupATLAS
lsetup panda
voms-proxy-init --voms atlas

# 2. Test locally first (always validate before grid submission)
python analysis.py input_test.root

# 3. Submit to grid with limited files for validation
prun --exec "python analysis.py %IN" \
     --inDS mc23_13p6TeV.DAOD_PHYSLITE.ttbar/ \
     --outDS user.$RUCIO_ACCOUNT.ttbar_hists_v1 \
     --outputs hist.root \
     --nFilesPerJob 5 \
     --nFiles 10

# 4. Monitor the task
pbook show

# 5. After validation, submit full dataset
prun --exec "python analysis.py %IN" \
     --inDS mc23_13p6TeV.DAOD_PHYSLITE.ttbar/ \
     --outDS user.$RUCIO_ACCOUNT.ttbar_hists_v2 \
     --outputs hist.root \
     --nFilesPerJob 5 \
     --mergeOutput

# 6. Retry any failed jobs
pbook retry <taskID>
```

## Troubleshooting

| Error                         | Cause                              | Fix                                                                              |
| ----------------------------- | ---------------------------------- | -------------------------------------------------------------------------------- |
| `sh: line 1: XYZ Killed`      | Exceeded memory limit              | Reduce `--nFilesPerJob` or `--nGBPerJob`                                         |
| `lost heartbeat`              | No heartbeat for 6 hours           | Usually recovers on `pbook retry`; transient site issue                          |
| `Looping job killed`          | No output update for 2 hours       | Use `--maxWalltime <hours>` for long jobs; `--noLoopingCheck` disables the check |
| `upstream job failed`         | Build job (bexec) failed           | Check build log on BigPanDA; fix compilation errors                              |
| `over_cpu_consumption`        | Multi-threaded exceeding CPU share | Use `--nCore N` to request multi-core queue                                      |
| Missing output files          | Output stream not used             | Use `--supStream` to suppress unused output streams                              |
| `proxy expired` / auth errors | VOMS proxy expired                 | Re-run `voms-proxy-init --voms atlas`                                            |
| `dataset already exists`      | Reused `--outDS` name              | Change dataset name; append version suffix                                       |
| Submission hangs              | Network or PanDA server issue      | Check https://bigpanda.cern.ch; retry after a few minutes                        |

## Gotchas

- **VOMS proxy must be valid**: all three tools fail silently or cryptically
  without a valid proxy. Run `voms-proxy-info` to check expiration.
- **`--outDS` naming**: must follow `user.<account>.<tag>` format. Reusing an
  existing dataset name causes submission failure; append a version suffix or
  timestamp.
- **Build job failures propagate**: if `--bexec` (prun) or the implicit build
  step (pathena) fails, all downstream analysis jobs fail with "upstream job
  failed". Fix the build error and resubmit.
- **Memory limits on worker nodes**: grid sites typically allow 2–4 GB per core.
  Reduce `--nFilesPerJob` or `--nGBPerJob` to stay within limits.
- **`--noBuild` sandbox limit**: pathena's `--noBuild` mode has a 50 MB sandbox
  limit. For larger payloads, use the default build step or a container.
- **Container availability**: `--containerImage` pulls from Docker Hub or CVMFS.
  Ensure the image is publicly accessible or available on CVMFS at the target
  site.
- **Placeholder spelling**: `%IN`, `%OUT`, `%RNDM:base` are literal strings
  inside `--exec`; PanDA substitutes them at runtime. Misspelling causes silent
  failures.
- **Multi-core jobs**: use `--nCore N` with pathena to request multi-core
  queues; without it, multi-threaded code may be killed for over-consuming CPU.

## Interop

- **Rucio**: input and output datasets are managed by Rucio. Use `rucio ls` to
  discover dataset names before submission.
- **setupATLAS / lsetup**: `lsetup panda` provides prun, pathena, and pbook.
  Combine with `asetup` for Athena-based pathena workflows.
- **BigPanDA**: https://bigpanda.cern.ch — web monitoring for all PanDA tasks.
  Filter by username, task ID, or dataset name.
- **Athena / AnalysisBase**: pathena submits Athena job options or
  ComponentAccumulator configs. Use `asetup` to configure the release before
  submission.
- **ServiceX**: for column-level data extraction without grid jobs, consider
  ServiceX as a lighter alternative to running prun/pathena for simple
  selections.

## Docs

https://panda-wms.readthedocs.io/en/latest/

Contact: hn-atlas-dist-analysis-help@cern.ch

Monitor: https://bigpanda.cern.ch
