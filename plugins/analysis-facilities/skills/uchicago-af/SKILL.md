---
name: uchicago-af
description: >-
  Use when working with the UChicago ATLAS Analysis Facility, submitting
  HTCondor batch jobs at UChicago, accessing JupyterLab at af.uchicago.edu,
  using XCache or Rucio for ATLAS data at UChicago, deploying ML models on
  Triton at UChicago AF, setting up ServiceX or Coffea Casa, or troubleshooting
  SSH access to login.af.uchicago.edu
---

# UChicago ATLAS Analysis Facility Workflow

## Overview

The UChicago ATLAS Analysis Facility (UChicago AF) provides ATLAS physicists
with interactive nodes (SSH + JupyterLab), HTCondor batch computing, GPU
resources, and advanced data services (XCache, Rucio, ServiceX, Coffea Casa,
Triton). It is part of the MWT2 Tier-2 center supporting US ATLAS computing.

## When to Use

- Setting up access to login.af.uchicago.edu or af.uchicago.edu
- Submitting HTCondor batch jobs for ATLAS analysis
- Launching JupyterLab sessions with CPU/GPU resources
- Accessing ATLAS data via XCache or Rucio
- Using ServiceX for data delivery or Coffea Casa for columnar analysis
- Deploying ML models on Triton Inference Server
- Troubleshooting storage quota, proxy, or SSH issues at UChicago

## Quick Reference

| Resource          | Value                                                    |
| ----------------- | -------------------------------------------------------- |
| SSH Login         | `login.af.uchicago.edu`                                  |
| JupyterLab        | `https://af.uchicago.edu`                                |
| XCache            | `root://xcache.af.uchicago.edu:1094//`                   |
| ServiceX (Uproot) | `uproot-atlas.servicex.af.uchicago.edu`                  |
| ServiceX (xAOD)   | `xaod.servicex.af.uchicago.edu`                          |
| Coffea Casa       | `https://coffea.af.uchicago.edu`                         |
| Triton gRPC       | `triton-traefik.triton.svc.cluster.local:8001`           |
| Triton S3         | `s3://triton-models/<username>/` at `s3.af.uchicago.edu` |
| Support Email     | `atlas-us-chicago-tier3-admins@cern.ch`                  |
| Discourse         | `atlas-talk.sdcc.bnl.gov`                                |
| Home Directory    | `/home/<username>` (100GB quota, backed up weekly)       |
| Data Directory    | `/data/<username>` (5TB quota, not backed up)            |
| Scratch Directory | `/scratch` (worker-node local, ephemeral)                |
| LOCALGROUPDISK    | `MWT2_UC_LOCALGROUPDISK` (15TB via Rucio)                |

## Getting Started Workflow

1. **Request Account**: Sign up at `https://af.uchicago.edu/` using your
   institutional or CERN identity (CERN makes approval smoother); provide your
   full name, home institution, and institutional email. Personal email
   providers (Gmail, Outlook, iCloud) are not accepted. Not yet an ATLAS member?
   Contact `atlas-us-chicago-tier3-admins@cern.ch`
2. **SSH Key Setup**: Generate an ed25519 or ecdsa key (deprecated key types
   such as DSA or RSA with a SHA-1 signature are rejected):
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
   Sign up at `https://af.uchicago.edu/` and upload the public key to your
   Analysis Facility profile (the "SSH public key" box)
3. **First Login**: SSH to `login.af.uchicago.edu`:
   ```bash
   ssh <username>@login.af.uchicago.edu
   ```
   Initial login may take ~15 minutes for home directory sync
4. **Verify Access**: Check that `/home/<username>` and `/data/<username>`
   exist. `/scratch` is a shared, worker-node-local directory — there is no
   permanent `/scratch/<username>`; per-job scratch space is provided at
   runtime.

## ATLAS Environment Setup

All ATLAS software is available via CVMFS:

```bash
# Setup ATLAS environment
setupATLAS

# Setup specific tool (e.g., Rucio, ROOT, AnalysisBase)
lsetup rucio
lsetup root
lsetup "views LCG_105 x86_64-el9-gcc13-opt"

# Setup specific Athena/AnalysisBase release
asetup AnalysisBase,24.2.38
```

## Storage

| Path                         | Quota    | Backed Up | Purged                    | Best For                   |
| ---------------------------- | -------- | --------- | ------------------------- | -------------------------- |
| `$HOME` (`/home/<username>`) | 100GB    | Weekly    | No                        | Code, configs, small files |
| `$DATA` (`/data/<username>`) | 5TB      | No        | No                        | Analysis outputs, ntuples  |
| `$SCRATCH` (`/scratch`)      | No quota | No        | After each job (HTCondor) | Temporary job outputs      |

**LOCALGROUPDISK**: UChicago provides `MWT2_UC_LOCALGROUPDISK` (15TB capacity)
accessible via Rucio. This is a local grid storage element for dataset
replication.

**Best Practices**:

- Store code and configs in `$HOME` (100GB, backed up weekly)
- Store analysis outputs in `$DATA` (5TB, not backed up)
- Use `$SCRATCH` only for temporary job files; it is local to the worker node
  and HTCondor cleans it after each job, so copy outputs to `$DATA` before the
  job exits
- Monitor `$HOME` quota: exceeding it will block SSH login
- Use XCache or Rucio for input data instead of copying to local storage

## Running Batch Jobs (HTCondor)

UChicago AF uses HTCondor for batch job submission. Two queues are available:

- **Short Queue** (`+queue="short"`): Max 4 hours runtime, faster scheduling
- **Long Queue** (default): Max 72 hours runtime

**Basic Submit File** (`job.sub`):

```condor
universe                = vanilla
executable              = job.sh
output                  = logs/out.$(ClusterId).$(ProcId)
error                   = logs/err.$(ClusterId).$(ProcId)
log                     = logs/log.$(ClusterId)
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = input_data/
transfer_output_files   = output/
+queue                  = "short"
request_cpus            = 1
request_memory          = 2GB
request_disk            = 1GB
use_x509userproxy       = true
x509userproxy           = /home/<username>/x509proxy
queue 10
```

**Always define `log`, `output`, and `error`** in every submit file.

**MWT2 overflow**: add `+ALLOW_MWT2=True` to let jobs spill onto the wider MWT2
Tier-2 pool when the local AF pool is full.

**Docker/Singularity Support**: Specify container image with
`+SingularityImage = "/cvmfs/..."` or similar directives.

**Key Commands**:

| Command                                   | Purpose                                             |
| ----------------------------------------- | --------------------------------------------------- |
| `condor_submit job.sub`                   | Submit job                                          |
| `condor_submit -i job.sub`                | Interactive debug session                           |
| `condor_q`                                | View your jobs                                      |
| `condor_watch_q`                          | Live monitor (not `watch condor_q`)                 |
| `condor_q -hold`                          | Why a job is held                                   |
| `condor_q -analyze <ClusterId>`           | Diagnose why a job is idle                          |
| `condor_ssh_to_job <JobId>`               | SSH into a running job                              |
| `condor_qedit <JobId> RequestMemory 4096` | Edit a held/idle job, then `condor_release <JobId>` |
| `condor_rm <ClusterId>`                   | Remove job                                          |
| `condor_status`                           | View available slots                                |

Use `condor_watch_q` for live monitoring — do **not** run `watch condor_q` (it
hammers the schedd).

## JupyterLab

Access JupyterLab at `https://af.uchicago.edu/jupyterlab` (requires ATLAS
AuthZ).

**Resource Limits**:

- CPU: 1-16 cores
- Memory: 1-32 GB RAM
- GPU: 0-7 GPUs (A100 with MIG partitioning up to 28 instances)
- Session Duration: Up to 72 hours

**GPU Specs**:

- 4x NVIDIA A100 40GB GPUs
- MIG (Multi-Instance GPU) partitioning available
- Up to 28 MIG instances across all A100s

**Docker Images**:

- `ml_platform`: TensorFlow, PyTorch, scikit-learn
- `AB-stable`: AnalysisBase stable release
- `AB-dev`: AnalysisBase development release

## Data Access

### XCache

High-performance caching layer for ATLAS data. The first access through XCache
is ~2x slower; subsequent (cached) accesses are much faster.

**Recommended (let Rucio pick the optimal XCache node):**

```bash
export SITE_NAME=AF_200
rucio list-file-replicas <scope>:<name> --protocol root
```

With `SITE_NAME=AF_200` set, the returned `root://` paths already point through
the optimal XCache node for each file.

**Manual prefix** — prepend the XCache door and add `:1094` to the source server
address, e.g. a path `root://someserver.org//path` becomes:

```bash
root://xcache.af.uchicago.edu:1094//root://someserver.org:1094//path
```

### Rucio

ATLAS distributed data management system.

**Setup**:

```bash
lsetup rucio
voms-proxy-init -voms atlas
```

**List Replicas**:

```bash
rucio list-file-replicas <scope>:<dataset_name>
```

**Download Dataset**:

```bash
rucio download <scope>:<dataset_name>
```

### CERN EOS

CERN EOS is mounted on login nodes at `/eos` but NOT available on worker nodes.

**Access on Login Nodes**:

```bash
kinit <username>@CERN.CH
ls /eos/atlas/...
```

**Access on Worker Nodes**: Use `xrdcp` with full EOS URL:

```bash
xrdcp root://eosatlas.cern.ch//eos/atlas/... output.root
```

### X509 Proxy

Required for grid operations (Rucio, XRootD, CERN services).

**Generate Proxy**: write it to `$HOME` so the HTCondor scheduler can read it
(the default proxy location, `/tmp/x509up_u$(id -u)`, is not on the shared
filesystem):

```bash
voms-proxy-init -voms atlas -out $HOME/x509proxy
```

**Check Proxy**:

```bash
voms-proxy-info -all
```

In an HTCondor submit file, reference the proxy with:

```condor
use_x509userproxy = true
x509userproxy = /home/<username>/x509proxy
```

## ServiceX

Two ServiceX instances for ATLAS data delivery:

- **Uproot** (flat ntuples): `uproot-atlas.servicex.af.uchicago.edu`
- **xAOD** (ATLAS xAOD format): `xaod.servicex.af.uchicago.edu`

**Setup**:

1. Sign in at the endpoint (`https://uproot-atlas.servicex.af.uchicago.edu/` or
   `https://xaod.servicex.af.uchicago.edu/`). Sign-in goes through a Globus
   registration page; you may use your institutional account. Wait for approval.
2. Download your `servicex.yaml` from your profile page and place it in your
   working directory (or `$HOME`). The file already contains your endpoint and
   token — do not hand-write it.
3. Track request status from the dashboard on the same site.

## Coffea Casa

Coffea Casa at `https://coffea.af.uchicago.edu` provides Dask + HTCondor
autoscaling for columnar analysis with Coffea.

**Features**:

- ATLAS AuthZ integration
- Automatic HTCondor worker scaling
- Distributed Coffea analysis

## Triton Inference Server

Deploy ML models for inference at scale.

**gRPC Endpoint**: `triton-traefik.triton.svc.cluster.local:8001`

**Model Repository**: S3 bucket at `s3.af.uchicago.edu`

- Path: `s3://triton-models/<username>/`
- Upload models to `s3://triton-models/<username>/<model_name>/`

**Supported Backends**:

- TensorFlow
- PyTorch
- ONNX Runtime
- TensorRT

**Model Polling**: Triton polls the S3 repository every 60 seconds for new
models.

**Model Directory Structure**:

```
<model_name>/
  config.pbtxt
  1/
    model.onnx (or model.plan, model.pt, etc.)
```

## VSCode Integration

Connect local VSCode to JupyterLab kernels:

1. Start JupyterLab session at `https://af.uchicago.edu/jupyterlab`
2. In VSCode, install Jupyter extension
3. Select "Existing Jupyter Server" and enter the JupyterLab URL
4. Authenticate with ATLAS credentials
5. Select remote kernel from UChicago AF JupyterLab

## Hardware Summary

| Resource                   | Quantity               |
| -------------------------- | ---------------------- |
| Interactive SSH Nodes      | 4                      |
| Interactive Jupyter Nodes  | 4                      |
| HTCondor Long Queue Cores  | 1520                   |
| HTCondor Short Queue Cores | 1280                   |
| GPUs (A100 40GB)           | 2x4 = 8                |
| GPUs (V100 16GB)           | 1x4 = 4                |
| GPUs (RTX 2080 Ti 12GB)    | 3x8 = 24               |
| GPUs (GTX 1080 Ti 12GB)    | 1x8 = 8                |
| Data Storage (`/data`)     | ~5.8PB (shared CephFS) |
| Cold Storage (`/cold`)     | ~4.5PB                 |
| Home Storage (`/home`)     | ~23TB (shared NFS)     |

## Common Issues

| Issue                         | Cause                                   | Solution                                      |
| ----------------------------- | --------------------------------------- | --------------------------------------------- |
| SSH login rejected            | Deprecated key (DSA / RSA SHA-1)        | Generate ed25519 or ecdsa key                 |
| Grid commands fail            | Expired X509 proxy                      | Regenerate with `voms-proxy-init -voms atlas` |
| Cannot write files            | `$HOME` quota exceeded                  | Clean up old files or use `$DATA`             |
| Job outputs lost              | Used `$SCRATCH`                         | Use `$DATA` for persistent storage            |
| EOS mount not found on worker | EOS only on login nodes                 | Use `xrdcp` with full EOS URL on workers      |
| JupyterLab session killed     | Exceeded resource limits or 72h timeout | Reduce resource request or split work         |

## Support

- **Email**: `atlas-us-chicago-tier3-admins@cern.ch`
- **Discourse**: `atlas-talk.sdcc.bnl.gov` (ATLAS community forum)
- **Documentation**: `https://usatlas.github.io/af-docs/`
