---
name: bnl-localgroupdisk-build-symlinks
description: >-
  Use when you need to build a symlink farm from an already-replicated Rucio
  dataset on BNL-OSG2_LOCALGROUPDISK for transparent proxy-free access on BNL
  SDCC nodes.
---

## Overview

Create a directory of symlinks pointing to LOCALGROUPDISK pnfs paths for
a given Rucio dataset. Each symlink maps a flat filename to the
hash-based LOCALGROUPDISK path so analysis code can read files
transparently without path changes or grid proxy.

Arguments:

- `$dataset_name` — Rucio dataset with scope
  (e.g., `user.jdoe:my_dataset`)
- `$farm_dir` — absolute path where the symlink farm will be created

If arguments are missing, ask the user.

## When to Use

- After a replication rule reaches state OK and you need local symlinks
- When data is already on LOCALGROUPDISK (e.g., from a previous migration
  or a colleague's upload) and you just need the local access layer
- Inside `/bnl-localgroupdisk:migrate`, this runs automatically — call
  standalone only for partial workflows

## Key Concepts

- **Hash-based storage**: LOCALGROUPDISK stores files under
  `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<username>/<2-char>/<2-char>/`.
  The symlink farm recreates a flat directory layout your analysis code
  expects.
- **PFN prefix**: Rucio returns PFNs like
  `root://dcgftp.usatlas.bnl.gov:1094//pnfs/...`. Strip the xrootd
  prefix to get the local pnfs path for the symlink target.
- **No proxy needed**: symlinks resolve through the pnfs mount on SDCC
  nodes — no grid proxy required at read time.

## Canonical Patterns

### Step 1: Get PFNs

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
rucio list-file-replicas $dataset_name \
  --protocols root --pfns --rses BNL-OSG2_LOCALGROUPDISK
```

Each line should look like:

```text
root://dcgftp.usatlas.bnl.gov:1094//pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<user>/<hash>/<hash>/<filename>.root
```

If empty, the replication rule is not yet complete — use
`/bnl-localgroupdisk:check-rule`.

### Step 2: Build symlinks

First, check if `$farm_dir` already exists with contents:

```bash
if [ -d "$farm_dir" ] && [ "$(ls -A "$farm_dir" 2>/dev/null)" ]; then
  echo "WARNING: $farm_dir already exists and is non-empty"
  echo "$(ls -1 "$farm_dir" | wc -l) entries"
  ls -la "$farm_dir" | head -10
fi
```

If non-empty, ask the user whether to **(a)** remove existing symlinks
first (`rm "$farm_dir"/*`) and rebuild, or **(b)** abort.

Then create the symlinks:

```bash
mkdir -p "$farm_dir"
rucio list-file-replicas $dataset_name \
  --protocols root --pfns --rses BNL-OSG2_LOCALGROUPDISK \
  > /tmp/pfns_build.txt
while read -r pfn; do
  pnfs_path="${pfn#root://dcgftp.usatlas.bnl.gov:1094/}"
  filename=$(basename "$pnfs_path")
  ln -s "$pnfs_path" "$farm_dir/$filename"
done < /tmp/pfns_build.txt
```

### Step 3: Verify

```bash
echo "Symlink count: $(ls -1 "$farm_dir" | wc -l)"
echo "Sample symlink:"
ls -la "$farm_dir"/$(ls "$farm_dir" | head -1)
```

Confirm: symlink count matches expected file count, and the target path
exists.

## Gotchas

- **Non-empty `$farm_dir`**: if the directory already has files or
  symlinks (e.g., from a previous attempt), building on top will create
  duplicates or errors. Always check and ask before proceeding.
- **Empty PFN output**: means replication is not complete — do not
  proceed, use `/bnl-localgroupdisk:check-rule` instead.

## Interop

- No grid proxy is needed to read files via symlinks on SDCC nodes.
- Symlinks point to pnfs paths under
  `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<account>/` — these
  resolve on any BNL SDCC node with the pnfs mount.
- TChain and TFile::Open work transparently with symlinks — analysis
  code needs no changes.

## Docs

- [bnl-localgroupdisk plugin](https://github.com/FlamyFlame/claude-bnl-localgroupdisk)
- [BNL SDCC storage documentation](https://usatlas.github.io/af-docs/bnl/storage/)
