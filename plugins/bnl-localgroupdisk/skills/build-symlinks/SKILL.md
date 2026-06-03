---
description: >
  Build a symlink farm from a Rucio dataset on BNL-OSG2_LOCALGROUPDISK.
  Extracts PFNs, strips the xrootd prefix, and creates one symlink per file
  pointing to the actual pnfs path. Use after replication rule reaches state OK.
disable-model-invocation: false
arguments: [dataset_name, farm_dir]
argument-hint: "<scope:dataset_name> <farm_dir>"
allowed-tools: Bash
---

# Build symlink farm from LOCALGROUPDISK dataset

Create a directory of symlinks pointing to LOCALGROUPDISK pnfs paths for
dataset `$dataset_name`, at location `$farm_dir`.

If arguments are missing, ask the user.

`$dataset_name` should include scope (e.g., `user.jdoe:my_dataset`, where `jdoe` is your Rucio account name from `rucio whoami`).

## Step 1: Get PFNs

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
rucio list-file-replicas $dataset_name \
  --protocols root --pfns --rses BNL-OSG2_LOCALGROUPDISK
```

Each line should look like:
```
root://dcgftp.usatlas.bnl.gov:1094//pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<user>/<hash>/<hash>/<filename>.root
```

If empty, the replication rule is not yet complete — use `/bnl-localgroupdisk:check-rule`.

## Step 2: Build symlinks

Save the PFN output from Step 1 to a temp file, then create symlinks:

First, check if `$farm_dir` already exists with contents:

```bash
if [ -d "$farm_dir" ] && [ "$(ls -A "$farm_dir" 2>/dev/null)" ]; then
  echo "WARNING: $farm_dir already exists and is non-empty ($(ls -1 "$farm_dir" | wc -l) entries)"
  echo "Contents:"
  ls -la "$farm_dir" | head -10
fi
```

If non-empty, ask the user whether to **(a)** remove existing symlinks first (`rm "$farm_dir"/*`) and rebuild, or **(b)** abort.

Then create the symlinks:

```bash
mkdir -p "$farm_dir"
rucio list-file-replicas $dataset_name \
  --protocols root --pfns --rses BNL-OSG2_LOCALGROUPDISK > /tmp/pfns_build.txt
# For each PFN, strip the xrootd prefix to get the local pnfs path
while read -r pfn; do
  pnfs_path="${pfn#root://dcgftp.usatlas.bnl.gov:1094/}"
  filename=$(basename "$pnfs_path")
  ln -s "$pnfs_path" "$farm_dir/$filename"
done < /tmp/pfns_build.txt
```

## Step 3: Verify

```bash
echo "Symlink count: $(ls -1 "$farm_dir" | wc -l)"
echo "Sample symlink:"
ls -la "$farm_dir"/$(ls "$farm_dir" | head -1)
```

Confirm: symlink count matches expected file count, and the target path exists.

## How it works

LOCALGROUPDISK stores files in hash-based subdirectories under
`/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<username>/<2-char>/<2-char>/`.
The symlink farm recreates the flat directory layout your analysis code expects
by putting one symlink per file in a single directory, each pointing to the
actual pnfs path. No grid proxy is needed to read via these symlinks on SDCC.
