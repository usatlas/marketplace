---
name: fsspec-xrootd
description: >-
  Use when accessing ROOT files on EOS, WLCG grid storage, or any XRootD
  endpoint from Python: mounting an XRootD path as an fsspec filesystem, passing
  root:// URIs to uproot or awkward, listing remote directories, or
  troubleshooting XRootD authentication and proxy issues.
---

# fsspec-xrootd

## Overview

fsspec-xrootd registers the `root://` URI scheme with the `fsspec` filesystem
abstraction. Once installed, any fsspec-aware library (uproot, awkward, dask)
can read files from EOS (`root://eosatlas.cern.ch/`) or any WLCG grid site
transparently, as if they were local files. Authentication uses an X.509 proxy
or token (WLCG Bearer Token), just as the `xrdcp` command-line tool would.

## When to Use

- Reading ATLAS NTuples stored on EOS from a laptop or analysis facility
- Running uproot or coffea over files referenced by PFN (physical file name)
  from Rucio
- Listing directory contents on EOS without `eos` or `xrdfs` shell tools
- Passing `root://` URIs from `rucio list-file-replicas` output directly to
  uproot

## Key Concepts

| Concept                | Notes                                                                |
| ---------------------- | -------------------------------------------------------------------- |
| `fsspec_xrootd` import | Must be imported before `uproot.open`; registers `root://` scheme    |
| `root://` URI          | XRootD path: `root://eosatlas.cern.ch//eos/atlas/...`                |
| Two packages required  | `pip install fsspec-xrootd xrootd` — both must be present            |
| X.509 proxy            | `voms-proxy-init --voms atlas` before opening remote files           |
| WLCG Bearer Token      | Alternative to X.509: `export BEARER_TOKEN=$(cat /tmp/bt_u$(id -u))` |
| `fsspec.filesystem()`  | Direct filesystem object for listing directories                     |

Install:

```bash
pip install fsspec-xrootd xrootd   # both packages required

voms-proxy-init --voms atlas        # or set BEARER_TOKEN
```

## Canonical Patterns

### Transparent uproot access

```python
import uproot
import fsspec_xrootd   # noqa: F401 — registers root:// scheme with fsspec

# uproot uses fsspec automatically for root:// URIs
with uproot.open("root://eosatlas.cern.ch//eos/atlas/atlascerngroupdisk/..."
                 ":reco") as tree:
    arrays = tree.arrays(["jet_pt", "weight_mc"])
```

### Iterate over remote files

```python
import uproot, fsspec_xrootd  # noqa: F401

for batch in uproot.iterate(
    "root://eosatlas.cern.ch//eos/atlas/path/to/ntuples/*.root:reco",
    ["jet_pt", "met_met"],
    step_size=100_000,
):
    pass
```

### List a remote directory

```python
import fsspec

fs = fsspec.filesystem("root", hostid="eosatlas.cern.ch")
files = fs.ls("/eos/atlas/atlascerngroupdisk/my/path/")
for f in files:
    print(f["name"], f["size"])
```

### Open a file directly via fsspec

```python
import fsspec

with fsspec.open("root://eosatlas.cern.ch//eos/atlas/path/file.root", "rb") as f:
    data = f.read(1024)   # raw bytes
```

### Build a file list from Rucio PFNs

```python
# After: rucio list-file-replicas --pfns user.me:my.container
pfns = [
    "root://eosatlas.cern.ch//eos/atlas/.../file1.root",
    "root://eosatlas.cern.ch//eos/atlas/.../file2.root",
]
import uproot, fsspec_xrootd  # noqa: F401

arrays = uproot.concatenate(
    [f"{pfn}:reco" for pfn in pfns],
    ["jet_pt", "weight_mc"],
)
```

## Gotchas

- **Two packages required**: `fsspec-xrootd` (fsspec plugin) and `xrootd`
  (Python bindings for the XRootD C++ library). Both must be installed.
- **`import fsspec_xrootd` must happen before `uproot.open`**: the import
  registers the `root://` scheme handler.
- **Proxy lifetime**: Grid proxies expire after 12–24 hours; VOMS-extended
  proxies after 96 hours. Running long coffea jobs overnight may hit proxy
  expiry.
- **EOS quota and rate limits**: EOS has per-user open-file and bandwidth
  limits; for large-scale processing use Rucio to stage files to a local
  filesystem or use an analysis facility with EOS access.
- **`[ERROR] AuthorizationFailed`**: proxy expired or missing — run
  `voms-proxy-info --all` and `voms-proxy-init --voms atlas`.
- **`[ERROR] No servers are available`**: wrong hostname or endpoint down —
  check with `xrdfs root://eosatlas.cern.ch/ ping`.
- **`Module 'XRootD' not found`**: `xrootd` Python bindings not installed —
  `pip install xrootd`.
- **Slow reads**: reading many small chunks over WAN — increase uproot
  `step_size` or use an EOS-local analysis facility.
- **`FileNotFoundError` on valid path**: trailing slash or case sensitivity —
  verify with `fs.ls()`.

## Interop

- **uproot**: `root://` URIs work transparently after `import fsspec_xrootd`.
- **Rucio / atlas-data-explorer**: Obtain PFNs from Rucio replicas; pass
  directly to uproot via fsspec-xrootd.
- **coffea**: coffea's dask executor works with `root://` file lists via
  fsspec-xrootd.

## Docs

https://coffeateam.github.io/fsspec-xrootd/
