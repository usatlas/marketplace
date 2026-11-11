---
name: af-uchicago
description: >-
  Use when working with the UChicago ATLAS Analysis Facility, submitting
  HTCondor batch jobs at UChicago, launching notebooks with BinderHub at
  binderhub.af.uchicago.edu (or asking about the retired AF Portal JupyterLab),
  using XCache or Rucio for ATLAS data at UChicago, deploying ML models on
  Triton at UChicago AF, setting up ServiceX or Coffea Casa, or troubleshooting
  SSH access to login.af.uchicago.edu
---

# UChicago ATLAS Analysis Facility Workflow

## Overview

The UChicago ATLAS Analysis Facility (UChicago AF) provides ATLAS physicists
with interactive nodes (SSH + BinderHub notebooks), HTCondor batch computing,
GPU resources, and advanced data services (XCache, Rucio, ServiceX, Coffea Casa,
Triton). It is part of the MWT2 Tier-2 center supporting US ATLAS computing.

## When to Use

- Setting up access to login.af.uchicago.edu or af.uchicago.edu
- Submitting HTCondor batch jobs for ATLAS analysis
- Launching BinderHub notebook servers with CPU/GPU resources
- Accessing ATLAS data via XCache or Rucio
- Using ServiceX for data delivery or Coffea Casa for columnar analysis
- Deploying ML models on Triton Inference Server
- Troubleshooting storage quota, proxy, or SSH issues at UChicago

## Quick Reference

| Resource          | Value                                                    |
| ----------------- | -------------------------------------------------------- |
| SSH Login         | `login.af.uchicago.edu`                                  |
| BinderHub         | `https://binderhub.af.uchicago.edu`                      |
| XCache            | `root://xcache.af.uchicago.edu:1094//`                   |
| ServiceX (Uproot) | `uproot-atlas.servicex.af.uchicago.edu`                  |
| ServiceX (xAOD)   | `xaod.servicex.af.uchicago.edu`                          |
| Coffea Casa       | `https://coffea.af.uchicago.edu`                         |
| Triton gRPC       | `triton-traefik.triton.svc.cluster.local:8001`           |
| Triton S3         | `s3://triton-models/<username>/` at `s3.af.uchicago.edu` |
| MCP Endpoint      | `https://mcp.af.uchicago.edu/mcp`                        |
| MCP Portal        | `https://mcp-portal.af.uchicago.edu/`                    |
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

**Linked credentials in jobs**: jobs can receive the credentials the user linked
on the MCP Platform (VOMS proxy, CERN Kerberos ticket, ServiceX token) without
anyone copying them around. Request each with `use_oauth_services`; HTCondor
delivers and refreshes it on the worker as `$_CONDOR_CREDS/af_<kind>.use`.

- Call `af_list_identities` first: each linked identity usable in jobs carries a
  `job_credential` with the `service` to request, the file `path`, its `format`,
  and the `env` assignment tools read it from. Do not guess kinds.
- Never `cat`, `echo`, or `base64` these files — job output is returned
  verbatim. Reference them only through the environment variables.
- If a kind is missing, route the user to `af_link_identity` or the portal.
- `klist` is not in the worker image; check a krb5 cache with
  `od -An -tx1 -N2 "$_CONDOR_CREDS/af_krb5.use"` (`05 04` is valid).
- Login nodes already set `CREDD_HOST`, so `condor_submit` there works too.

```condor
use_oauth_services = af_x509, af_krb5
```

```bash
#!/bin/bash
# job.sh: set env vars after any setup that may override them (e.g. lsetup emi)
export X509_USER_PROXY="$_CONDOR_CREDS/af_x509.use"
export KRB5CCNAME="FILE:$_CONDOR_CREDS/af_krb5.use"
voms-proxy-info --timeleft
```

## BinderHub Notebooks

Launch notebooks from BinderHub at `https://binderhub.af.uchicago.edu`. The AF
Portal JupyterLab (`https://af.uchicago.edu/jupyterlab`) is retired; point users
to BinderHub instead.

- Pick an image under **Curated Repositories** (`ml-platform:latest` is the
  recommended default), or launch from a Git repository.
- Set resources in **Advanced setting**: site (UC AF, ssl, nrp), GPU model and
  count, CPU, memory, and **QoS → Guaranteed** to reserve exactly what is
  requested.
- Servers are JupyterHub named servers at
  `https://jupyterhub.af.uchicago.edu/user/<username>/<server-name>/`.
- On the UC AF site, notebooks start in `/home/<username>` with `/data` and
  `/cvmfs` mounted; files saved elsewhere are lost when the server stops.
- Idle servers are stopped after 24 hours; relaunch to continue.

**GPU Specs**:

- Models include NVIDIA A100 SXM4 40GB (full and MIG slices), H200 NVL (MIG
  slices), Tesla V100, RTX 2080 Ti, and GTX 1080 Ti; pick one under **Advanced
  setting**, which shows free/total counts, or choose "Any"
- For current per-node models and counts, see
  `https://usatlas.github.io/af-docs/uchicago/hardware/`

**Docker Images**:

- `ml-platform:latest`: TensorFlow, PyTorch, scikit-learn (recommended)
- `ml-platform-cpu:<release>` / `ml-platform-gpu:<release>`: CPU or GPU builds,
  `latest` or a pinned release such as `2026.11.4`
- `AB-STABLE`: AnalysisBase stable release
- `AB-DEV`: AnalysisBase development release

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

Connect local VSCode to a BinderHub notebook server's kernel:

1. Launch a server from `https://binderhub.af.uchicago.edu`
2. Create a JupyterHub API token at
   `https://jupyterhub.af.uchicago.edu/hub/token` with the `access:servers`
   scope
3. In VSCode, install the Jupyter extension, then select "Existing Jupyter
   Server" and enter
   `https://jupyterhub.af.uchicago.edu/user/<username>/<server-name>/?token=<token>`
4. Select the remote kernel; after a relaunch, the same token reconnects

## MCP Platform

UChicago AF runs the AF MCP Platform, a credential-brokered
[Model Context Protocol](https://modelcontextprotocol.io/) gateway that exposes
Rucio, AMI, HTCondor, JupyterHub, and AF filesystem tools to LLM clients such as
Claude Code and Claude Desktop.

- **MCP endpoint**: `https://mcp.af.uchicago.edu/mcp` — point an MCP-over-HTTP
  client at this URL. Most clients auto-discover the broker's OAuth endpoints
  and open a browser to log in; no manual token setup is needed.
- **Portal**: `https://mcp-portal.af.uchicago.edu/` — web UI for the platform.
- **Personal Access Tokens**: for clients that cannot do the browser-based OAuth
  flow, generate a static bearer token at
  `https://mcp-portal.af.uchicago.edu/tokens/`, then wire it in as an
  `Authorization: Bearer <token>` header:
  - **Claude Code**:
    `claude mcp add --transport http atlas-af https://mcp.af.uchicago.edu/mcp/ --header "Authorization: Bearer $MCP_BEARER_TOKEN"`
    (export the token to that env var first).
  - **Claude Desktop / Claude.ai**: Settings > Connectors > Add custom
    connector > Request headers — Name `Authorization`, Value `Bearer <token>`,
    marked Required.
- **Identities**: link your ATLAS/CERN identity to your AF account at
  `https://mcp-portal.af.uchicago.edu/identities/` — required before the broker
  can mint per-user Rucio/AMI/x509 credentials on your behalf.

The `atlas-af` server's tools are named `<prefix>_<tool>`, one prefix per
backend service (Rucio, AMI, HTCondor, JupyterHub, ServiceX, filesystem, ATLAS
search, ...). Services and their prefixes change as backends are added or
renamed, so do not hard-code tool names — discover them at run time:

- `af_list_mcp_servers` — every configured service, its tool-name prefix, the
  identity it needs, and its availability to the caller. Availability is the
  broker's last-known status, not a live probe of the backend, so it can lag a
  recovery or an outage; if a service shows unavailable but its tools are
  listed, try a read-only call before concluding it is down.
- `af_whoami` / `af_list_identities` — the caller's permissions and which
  identities are linked; `af_link_identity` starts linking a missing one.

The gateway's own `af_*` tools are the stable entry point; use them first when
an expected tool is missing or a call fails.

This overlaps with domains the `atlas` plugin also covers via CLI (Rucio in the
setupatlas, eiclient, panda, servicex, and centralpage skills; AMI/pyAMI in
setupatlas and centralpage). When both plugins are installed, prefer the
Rucio/AMI MCP tools above over those skills' CLI commands when available — the
MCP path needs no `lsetup`/VOMS-proxy setup, but only works once the user has
linked their identity (check with `af_whoami`).

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

| Issue                         | Cause                            | Solution                                                  |
| ----------------------------- | -------------------------------- | --------------------------------------------------------- |
| SSH login rejected            | Deprecated key (DSA / RSA SHA-1) | Generate ed25519 or ecdsa key                             |
| Grid commands fail            | Expired X509 proxy               | Regenerate with `voms-proxy-init -voms atlas`             |
| Cannot write files            | `$HOME` quota exceeded           | Clean up old files or use `$DATA`                         |
| Job outputs lost              | Used `$SCRATCH`                  | Use `$DATA` for persistent storage                        |
| EOS mount not found on worker | EOS only on login nodes          | Use `xrdcp` with full EOS URL on workers                  |
| Notebook server stopped       | Idle for 24 hours                | Relaunch from BinderHub; files in `/home`/`/data` persist |

## Support

- **Email**: `atlas-us-chicago-tier3-admins@cern.ch`
- **Discourse**: `atlas-talk.sdcc.bnl.gov` (ATLAS community forum)
- **Documentation**: `https://usatlas.github.io/af-docs/`
