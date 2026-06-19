---
name: migrate
description: >-
  Use when migrating a directory of local ROOT files to BNL-OSG2_LOCALGROUPDISK
  via Rucio on BNL SDCC nodes, or for any sub-step of that workflow: pre-flight
  checks (Rucio account, grid proxy, quotas, RSE names, pnfs mount), monitoring
  a Rucio replication rule until it reaches OK/STUCK, or building a symlink farm
  from an already-replicated dataset for transparent proxy-free access.
---

## Overview

End-to-end migration of a directory of ROOT files to BNL LOCALGROUPDISK. Handles
pre-flight checks, upload to scratchdisk, replication, symlink farm creation,
and optional codebase path adaptation with safe rollback.

For a **partial workflow** (run one phase standalone — e.g. you already
replicated and only need the symlink farm, or you just want to re-check your
proxy, or resume monitoring an existing rule), follow the bundled reference for
that phase instead of the full pipeline:

- `references/preflight.md` — the 5 prerequisite checks, standalone
- `references/check-rule.md` — monitor a Rucio rule ID to OK/STUCK
- `references/build-symlinks.md` — build a symlink farm from an
  already-replicated dataset

Arguments:

- `$source_dir` — absolute path to the directory containing `.root` files
- `$dataset_name` — Rucio dataset name (no scope prefix), e.g.
  `powheg_cc_evgen_truth`

If any argument is missing, ask the user before proceeding.

### Autonomous mode

If the user's message includes **any** of these phrases (case-insensitive): "no
confirmation", "no confirm", "autonomous", "proceed without confirmation", "all
steps without confirmation", "no questions" — then **skip all interactive
prompts** and use defaults:

- Survey (Step 1): proceed without asking
- Decision Point 1: **upload + symlink swap**
- Decision Point 2: **same-path swap**
- `_orig` guard (Step 7): **does not stop** — a pre-existing
  `${source_dir}_orig` is never overwritten; the backup goes to a unique name
- DID conflict (Step 2): still STOP — real problem, not a preference

The one exception to "no questions": the **Final step** always asks whether to
delete the `$BACKUP_DIR` backup (never automatic — irreversible and the only
rollback path). This runs once, at the very end, after all work is done.

The user can pre-answer individual decision points in their message (e.g.,
"using same-path swap" or "upload only"). Honor explicit choices over defaults.
Autonomous mode only suppresses the _prompt_ — all checks, verifications, and
error stops still run.

## When to Use

- Migrating ROOT files from personal pnfs/dCache or local storage to permanent
  LOCALGROUPDISK storage at BNL
- The skill presents three decision points:
  1. **Upload + symlink swap** (default) vs **upload only**
  2. **Same-path swap** (default, zero code changes) vs **different path**
  3. If different path: **full integration** (scan code, update paths, test,
     rollback-safe) vs **symlink only**

## Key Concepts

- **Phase 1 (upload + replicate)**: always runs — uploads files to scratchdisk,
  creates a Rucio dataset, adds a replication rule to LOCALGROUPDISK, waits for
  completion.
- **Phase 2 (symlink farm)**: builds a directory of symlinks pointing to
  LOCALGROUPDISK pnfs paths. For same-path swap, renames the original directory
  to `_orig` and places the farm at the original path (atomic swap via staging
  directory).
- **Phase 3 (full integration)**: different-path only — creates a git branch,
  scans codebase for path references (including constructed paths, config files,
  aliases), proposes edits, tests compilation and TTree entry counts, rolls back
  on failure.
- **Rucio scope**: `user.<account>` — derived from `rucio whoami`.
- **PFN prefix**: `root://dcgftp.usatlas.bnl.gov:1094/` — strip this to get the
  local pnfs path for symlinks.
- **FTS queue**: user-priority transfers wait 1–12 hours; actual transfer is ~5
  min per 100 GB.

## Canonical Patterns

### Environment setup

All `rucio` and `voms-proxy-*` commands below require the ATLAS environment.
Bootstrap it **once per shell** as documented in the `setupatlas` skill (sources
ALRB, exposes `lsetup`), then set up Rucio:

```bash
# Bootstrap per the setupatlas skill, then:
lsetup rucio >/dev/null 2>&1
```

In a non-interactive shell where the `setupATLAS` alias is not defined, source
ALRB directly first (see the `setupatlas` skill for details):

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
```

Subsequent code blocks assume the environment is already set up.

### Prerequisites (5 pre-flight checks)

Before starting, run all checks. STOP and report if any fails.

**Check 1 — Rucio account:**

```bash
rucio whoami 2>/dev/null
```

Record the `account` name — used as `user.<account>` scope throughout.

**Check 2 — Grid proxy:**

```bash
voms-proxy-info --all 2>&1
```

- Must have >2 hours remaining (>24h recommended). If <2h, tell user to run
  `voms-proxy-init -voms atlas:/atlas/usatlas -valid 96:00` (the explicit group
  is required — plain `-voms atlas` may omit `/atlas/usatlas`).
- VOMS attributes must include `/atlas/usatlas` — **required for LOCALGROUPDISK
  quota**. If missing, direct user to `https://atlas-auth.cern.ch/`.

**Check 3 — RSE names:**

```bash
rucio list-rses 2>/dev/null | grep -i "BNL-OSG2"
```

Must show `BNL-OSG2_LOCALGROUPDISK` and `BNL-OSG2_SCRATCHDISK`.

**Check 4 — Quotas:**

```bash
ACCOUNT=$(rucio whoami 2>/dev/null | grep "account" | awk '{print $2}')
rucio list-account-limits $ACCOUNT 2>/dev/null \
  | grep -E "BNL-OSG2_(LOCALGROUPDISK|SCRATCHDISK)"
rucio list-account-usage $ACCOUNT 2>/dev/null \
  | grep BNL-OSG2_SCRATCHDISK
```

- LOCALGROUPDISK must show a limit (default 50 TB). If missing, the user needs
  `/atlas/usatlas` VOMS group membership.
- SCRATCHDISK: check available space for staging the upload.

**Check 5 — pnfs mount:**

```bash
ls /pnfs/usatlas.bnl.gov/LOCALGROUPDISK/ 2>&1 | head -3
```

Must be accessible at `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/` (not
`atlaslocalgroupdisk`).

**Report pre-flight results** as a summary table:

| Check         | Status       | Details                     |
| ------------- | ------------ | --------------------------- |
| Rucio account | OK/FAIL      | account name                |
| Grid proxy    | OK/WARN/FAIL | time remaining, VOMS groups |
| RSE names     | OK/FAIL      | confirmed names             |
| LGD quota     | OK/FAIL      | limit                       |
| Scratchdisk   | OK/FAIL      | limit, used                 |
| pnfs mount    | OK/FAIL      | path                        |

STOP if any check is FAIL.

### Phase 1: Upload and replicate (always runs)

Execute sequentially. Stop on any error and report. Derive `$SCOPE` from the
Rucio account (e.g., account `jdoe` → `$SCOPE` = `user.jdoe`).

**Step 1 — Survey source files:**

```bash
ls -1 "$source_dir"/*.root | head -5
ls -1 "$source_dir"/*.root | wc -l
du -sh "$source_dir"
```

Check for non-`.root` files:

```bash
find "$source_dir" -maxdepth 1 -type f ! -name '*.root' 2>/dev/null
```

If any non-`.root` files are found, **warn the user**:

> **Warning:** `$source_dir` contains non-`.root` files that will NOT be
> included in the migration:
>
> ```text
> <list of files>
> ```
>
> If your analysis code expects these files (metadata, logs, config), the
> symlink farm will be missing them and your code may break. Options:
>
> 1. **Proceed anyway** — only `.root` files will be migrated
> 2. **Abort** — manually handle the extra files first
>
> In autonomous mode: proceed with warning noted in output.

Report: number of `.root` files, total size, any non-`.root` files. Confirm with
the user before proceeding.

**Step 2 — Check for DID conflicts:**

Check **every** `.root` file, not just the first — a collision on any one of
them must be caught before upload:

```bash
for f in "$source_dir"/*.root; do
  rucio list-dids "$SCOPE:$(basename "$f")" 2>/dev/null
done
```

If any file already exists as a DID under the user's scope, STOP and warn.
Options: (a) reuse existing DID if it has a scratchdisk replica — skip to Step
4; (b) rename with a suffix (last resort).

**Step 3 — Upload to scratchdisk:**

```bash
rucio upload --rse BNL-OSG2_SCRATCHDISK --scope $SCOPE \
  "$source_dir"/*.root
```

**Source files are NOT modified or deleted.** ~30s per 4 GB file. For

> 50 files, upload in batches. STOP on any error — nothing to clean up.

**Step 4 — Create dataset and attach files:**

```bash
rucio add-dataset $SCOPE:$dataset_name
rucio list-dids "$SCOPE:*" --type FILE --short 2>/dev/null | tail -5
rucio attach $SCOPE:$dataset_name $SCOPE:<file_pattern>
```

Verify: `rucio list-files $SCOPE:$dataset_name` should show all files.

**Step 5 — Add replication rule:**

```bash
RULE_ID=$(rucio add-rule $SCOPE:$dataset_name 1 \
  BNL-OSG2_LOCALGROUPDISK)
echo "Rule ID: $RULE_ID"
```

**Step 5b — Wait for replication:**

Poll the rule until state reaches `OK` or `STUCK`. Use the Monitor tool:

```bash
RULE_ID="<RULE_ID>"
prev=""
while true; do
  info=$(rucio rule-info $RULE_ID 2>/dev/null)
  state=$(echo "$info" | grep "^State:" | awk '{print $2}')
  locks=$(echo "$info" | grep "^Locks" | sed 's/.*: //')
  cur="State=$state Locks=$locks"
  if [ "$cur" != "$prev" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') $cur"
    prev="$cur"
  fi
  if [ "$state" = "OK" ]; then
    echo "REPLICATION COMPLETE"
    exit 0
  fi
  if [ "$state" = "STUCK" ]; then
    echo "REPLICATION STUCK — check: rucio rule-info $RULE_ID"
    exit 1
  fi
  sleep 120
done
```

Use `timeout: 3600000` (1 hour). If it times out, re-run — FTS queue waits of
1–12 hours are normal. If `STUCK`, report the error and STOP.

### Decision Points

**Decision Point 1 — Migration mode** (after replication reaches OK):

> 1. **Upload + symlink swap** (default) — build a symlink farm for transparent
>    local access
> 2. **Upload only** — data is on LOCALGROUPDISK, stop here

Upload only → no symlink farm and no backup. **Go to the Final step** (summary
only; no cleanup decision).

**Decision Point 2 — Symlink placement:**

> 1. **Same-path swap** (default) — rename `source_dir` to `source_dir_orig`,
>    place symlink farm at `source_dir`. Analysis code works without any
>    changes.
> 2. **Different path** — place symlink farm at a separate location (user
>    provides the path).

Same-path swap → set `$farm_dir = $source_dir`, go to Phase 2. Different path →
ask user for `$farm_dir`, go to Decision Point 3.

**Decision Point 3 — Code integration** (different-path only):

> 1. **Full integration** (default) — build symlink farm, scan codebase for
>    references to the old path, update code, test with safe rollback. All
>    changes on a git branch (`lgd-migrate-<dataset>`).
> 2. **Symlink only** — build symlink farm at the new path, no code changes.

Symlink only → go to Phase 2 (skip rename step). Full integration → go to
Phase 3.

### Phase 2: Symlink farm

**Step 6 — Get PFNs:**

```bash
rucio list-file-replicas $SCOPE:$dataset_name \
  --protocols root --pfns --rses BNL-OSG2_LOCALGROUPDISK \
  > /tmp/pfns_${dataset_name}.txt
```

**Step 7 — Build symlink farm:**

**If same-path swap** (`$farm_dir == $source_dir`):

Build the farm in a staging directory first, then do an atomic swap.

Guard checks (these **never stop** the run — the only `_orig` decision is the
deletion at the very end, see the Final step):

1. If `${source_dir}_lgd_staging` exists (leftover), remove it.
2. Choose a backup directory `$BACKUP_DIR` that does not clobber any existing
   one, so a leftover `${source_dir}_orig` from a previous migration is never
   overwritten and never halts the run:

```bash
BACKUP_DIR="${source_dir}_orig"
[ -e "$BACKUP_DIR" ] && BACKUP_DIR="${source_dir}_orig.$(date +%Y%m%d_%H%M%S)"
echo "Backup directory: $BACKUP_DIR"
```

Build the staging farm:

```bash
STAGING="${source_dir}_lgd_staging"
mkdir -p "$STAGING"
while read -r pfn; do
  pnfs_path="${pfn#root://dcgftp.usatlas.bnl.gov:1094/}"
  filename=$(basename "$pnfs_path")
  ln -s "$pnfs_path" "$STAGING/$filename"
done < /tmp/pfns_${dataset_name}.txt
```

Verify staging count before swapping:

```bash
ORIG_COUNT=$(ls -1 "$source_dir"/*.root 2>/dev/null | wc -l)
FARM_COUNT=$(ls -1 "$STAGING" | wc -l)
echo "Original: $ORIG_COUNT files, Farm: $FARM_COUNT symlinks"
```

If counts match, perform the swap:

```bash
mv "$source_dir" "$BACKUP_DIR"
mv "$STAGING" "$source_dir"
```

If the second `mv` fails, immediately restore:

```bash
mv "$BACKUP_DIR" "$source_dir"
rm -rf "$STAGING"
```

**If different path:**

```bash
mkdir -p "$farm_dir"
while read -r pfn; do
  pnfs_path="${pfn#root://dcgftp.usatlas.bnl.gov:1094/}"
  filename=$(basename "$pnfs_path")
  ln -s "$pnfs_path" "$farm_dir/$filename"
done < /tmp/pfns_${dataset_name}.txt
```

**Step 8 — Verify:**

1. Symlink count matches source file count: `ls -1 "$farm_dir" | wc -l`
2. Spot-check one symlink resolves:
   `ls -la "$farm_dir"/$(ls "$farm_dir" | head -1)`
3. ROOT readability check:

   ```bash
   root -b -l -q -e '
     auto f=TFile::Open("'"$farm_dir"'/$(ls $farm_dir | head -1)");
     cout << (f && !f->IsZombie() ? "OK" : "FAIL") << endl;'
   ```

**Step 8b — Smoke test (same-path swap only):**

Three checks compare the backup `$BACKUP_DIR` (original local files, renamed in
Step 7) against the farm `$farm_dir` (symlinks to the LOCALGROUPDISK replicas).
Run them in order and STOP at the first failure. The smoke test PASSES only if
all three pass.

**(1) Filename set** — nothing dropped, added, or duplicated:

```bash
diff <(cd "$BACKUP_DIR" && ls -1 *.root | sort) \
     <(cd "$farm_dir" && ls -1 *.root | sort) \
  && echo "FILENAMES MATCH" || echo "FILENAMES MISMATCH"
```

**(2) Per-file TTree entry counts** — compared file-by-file (not a single
chained total, so offsetting errors across files cannot cancel). Reads only
TTree metadata, so it is fast even for large datasets:

```bash
root -b -l -q -e '
  #include <TSystemDirectory.h>
  #include <TSystemFile.h>
  #include <TFile.h>
  #include <TTree.h>
  #include <TKey.h>
  #include <iostream>
  using namespace std;
  TString od = "'"$BACKUP_DIR"'", fd = "'"$farm_dir"'";
  TSystemDirectory dir(od, od);
  TIter nf(dir.GetListOfFiles());
  TSystemFile *sf; bool ok = true;
  while ((sf = (TSystemFile*)nf())) {
    TString fn = sf->GetName();
    if (sf->IsDirectory() || !fn.EndsWith(".root")) continue;
    TFile *fp = TFile::Open(od+"/"+fn), *ff = TFile::Open(fd+"/"+fn);
    if (!fp || fo->IsZombie() || !ff || ff->IsZombie()) {
      cout << fn << ": FAIL open" << endl; ok = false; continue; }
    TIter nk(fo->GetListOfKeys()); TKey *k;
    while ((k = (TKey*)nk())) {
      if (TString(k->GetClassName()) != "TTree") continue;
      TString tn = k->GetName();
      TTree *to = (TTree*)fo->Get(tn), *tf = (TTree*)ff->Get(tn);
      Long64_t no = to ? to->GetEntries() : -1;
      Long64_t ne = tf ? tf->GetEntries() : -2;
      if (no != ne) {
        cout << fn << ":" << tn << " orig=" << no << " farm=" << ne
             << " MISMATCH" << endl; ok = false; }
    }
    fo->Close(); ff->Close();
  }
  cout << (ok ? "PER-FILE COUNTS MATCH" : "PER-FILE COUNTS MISMATCH") << endl;
'
```

**(3) Content checksum (adler32)** — authoritative byte-level check. Rucio
registers an adler32 per file at upload and FTS verifies the replica against it
before the rule reaches `OK`, so comparing each **local source** file's adler32
to its **Rucio-registered** adler32 proves source ≡ replica without re-reading
from LOCALGROUPDISK:

```bash
# Rucio-registered checksums (NAME + ADLER32 columns)
rucio list-files $SCOPE:$dataset_name 2>/dev/null
# Local source checksums (xrdadler32 ships with xrootd; `lsetup xrootd` if absent)
for f in "$BACKUP_DIR"/*.root; do
  printf '%s %s\n' "$(basename "$f")" "$(xrdadler32 "$f" | awk '{print $1}')"
done
```

Every file's local adler32 must equal its Rucio-registered adler32. To compare
the farm replicas directly instead (reads from LOCALGROUPDISK, slower), run
`xrdadler32 "$farm_dir"/*.root` and match against the source values.

Checks (1)+(3) together guarantee file-by-file content equality; (2) is a fast,
checksum-free cross-check.

- **PASSED**: data verified on LOCALGROUPDISK. Do **not** delete the backup here
  — the `$BACKUP_DIR` deletion decision is deferred to the **Final step**.
  Proceed there.
- **FAILED**: report the mismatch. Do NOT delete the backup. Offer to roll back:
  `mv "$farm_dir" "${farm_dir}_lgd"; mv "$BACKUP_DIR" "$source_dir"`.

**DONE for Phase 2 → go to the Final step.**

### Phase 3: Full integration (different-path with code changes)

All changes are on a rollback-safe git branch.

**Step 6 — Save working tree state:**

```bash
git status --porcelain
```

If dirty, ask: (a) Commit first (recommended), or (b) Stash. Record
`STASH_CREATED` and stash ref if applicable.

**Step 6b — Create migration branch:**

```bash
BASE_BRANCH=$(git symbolic-ref --short HEAD)
git checkout -b lgd-migrate-${dataset_name}
```

Record `$BASE_BRANCH` — used for rollback (never hardcode `main`).

**Step 7 — Get PFNs and build symlink farm:**

Same as Phase 2 Steps 6–8, different-path variant (do NOT rename `$source_dir`).

**Step 8 — Find and update path references:**

Search the codebase for references to `$source_dir`. Do not stop at literal
string matches — handle these edge cases:

- **Constructed paths**: `base_dir + subdir + filename`. Search for directory
  basename, parent name, and representative filenames.
- **Multiple indirection levels**: a base directory set in one file, used in
  another, passed as argument to a third.
- **Config files and scripts**: `.cfg`, `.json`, `.yaml`, `.sh`, job submission
  files.
- **Relative vs absolute**: `~/`, `$HOME`, or symlinks resolving to
  `$source_dir`.

For each match, classify the hit and propose the edit. Present the list to the
user for confirmation before applying. Show `git diff --stat` after editing.

If no references found, ask the user which file defines the path. If unknown,
exit with manual instructions and skip to Step 10 with `Test result: SKIPPED`.

**Step 9 — Test run:**

_Level 1 — ROOT-level verification (always run):_ Open a sample file, verify not
zombie, compare TTree entry counts via TChain between original and farm.
MISMATCH → STOP and roll back.

_Level 2 — Analysis-level test (if code was changed):_ Attempt compilation
(ACLiC for ROOT macros, framework build system otherwise). If possible without
disruption, run minimal test in a temp directory (never overwrite original
outputs). If test would require Condor or long runtime, report:

```text
Verified: compilation OK, TChain entry counts match (<N> entries).
Not tested: full analysis run (requires <reason>).
Recommended: run <specific command> and compare output.
```

**Step 9b — Finalize or roll back:**

If tests pass: commit changes, restore stash (report conflicts if any), suggest
merging `lgd-migrate-<dataset>` into `$BASE_BRANCH`.

If tests fail: report error, revert all changes, delete branch, restore stash,
report:

```text
## Migration test FAILED: <dataset_name>
- Error: <error output>
- Rollback: all code changes reverted, branch deleted
- Stash: <restored / restored with conflicts / none>
- Symlink farm at $farm_dir still intact (harmless)
- Original files at $source_dir unchanged
```

**DONE for Phase 3 → go to the Final step.** (Phase 3 keeps the source dir in
place and creates no `$BACKUP_DIR`, so the Final step only writes the summary.)

### Final step — Summary and backup cleanup

Every path ends here. Write the migration summary, then make the backup-cleanup
decision. This is the **last** action of the run, and in autonomous mode it is
the **only** question asked — nothing earlier stops for it.

**Summary** (include the fields that apply to the path taken):

```text
## LOCALGROUPDISK Migration: <dataset_name>
- Source: $source_dir (<N> files, <size>)
- Dataset: $SCOPE:$dataset_name
- Rule ID: $RULE_ID
- Symlink farm: $farm_dir
- Backup (same-path swap only): $BACKUP_DIR
- Code files modified (full integration only): <list or "none">
- Test result (full integration only): PASS / FAIL / SKIPPED
- Branch (full integration only): lgd-migrate-<dataset> (base: $BASE_BRANCH)
```

**Backup cleanup** — only when a same-path swap created `$BACKUP_DIR`
(upload-only and different-path runs have no backup; skip this and finish):

The original files are preserved at `$BACKUP_DIR`. Deleting it is irreversible
and it is the only rollback path, so it is **never deleted automatically**. Ask
the user — a plain question, not a stop, in every mode including autonomous:

- Warn that the backup is retained at `$BACKUP_DIR`, and that removing it
  reclaims the local/pnfs space the migration was likely meant to free.
- Offer the choice: (a) have the agent delete `$BACKUP_DIR` now (then report
  space freed), or (b) keep it and remove it manually later.
- Delete only on explicit choice (a). This is the single end-of-run question in
  autonomous mode.

## Worked Example

Suppose you have 25 Monte Carlo ROOT files (98 GB total) at
`/pnfs/usatlas.bnl.gov/users/<you>/mc_sample/` and want them on LOCALGROUPDISK
with a symlink farm at the original path.

```text
/bnl-localgroupdisk:migrate /pnfs/usatlas.bnl.gov/users/<you>/mc_sample mc_sample_truth
```

1. **Pre-flight**: all 5 checks pass.
2. **Survey**: 25 `.root` files, 98 GB.
3. **Upload**: `rucio upload --rse BNL-OSG2_SCRATCHDISK` — ~12 min.
4. **Dataset**: `user.<you>:mc_sample_truth`, 25 files attached.
5. **Replication rule**: returns rule ID. FTS queue: 1–12 hours.
6. **Decision Point 1**: upload + symlink swap (default).
7. **Decision Point 2**: same-path swap (default).
8. **Symlink farm**: renames original to `mc_sample_orig`, creates symlinks at
   the original path.
9. **Smoke test**: filename set, per-file entry counts, and adler32 all match —
   PASSED.
10. **Final step**: prints the summary; backup `mc_sample_orig` is retained
    (never auto-deleted) and the run ends by asking whether to delete it now or
    leave it for manual removal.

After migration: analysis code reads from the same path — no changes needed. No
grid proxy required.

## Troubleshooting

| Step | Problem                        | What happens                                            |
| ---- | ------------------------------ | ------------------------------------------------------- |
| 2    | `Database error` (dup DID)     | Stops, offers reuse or rename                           |
| 5    | `insufficient quota`           | Stops, directs to ATLAS IAM for VOMS group              |
| 5b   | Rule stuck at 0/N for hours    | Normal FTS queue delay; skill documents expected timing |
| 8    | Symlinks don't resolve         | Checks pnfs mount; reports if unavailable               |
| 8    | Crash between rename and build | Farm built in staging dir first, then atomic swap       |
| 8    | ROOT can't open file           | Reports failure; original at `$BACKUP_DIR` is intact    |
| 8    | Code search finds nothing      | Asks user; exits with manual instructions if unknown    |
| 9    | Test fails after code edits    | Rolls back all changes, deletes branch, restores stash  |
| 9b   | Stash pop has merge conflict   | Reports conflicting files, asks user to resolve         |

## Gotchas

- **Pre-existing `_orig` never stops the run**: if `${source_dir}_orig` already
  exists from a previous migration, the skill does not stop or overwrite it — it
  backs up to a unique `${source_dir}_orig.<timestamp>` (`$BACKUP_DIR`) instead.
- **DID conflict**: if filenames are already registered in Rucio, the skill
  stops even in autonomous mode — this indicates a real problem.
- **Non-`.root` files**: the skill only uploads `.root` files. If the source
  directory contains metadata, logs, or config files, the symlink farm will be
  missing them. The skill warns about this.
- **Source files are never deleted**: `rucio upload` copies files. The original
  directory is only renamed (to `$BACKUP_DIR`) during same-path swap.
- **Backup is never auto-deleted**: even after a passing smoke test, and even in
  autonomous mode, the skill never removes `$BACKUP_DIR` on its own — deletion
  is irreversible and the backup is the sole rollback path. The decision is made
  once, in the Final step, as a plain question (the single end-of-run prompt in
  autonomous mode).
- **Smoke test depth**: Step 8b verifies the filename set, per-file TTree entry
  counts, and per-file adler32 (local source vs Rucio-registered, which FTS
  validated against the replica). adler32 + matching filenames already prove
  byte-level content equality; it is not just an entry-count check.

### Rollback

At no point are source files modified or deleted. Full rollback:

```bash
rm -rf "$farm_dir"
mv "$BACKUP_DIR" "$source_dir"   # if same-path swap
rucio delete-rule $RULE_ID
rucio erase $SCOPE:$dataset_name
# If full integration:
git checkout "$BASE_BRANCH" -- .
git checkout "$BASE_BRANCH"
git branch -D lgd-migrate-${dataset_name}
```

## Interop

- Symlink farm files are readable without grid proxy on SDCC nodes.
- Grid proxy and VOMS are only needed during upload and replication; use
  `-valid 96:00` since FTS can take up to 12 hours.
- Same-path swap is the recommended default: TChain and TFile::Open work
  transparently with symlinks — zero code changes needed.
- RSE names: `BNL-OSG2_LOCALGROUPDISK`, `BNL-OSG2_SCRATCHDISK` (note
  hyphen/underscore positions).
- LOCALGROUPDISK pnfs mount on SDCC: `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/`.
- Files land at:
  `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<username>/<2-char-hash>/<2-char-hash>/<filename>`.
- Default quota: 50 TB per user.
- `rucio upload` copies files — source is never modified or deleted.
- FTS queue wait: typically 1–12 hours; actual transfer is minutes.

## Docs

- [bnl-localgroupdisk plugin](https://github.com/FlamyFlame/claude-bnl-localgroupdisk)
- [BNL SDCC storage documentation](https://usatlas.github.io/af-docs/bnl/storage/)
