---
name: atlas-containers
description: >-
  Use when running ATLAS software inside containers via setupATLAS -c, choosing
  between Apptainer/Docker/Podman/Shifter, setting up containers on macOS or
  without CVMFS, mounting directories, passing GPU flags, submitting batch jobs
  from containers, using custom or standalone container images, joining Docker
  sessions, or debugging container-related issues like timezone, symlink, or
  SSH-agent problems.
---

# ATLAS Containers

## Overview

ATLAS containers provide a reproducible OS environment (CentOS 7, AlmaLinux 9,
etc.) for running ATLAS software, independent of the host operating system. The
`setupATLAS -c` command launches a container shell with CVMFS, home directory,
and working directory mounted automatically. Containers are the standard way to
run ATLAS software on macOS, on older Linux hosts that need a newer OS, or in
batch systems where the host OS does not match the release requirements.

## When to Use

- Running ATLAS software on macOS (Docker required)
- Running EL9 releases on a CentOS 7 host (or vice versa)
- Working on a machine without CVMFS (standalone setupATLAS download)
- Using custom container images from Docker Hub or GitLab registries
- Submitting batch jobs that need a containerized environment
- Passing GPU flags to the container runtime
- Debugging container mount, timezone, or SSH issues

## Key Concepts

**Container software support:**

| Platform | Apptainer  | Docker    | Podman     | Shifter    |
| -------- | ---------- | --------- | ---------- | ---------- |
| Linux    | Supported  | Supported | Supported  | Supported  |
| macOS    | No support | Supported | No support | No support |

On Linux, Apptainer (formerly Singularity) is the default. On macOS, Docker
Desktop is the only supported runtime.

**Container type auto-detection:**

When entering a container, setupATLAS inspects the image and classifies it:

| Type             | Trigger                   | Behavior                         |
| ---------------- | ------------------------- | -------------------------------- |
| atlas-default    | Standard ATLAS base image | Runs setupATLAS inside container |
| atlas-standalone | Has `/release_setup.sh`   | Skips auto setupATLAS            |
| non-atlas        | Non-ATLAS image           | Skips auto setupATLAS            |

**Mount points (automatic):**

| Host      | Container      | Notes                      |
| --------- | -------------- | -------------------------- |
| `$TMPDIR` | `/scratch`     | Temporary storage          |
| `$PWD`    | `/srv`         | Working directory at entry |
| `$HOME`   | `/home/<user>` | Home directory             |
| `/cvmfs`  | `/cvmfs`       | CVMFS software repository  |

**Login scripts:** Container shells source dedicated rc files instead of the
host login scripts:

- `$HOME/.bashrc.container` — bash
- `$HOME/.zshrc.container` — zsh
- `$HOME/.ssh.container` — SSH configuration

Create these files to customize the container shell environment without
affecting the host shell.

See `references/container-options.md` for the full option table and advanced
configuration environment variables.

## Canonical Patterns

### Enter a container shell

```bash
setupATLAS -c centos7        # CentOS 7 container
setupATLAS -c el9            # AlmaLinux 9 container
```

After entering, the standard setupATLAS menu appears and `asetup`/`lsetup` are
available inside the container.

### List available containers

```bash
setupATLAS -c --showVersions          # list all available containers
setupATLAS -c find=analysisbase,24.2,alma9  # search for specific image
queryC analysisbase                   # query containers on CVMFS
```

### Use a custom container image

```bash
# Docker Hub image
setupATLAS -c docker://atlas/analysisbase:21.2.85-centos7

# GitLab registry image
setupATLAS -c docker://gitlab-registry.cern.ch/atlas/athena/analysisbase:24.2.0
```

### Standalone container (atlas-standalone type)

For images that ship a pre-built release (detected by `/release_setup.sh`),
setupATLAS does not run automatically inside. Source the release manually:

```bash
setupATLAS -c docker://gitlab-registry.cern.ch/atlas/athena/analysisbase:24.2.0
# Inside the container:
source /release_setup.sh
source /alrb/postATLASReleaseSetup.sh
```

### Run without CVMFS (standalone setupATLAS)

Download the standalone bootstrap when CVMFS is unavailable:

```bash
curl -O https://atlas-tier3-sw.web.cern.ch/containers/setupATLAS
chmod +x ./setupATLAS
./setupATLAS -c el9
```

This downloads the container image and enters it. CVMFS is accessed from inside
the container via the automounter.

### GPU passthrough

```bash
# Apptainer/Singularity (Linux)
setupATLAS -c centos7 -e "--nv"

# Docker (Linux or macOS)
setupATLAS -c centos7 -e "--gpus all"
```

The `-e` flag passes runtime exec options directly to the container backend.

### Batch submission from containers

Enter the container with the `-b` flag to enable batch mode, then generate
submission scripts:

```bash
setupATLAS -c centos7 -b
batchScript "source /path/myJob.sh" -o submitMyJob.sh

# Submit to SLURM
sbatch --export=NONE submitMyJob.sh

# Submit to LSF
bsub -L /bin/bash submitMyJob.sh
```

The `-b` flag configures the container for non-interactive batch execution.

### Force a specific container runtime

```bash
# Force Docker on a Linux system that has both Apptainer and Docker
setupATLAS -c el9 --swtype docker

# Force Podman
setupATLAS -c el9 --swtype podman
```

Or set the environment variable before entering:

```bash
export ALRB_CONT_SWTYPE=docker
setupATLAS -c el9
```

### Join an existing Docker container

```bash
export ALRB_CONT_CONDUCT="dockerJoin"
setupATLAS -c <container>
```

This attaches to an already-running Docker container instead of starting a new
one. Warning: exiting the joined session kills that session only, but the
original container keeps running.

### Run a command and exit

```bash
# Execute a payload inside the container without an interactive shell
setupATLAS -c el9 -r "asetup StatAnalysis,0.7,latest && myScript.sh"
```

### Pre/post setup hooks

```bash
# Run commands before setupATLAS runs inside the container
setupATLAS -c el9 --presetup "export MY_VAR=foo"

# Run commands after setupATLAS completes inside the container
setupATLAS -c el9 --postsetup "source ~/mysetup.sh"
```

## Worked Example

**Scenario:** Run a StatAnalysis job on macOS where Apptainer is unavailable.

1. Install Docker Desktop for macOS and start it.

2. Download standalone setupATLAS (if CVMFS is not available):

   ```bash
   curl -O https://atlas-tier3-sw.web.cern.ch/containers/setupATLAS
   chmod +x ./setupATLAS
   ```

3. Enter an EL9 container:

   ```bash
   ./setupATLAS -c el9
   ```

4. Inside the container, set up the analysis release:

   ```bash
   setupATLAS
   asetup StatAnalysis,0.7,latest
   ```

5. Create a container-specific login script so future shells auto-configure. Add
   the standard setupATLAS initialization (see the setupatlas skill) to
   `$HOME/.bashrc.container` — container shells source this file instead of
   `~/.bashrc`.

6. Run the analysis:

   ```bash
   cd /srv    # maps to $PWD on the host
   python my_analysis.py
   ```

## Gotchas

- **macOS: Docker only.** Apptainer, Podman, and Shifter are unsupported on
  macOS. Install Docker Desktop.
- **macOS: case-insensitive filesystem.** The default macOS filesystem is
  case-insensitive (HFS+/APFS). File-name collisions can occur with ATLAS
  software that assumes case-sensitive paths. Consider a case-sensitive APFS
  volume for the working directory.
- **macOS: hostname restrictions.** The computer name must contain only
  `A-Za-z0-9` characters (no hyphens or special characters), or container
  startup may fail.
- **macOS: X11 forwarding.** Install XQuartz and enable "Allow connections from
  network clients" in XQuartz preferences for GUI applications.
- **macOS: SSH agent.** Docker on macOS cannot access the host SSH agent. Run
  `ssh-add` inside the container after entering.
- **Relative symlinks only.** Absolute symlinks break inside containers because
  host paths differ from container paths. Always use relative symlinks in the
  working directory.
- **Timezone issue with voms-proxy.** In unpacked Apptainer containers,
  `voms-proxy-init` can fail with timezone errors. Fix with
  `export TZ=<timezone>` (e.g. `export TZ=America/Chicago`) or use `arcproxy` as
  an alternative.
- **ATLAS units are MeV.** All ATLAS energy, momentum, and mass values are in
  MeV, not GeV. This applies to ROOT files, xAOD containers, and framework
  outputs accessed from within containers.
- **Exiting a joined Docker session.** When using `dockerJoin`, exiting kills
  only the joined session, not the original container. But be aware that
  processes started in the joined session terminate on exit.

## Troubleshooting

| Symptom                               | Cause                                   | Fix                                                                                |
| ------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------- |
| `setupATLAS -c` hangs on macOS        | Docker Desktop not running              | Start Docker Desktop, wait for engine ready                                        |
| `FATAL: container creation failed`    | Apptainer not installed or too old      | Install Apptainer >= 1.0 or use `--swtype docker`                                  |
| Files missing inside container        | Working dir not under `$HOME` or `$PWD` | Move files to `$HOME` or `$PWD`; add custom mounts with `-o "-v /host:/container"` |
| `voms-proxy-init` timezone error      | Unpacked container TZ mismatch          | `export TZ=America/Chicago` or use `arcproxy`                                      |
| X11 apps fail on macOS                | XQuartz not configured                  | Install XQuartz, enable network clients, restart                                   |
| SSH auth fails inside Docker on macOS | Host SSH agent inaccessible             | Run `ssh-add` inside the container                                                 |
| `Permission denied` on mounted files  | UID mapping mismatch (rootless Podman)  | Use Apptainer or Docker; or configure Podman UID mapping                           |
| Container exits immediately with `-r` | Payload script has errors               | Test the script interactively first, check exit codes                              |
| Hostname-related errors on macOS      | Special characters in computer name     | Change computer name to alphanumeric only in System Settings                       |
| Java/Atlantis crashes in Singularity  | Known unresolved issue                  | No fix available; use Docker instead                                               |

## Interop

- **setupATLAS**: The `setupATLAS -c` flag is the container entry point — see
  the setupatlas skill for `asetup`, `lsetup`, and `acm` usage after entering.
- **StatAnalysis**: Enter an EL9 container, then
  `asetup StatAnalysis,0.7,latest` — see the statanalysis skill.
- **Batch systems**: The `-b` flag integrates with SLURM (`sbatch`) and LSF
  (`bsub`) schedulers at ATLAS sites.
- **Rucio/PanDA**: Grid tools work inside containers after
  `voms-proxy-init --voms atlas` — see the setupatlas skill for grid patterns.

## Docs

https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Containers

### Reference Files

- **`references/container-options.md`** — Full container option table,
  environment variables, advanced runtime configuration, and conduct keywords.
