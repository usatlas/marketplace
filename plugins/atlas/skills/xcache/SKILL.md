---
name: xcache
description: >-
  Use when setting up a local XCache disk caching proxy for XRootD root://
  protocol access: starting an xcache instance, caching remote ATLAS files on a
  laptop or Tier-3 site, using ALRB_XCACHE_PROXY with ROOT or Rucio file
  replicas, or troubleshooting VOMS proxy and cache directory issues.
---

# XCache

## Overview

XCache is a local disk caching proxy for remote file access via the XRootD
`root://` protocol. It intercepts `root://` requests, caches the data on local
disk, and serves subsequent reads from the cache. This is useful for laptops,
desktops, and Tier-3 sites that repeatedly access the same remote files — the
first access goes over the network, but subsequent accesses are local disk
speed.

## When to Use

- Running an analysis that repeatedly reads the same remote ROOT files
- Working on a laptop or desktop with limited bandwidth to WLCG storage
- Setting up a shared cache on a Tier-3 site to reduce external network traffic
- Accelerating iterative development where the same NTuples are read many times

## Key Concepts

**Local vs remote proxy**: XCache exposes two proxy endpoints after starting:

| Variable                   | Endpoint                               | Use case                                 |
| -------------------------- | -------------------------------------- | ---------------------------------------- |
| `ALRB_XCACHE_PROXY`        | `root://localhost:59560//`             | Same machine as the cache                |
| `ALRB_XCACHE_PROXY_REMOTE` | `root://atlasremote.triumf.ca:59560//` | Other machines on the same local network |

**How it works**: Prepend the proxy variable to any `root://` URI. XCache
intercepts the request, fetches blocks from the remote server, stores them on
local disk, and serves them. Repeated reads of the same blocks hit the local
cache.

**VOMS proxy required**: XCache authenticates to remote storage using a valid
VOMS proxy. A long-lived proxy (96 hours) is recommended to avoid expiry during
extended analysis sessions.

## Canonical Patterns

### Setup and start

```bash
setupATLAS
lsetup xcache
voms-proxy-init -voms atlas -valid 96:0
xcache start -d /tmp/myCache
```

### Setup alongside a release

```bash
lsetup "asetup AthAnalysis,21.2.3" xcache
voms-proxy-init -voms atlas -valid 96:0
xcache start -d /tmp/myCache
```

### Access a remote file through the local cache

```bash
root [0] TFile::Open("${ALRB_XCACHE_PROXY}root://tbn18.nikhef.nl:1094//pnfs/nikhef.nl/data/atlas/path/to/file.root")
```

The first open fetches from the remote server and caches locally. Subsequent
opens of the same file read from disk.

### Access via the remote proxy (other machines on the network)

```bash
root [0] TFile::Open("${ALRB_XCACHE_PROXY_REMOTE}root://tbn18.nikhef.nl:1094//pnfs/nikhef.nl/data/atlas/path/to/file.root")
```

### Use with Rucio file replicas

Generate cached URIs from Rucio replica output:

```bash
rucio list-file-replicas --rse SOME_RSE --protocol root --pfns scope:dataset \
  | sed -e 's/^root/${ALRB_XCACHE_PROXY}root/'
```

### Use with uproot (Python)

```python
import os
import uproot
import fsspec_xrootd  # noqa: F401 — registers root:// scheme

proxy = os.environ["ALRB_XCACHE_PROXY"]
remote_uri = "root://eosatlas.cern.ch//eos/atlas/path/to/file.root"
cached_uri = f"{proxy}{remote_uri}"

with uproot.open(f"{cached_uri}:tree") as tree:
    arrays = tree.arrays(["jet_pt", "met_met"])
```

### Stop the cache

```bash
xcache stop
```

### Check cache status

```bash
xcache status
```

### Automatic proxy renewal

For long-running sessions, configure automatic proxy delegation:

```bash
# See the example script for myproxy-based renewal
cat $ATLAS_LOCAL_ROOT_BASE/user/myproxydelegate-example.sh
```

### Use with xrdcp for bulk downloads

```bash
# Download through the cache with xrdcp
xrdcp ${ALRB_XCACHE_PROXY}root://remote-server:1094//path/to/file.root local.root
```

Subsequent xrdcp calls for the same file read from the local cache instead of
the network.

## Gotchas

- **VOMS proxy required**: XCache cannot authenticate to remote storage without
  a valid proxy. Use `voms-proxy-info --all` to check, and
  `voms-proxy-init -voms atlas -valid 96:0` to renew.
- **Cache directory can grow large**: Monitor disk usage in the cache directory.
  XCache does not automatically evict old files — manage the directory manually
  or set up a cron job.
- **Port conflicts**: The default port is 59560. If another xcache instance or
  service uses that port, `xcache start` will fail. Check with
  `netstat -tlnp | grep 59560`.
- **localhost vs remote endpoint**: `ALRB_XCACHE_PROXY` uses `localhost` and
  only works on the machine running xcache. Use `ALRB_XCACHE_PROXY_REMOTE` for
  access from other machines on the same network.
- **Environment variables disappear in new shells**: The `ALRB_XCACHE_PROXY`
  variables are set by `xcache start` in the current shell only. Re-export them
  or re-run `lsetup xcache` in new terminal sessions.
- **ATLAS energy/momentum values are in MeV**: Fields read from ATLAS NTuples
  through xcache are still in MeV — divide by 1000 for GeV-scale comparisons.

## Interop

- **setupATLAS**: `lsetup xcache` requires `setupATLAS` to be sourced first. See
  the setupatlas skill.
- **fsspec-xrootd / uproot**: Prepend the xcache proxy to `root://` URIs passed
  to uproot for cached Python access. See the fsspec-xrootd skill.
- **Rucio**: Use `rucio list-file-replicas` to obtain `root://` PFNs, then
  prepend the xcache proxy for cached access.
- **asetup**: XCache can be set up alongside a release —
  `lsetup "asetup ..." xcache` configures both in one command.

## Docs

- https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Xcache
- https://gitlab.cern.ch/atlas-tier3sw/xcache
