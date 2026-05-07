---
name: fsspec-xrootd
description: >-
  Use when accessing ROOT files on EOS, WLCG grid storage, or any XRootD
  endpoint from Python: mounting an XRootD path as an fsspec filesystem, passing
  root:// URIs to uproot or awkward, listing or writing remote directories,
  multi-site replica access, or troubleshooting XRootD authentication and proxy
  issues.
---

# fsspec-xrootd

## Overview

fsspec-xrootd registers the `root` protocol with the `fsspec` filesystem
abstraction via an entry-point (`fsspec.specs`) — no explicit import is needed
once the package is installed. Any fsspec-aware library (uproot, awkward, dask)
can then read or write files on EOS (`root://eosatlas.cern.ch/`) or any WLCG
grid site transparently. Authentication uses an X.509 proxy or WLCG Bearer
Token, just as `xrdcp` would.

## When to Use

- Reading ATLAS NTuples stored on EOS from a laptop or analysis facility
- Running uproot or coffea over files referenced by PFN (physical file name)
  from Rucio
- Listing directory contents on EOS without `eos` or `xrdfs` shell tools
- Passing `root://` URIs from `rucio list-file-replicas` output directly to
  uproot
- Accessing files from multiple WLCG grid sites with automatic replica selection

## Key Concepts

| Concept               | Notes                                                                   |
| --------------------- | ----------------------------------------------------------------------- |
| Auto-registration     | Installed via entry point `fsspec.specs`; no explicit import needed     |
| `root://` URI         | XRootD path: `root://eosatlas.cern.ch//eos/atlas/...`                   |
| `[xrootd]` extra      | `pip install "fsspec-xrootd[xrootd]"` — bundles the XRootD C++ bindings |
| X.509 proxy           | `voms-proxy-init --voms atlas` before opening remote files              |
| WLCG Bearer Token     | Alternative to X.509: `export BEARER_TOKEN=$(cat /tmp/bt_u$(id -u))`    |
| `fsspec.filesystem()` | Direct filesystem object; `hostid` is a required parameter              |
| `locate_all_sources`  | Finds all replicas; defaults to `True`. Set `False` for redirector-only |
| `valid_sources`       | Allowlist of hostnames to restrict replica selection                    |
| `timeout`             | XRootD client timeout in seconds; `0` (default) means no timeout        |

Install:

```bash
pip install "fsspec-xrootd[xrootd]"    # one package, one extra
# or
conda install -c conda-forge fsspec-xrootd

voms-proxy-init --voms atlas             # or set BEARER_TOKEN
```

## Canonical Patterns

### Transparent uproot access

After installation the `root://` scheme is auto-registered. Explicit
`import fsspec_xrootd` is harmless but not required.

```python
import uproot

with uproot.open("root://eosatlas.cern.ch//eos/atlas/atlascerngroupdisk/..."
                 ":reco") as tree:
    arrays = tree.arrays(["jet_pt", "weight_mc"])
```

### Iterate over remote files

```python
import uproot

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
import uproot

arrays = uproot.concatenate(
    [f"{pfn}:reco" for pfn in pfns],
    ["jet_pt", "weight_mc"],
)
```

### Multi-site replica access

When reading via a WLCG redirector, `locate_all_sources` finds every server
holding the file and picks the best. Use `valid_sources` to restrict which sites
are tried (entries must be bare hostnames, no port).

```python
import fsspec

fs = fsspec.filesystem(
    "root",
    hostid="cms-xrd-global.cern.ch",     # WLCG global redirector
    locate_all_sources=True,
    valid_sources=["cmsxrootd-site1.fnal.gov", "xrootd.unl.edu"],
)
with fs.open("/store/mc/path/to/file.root", "rb") as f:
    ...
```

### Write a file to EOS

```python
import fsspec

fs = fsspec.filesystem("root", hostid="eosatlas.cern.ch")
with fs.open("/eos/atlas/user/m/myuser/output/result.txt", "wb") as f:
    f.write(b"result data")
```

### Query server checksum

```python
import fsspec

fs = fsspec.filesystem("root", hostid="eosatlas.cern.ch")
algorithm, value = fs.checksum("/eos/atlas/path/file.root")
print(f"{algorithm}: {value}")   # e.g. "adler32: 1a2b3c4d"
```

### Storage options for performance tuning

```python
import fsspec

fs = fsspec.filesystem(
    "root",
    hostid="eosatlas.cern.ch",
    timeout=60,                    # seconds; 0 = no timeout (default)
    filehandle_cache_size=512,     # max open file handles cached (default 256)
    filehandle_cache_ttl=60,       # seconds before cached handles expire (default 30)
)
```

## Gotchas

- **`[xrootd]` extra is required**: Install as
  `pip install "fsspec-xrootd[xrootd]"`. The bare `pip install fsspec-xrootd`
  omits the XRootD C++ bindings. If you see
  `ModuleNotFoundError: No module named 'XRootD'`, re-install with the extra.
- **No explicit import needed**: `root://` is auto-registered via the fsspec
  entry-point (`fsspec.specs`) when the package is installed. Explicit
  `import fsspec_xrootd` is safe but unnecessary in normal installed usage.
- **`valid_sources` hostnames have no port**: entries like
  `cmsxrootd-site1.fnal.gov` are bare domain names; the port is stripped
  automatically from XRootD replies.
- **Proxy lifetime**: Grid proxies expire after 12–24 hours; VOMS-extended
  proxies after 96 hours. Long coffea jobs running overnight may hit proxy
  expiry.
- **EOS quota and rate limits**: EOS has per-user open-file and bandwidth
  limits; for large-scale processing use Rucio to stage files to a local
  filesystem or use an analysis facility with EOS access.
- **`[ERROR] AuthorizationFailed`**: proxy expired or missing — run
  `voms-proxy-info --all` and `voms-proxy-init --voms atlas`.
- **`[ERROR] No servers are available`**: wrong hostname or endpoint down —
  check with `xrdfs root://eosatlas.cern.ch/ ping`.
- **Slow reads**: reading many small chunks over WAN — increase uproot
  `step_size` or use an EOS-local analysis facility.
- **`FileNotFoundError` on valid path**: trailing slash or case sensitivity —
  verify with `fs.ls()`.
- **Linux only**: fsspec-xrootd is only tested on Linux (XRootD C++ library
  constraint).
- **ATLAS energy/momentum values are in MeV**: fields like `jet_pt`, `met_met`
  come from ATLAS NTuples in MeV — divide by 1000 before GeV-scale comparisons.

## Interop

- **uproot**: `root://` URIs work transparently after installation via the entry
  point; no additional import required.
- **Rucio / atlas-data-explorer**: Obtain PFNs from Rucio replicas; pass
  directly to uproot via fsspec-xrootd.
- **coffea**: coffea's dask executor works with `root://` file lists via
  fsspec-xrootd.

## Docs

https://scikit-hep.org/fsspec-xrootd/
