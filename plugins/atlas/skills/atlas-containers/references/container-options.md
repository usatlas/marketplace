# Container Options Reference

- Containers documentation:
  https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Containers

## Command-line options

| Option             | Env var equivalent      | Description                                    |
| ------------------ | ----------------------- | ---------------------------------------------- |
| `-c <image>`       |                         | Enter container (e.g. `centos7`, `el9`)        |
| `-b`               |                         | Enable batch mode for job submission           |
| `-e`, `--execopt`  | `ALRB_CONT_CMDOPTS`    | Runtime exec options (e.g. `"--nv"` for GPU)   |
| `-o`, `--runopt`   | `ALRB_CONT_OPTS`       | Runtime options passed to container engine     |
| `-r`, `--runpayload`| `ALRB_CONT_RUNPAYLOAD` | Run commands inside container and exit         |
| `-s`, `--setupfile`| `ALRB_CONT_SETUPFILE`  | Source this file inside the container          |
| `--swtype`         | `ALRB_CONT_SWTYPE`     | Force container software: apptainer, docker, podman, shifter |
| `--conduct`        | `ALRB_CONT_CONDUCT`    | Behavior keywords (see below)                  |
| `--presetup`       | `ALRB_CONT_PRESETUP`   | Commands to run before setupATLAS in container |
| `--postsetup`      | `ALRB_CONT_POSTSETUP`  | Commands to run after setupATLAS in container  |
| `--showVersions`   |                         | List available container images                |

## Environment variables

Set these before running `setupATLAS -c` to control container behavior
without command-line flags.

| Variable                 | Description                                       |
| ------------------------ | ------------------------------------------------- |
| `ALRB_CONT_CMDOPTS`     | Extra exec options for the container runtime      |
| `ALRB_CONT_OPTS`        | Extra run options for the container runtime       |
| `ALRB_CONT_RUNPAYLOAD`  | Payload command string; container exits after run  |
| `ALRB_CONT_SETUPFILE`   | Path to script sourced inside container           |
| `ALRB_CONT_SWTYPE`      | Container backend: `apptainer`, `docker`, `podman`, `shifter` |
| `ALRB_CONT_CONDUCT`     | Comma-separated behavior keywords                 |
| `ALRB_CONT_PRESETUP`    | Commands run before setupATLAS in container       |
| `ALRB_CONT_POSTSETUP`   | Commands run after setupATLAS in container        |

## Conduct keywords

The `--conduct` option (or `ALRB_CONT_CONDUCT` env var) accepts
comma-separated keywords that modify container behavior:

| Keyword       | Effect                                                    |
| ------------- | --------------------------------------------------------- |
| `dockerJoin`  | Attach to an existing Docker container instead of starting a new one |

## Image name syntax

| Form                                        | Example                                                          |
| ------------------------------------------- | ---------------------------------------------------------------- |
| Short alias                                 | `centos7`, `el9`                                                 |
| Docker Hub reference                        | `docker://atlas/analysisbase:21.2.85-centos7`                    |
| GitLab registry reference                   | `docker://gitlab-registry.cern.ch/atlas/athena/analysisbase:24.2.0` |
| Search pattern                              | `find=analysisbase,24.2,alma9`                                   |

Short aliases resolve to CVMFS-hosted Apptainer images. Docker references
pull from the specified registry.

## Container type detection

setupATLAS auto-detects image type and adjusts behavior:

| Type             | Detection rule                    | setupATLAS inside? |
| ---------------- | --------------------------------- | ------------------ |
| atlas-default    | Standard ATLAS base image         | Yes                |
| atlas-standalone | `/release_setup.sh` exists        | No                 |
| non-atlas        | Not an ATLAS image                | No                 |

For atlas-standalone images, source the release manually:

```bash
source /release_setup.sh
source /alrb/postATLASReleaseSetup.sh
```

## Mount points

These directories are mounted automatically:

| Host       | Container      | Notes                            |
| ---------- | -------------- | -------------------------------- |
| `$TMPDIR`  | `/scratch`     | Temporary storage                |
| `$PWD`     | `/srv`         | Working directory at entry       |
| `$HOME`    | `/home/<user>` | Home directory                   |
| `/cvmfs`   | `/cvmfs`       | CVMFS software repository        |

Add custom mounts via the `-o` flag:

```bash
# Docker
setupATLAS -c el9 -o "-v /data/mydata:/data/mydata"

# Apptainer
setupATLAS -c el9 -o "-B /data/mydata:/data/mydata"
```

## Login scripts

Container shells source these files (if they exist) instead of the host
login scripts:

| Shell | File                      |
| ----- | ------------------------- |
| bash  | `$HOME/.bashrc.container` |
| zsh   | `$HOME/.zshrc.container`  |
| SSH   | `$HOME/.ssh.container`    |

## GPU passthrough examples

```bash
# Apptainer with NVIDIA GPU
setupATLAS -c centos7 -e "--nv"

# Docker with NVIDIA GPU
setupATLAS -c centos7 -e "--gpus all"

# Docker with specific GPUs
setupATLAS -c centos7 -e "--gpus '\"device=0,1\"'"
```

## Batch mode

Enter with `-b` to prepare for batch submission:

```bash
setupATLAS -c centos7 -b
batchScript "source /path/myJob.sh" -o submitMyJob.sh
```

Submit the generated script to the local scheduler:

| Scheduler | Command                                |
| --------- | -------------------------------------- |
| SLURM     | `sbatch --export=NONE submitMyJob.sh`  |
| LSF       | `bsub -L /bin/bash submitMyJob.sh`     |
| HTCondor  | `condor_submit submitMyJob.sub`        |

The `--export=NONE` flag for SLURM prevents host environment leakage into
the container job.
