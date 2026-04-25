# pathena — Full Option Reference

pathena submits Athena job options or transformation commands to the ATLAS grid
via PanDA. It automatically packages the user's work area (including compiled
libraries from `asetup`) and creates a build job on the grid.

## Setup

```bash
setupATLAS
asetup AnalysisBase,25.2.20,here   # or any Athena release
lsetup panda
voms-proxy-init --voms atlas
```

## Basic Syntax

### Job options mode

```bash
pathena jobOptions.py --inDS inputDS --outDS outputDS [options]
```

### Transformation mode

```bash
pathena --trf "Transform_trf.py arg1=%IN arg2=%OUT.suffix" --inDS inputDS --outDS outputDS [options]
```

## Input/Output Options

| Option           | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| `--inDS`         | Input dataset (Rucio name); PanDA splits files across jobs       |
| `--outDS`        | Output dataset; must match `user.<account>.<tag>`                |
| `--destSE`       | Destination RSE for output storage                               |
| `--secondaryDSs` | Secondary input datasets; format: `NAME:nFiles:datasetName/`    |

## Job Sizing Options

| Option             | Description                                                    |
| ------------------ | -------------------------------------------------------------- |
| `--nEventsPerJob`  | Events per job                                                 |
| `--nFilesPerJob`   | Files per job                                                  |
| `--nFiles`         | Limit total input files (use for testing before full runs)     |
| `--nGBPerJob`      | GB per job (alternative to `--nFilesPerJob`)                   |
| `--split`          | Number of jobs when no input dataset is specified              |
| `--maxCpuCount`    | Maximum CPU time in seconds                                    |
| `--maxWalltime`    | Maximum wall clock time in seconds                             |

## Build Options

| Option           | Description                                                      |
| ---------------- | ---------------------------------------------------------------- |
| `--noBuild`      | Skip build step; 50 MB sandbox limit applies                     |
| `--noCompile`    | Include source but skip compilation                              |
| `--extFile`      | Additional files to include in the sandbox                       |
| `--excludeFile`  | Glob patterns to exclude from the sandbox                        |

## Site and Resource Options

| Option              | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| `--site`            | Target specific site                                           |
| `--excludedSite`    | Comma-separated sites to avoid                                 |
| `--cloud`           | Target cloud (e.g. `US`, `CERN`)                               |
| `--memory`          | Requested memory in MB                                         |
| `--nCore`           | Number of CPU cores; routes to multi-core queues               |
| `--maxDiskCount`    | Maximum disk usage in KB per job                               |

## Athena-Specific Options

| Option              | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| `--trf`             | Transformation command string (alternative to job options)      |
| `--CA`              | Enable ComponentAccumulator configuration mode                  |
| `--athenaTag`       | Override the Athena version tag                                 |
| `--useAthenaPackages` | Include Athena packages from the work area                   |

## Production Options

| Option              | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| `--official`        | Submit as group production (requires `--voms`)                 |
| `--voms`            | VOMS role for group production (e.g. `atlas:/atlas/phys-hdbs`) |

## Event Picking

| Option                   | Description                                             |
| ------------------------ | ------------------------------------------------------- |
| `--eventPickEvtList`     | Text file with run:event pairs to pick                  |
| `--eventPickDataType`    | Data type to pick from (e.g. `AOD`, `ESD`)              |
| `--eventPickStreamName`  | Stream name filter                                      |

## Placeholder Variables

Use inside `--trf` strings. PanDA substitutes at runtime.

| Placeholder      | Resolves to                                                    |
| ---------------- | -------------------------------------------------------------- |
| `%IN`            | Comma-separated input file names for this job                  |
| `%OUT.suffix`    | Output file with given suffix (e.g. `%OUT.NTUP.root`)         |
| `%MAXEVENTS`     | Maximum events to process in this job                          |
| `%SKIPEVENTS`    | Number of events to skip (for splitting)                       |
| `%RNDM:base`     | Random seed derived from `base + jobID`                       |
| `%CORE_NUMBER`   | Number of allocated cores (use with `--nCore`)                 |

## Examples

### Job options with input data

```bash
pathena MyAnalysis_jobOptions.py \
     --inDS data18_13TeV.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.analysis_v1
```

### Test with limited files

Always limit files when validating a new workflow.

```bash
pathena MyAnalysis_jobOptions.py \
     --inDS data18_13TeV.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.test_v1 \
     --nFiles 2
```

### Transformation with event splitting

```bash
pathena --trf "Reco_trf.py inputAODFile=%IN outputNTUP=%OUT.NTUP.root maxEvents=%MAXEVENTS" \
     --inDS data18_13TeV.AOD.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.reco_v1 \
     --nEventsPerJob 10000
```

### ComponentAccumulator configuration

```bash
pathena --trf "athena.py --CA MyConfig.py --evtMax=%MAXEVENTS --filesInput=%IN" \
     --inDS mc23.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.ca_output \
     --nEventsPerJob 5000
```

### Multi-core job

```bash
pathena MyAnalysis_jobOptions.py \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.multicore_v1 \
     --nCore 8 \
     --nEventsPerJob 50000
```

### Event picking

Select specific events by run and event number from a text file.

```bash
# events.txt format (one per line):
# 123456:789
# 123456:790

pathena MyAnalysis_jobOptions.py \
     --eventPickEvtList events.txt \
     --eventPickDataType AOD \
     --outDS user.$RUCIO_ACCOUNT.picked_events
```

### Group production

```bash
pathena MyAnalysis_jobOptions.py \
     --inDS mc23.dataset/ \
     --outDS group.phys-hdbs.production_v1 \
     --official \
     --voms atlas:/atlas/phys-hdbs
```

### noBuild mode (small payload)

Skip compilation when the payload fits in the 50 MB sandbox limit.

```bash
pathena MyScript.py \
     --inDS mc23.DAOD_PHYSLITE.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.nobuild_test \
     --noBuild
```

### Output to specific storage element

```bash
pathena MyAnalysis_jobOptions.py \
     --inDS mc23.dataset/ \
     --outDS user.$RUCIO_ACCOUNT.analysis_v1 \
     --destSE BNL-OSG2_LOCALGROUPDISK
```
