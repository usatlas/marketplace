---
description: >
  Migrate a directory of local ROOT files to BNL-OSG2_LOCALGROUPDISK via Rucio
  (upload to scratchdisk, replicate, optionally build symlink farm and adapt
  analysis code). Use when the user wants to move ROOT files from personal
  pnfs/dCache or local storage to LOCALGROUPDISK for permanent, proxy-free
  access on BNL SDCC nodes.
disable-model-invocation: false
arguments: [source_dir, dataset_name]
argument-hint: "<source_dir> <dataset_name>"
allowed-tools: Bash Read Edit Monitor
---

# Migrate ROOT files to BNL-OSG2_LOCALGROUPDISK

Migrate a directory of ROOT files to BNL LOCALGROUPDISK. Depending on user
choice, optionally build a symlink farm and adapt analysis code.

## Arguments

- `$source_dir` — absolute path to the directory containing `.root` files
- `$dataset_name` — Rucio dataset name (no scope prefix), e.g. `powheg_cc_evgen_truth`

If any argument is missing, ask the user before proceeding.

## Autonomous mode

If the user's message includes **any** of these phrases (case-insensitive):
- "no confirmation", "no confirm", "autonomous", "proceed without confirmation",
  "all steps without confirmation", "no questions"

Then **skip all interactive prompts** and use these defaults:
- Survey (Step 1): proceed without asking
- Decision Point 1: **upload + symlink swap**
- Decision Point 2: **same-path swap**
- `_orig` guard (Step 7): remove existing `_orig` and proceed
- DID conflict (Step 2): still STOP — this indicates a real problem, not a preference

The user can also pre-answer individual decision points in their message
(e.g., "using same-path swap" or "upload only"). Honor explicit choices
over defaults. Autonomous mode only suppresses the *prompt* — all checks,
verifications, and error stops still run.

## Prerequisites

Before starting, run all 5 pre-flight checks. STOP and report if any fails.

### Check 1: Rucio account

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
rucio whoami 2>/dev/null
```

Record the `account` name — used as `user.<account>` scope throughout.

### Check 2: Grid proxy

```bash
voms-proxy-info --all 2>&1
```

- Proxy must have >2 hours remaining (>24h recommended for large uploads).
  If <2h, tell user to run `voms-proxy-init -voms atlas -valid 96:00`
- VOMS attributes must include `/atlas/usatlas` — **required for LOCALGROUPDISK quota**.
  If missing, direct user to ATLAS IAM (`https://atlas-auth.cern.ch/`).

### Check 3: RSE names

```bash
rucio list-rses 2>/dev/null | grep -i "BNL-OSG2"
```

Must show `BNL-OSG2_LOCALGROUPDISK` and `BNL-OSG2_SCRATCHDISK`.

### Check 4: Quotas

```bash
ACCOUNT=$(rucio whoami 2>/dev/null | grep "account" | awk '{print $2}')
rucio list-account-limits $ACCOUNT 2>/dev/null | grep -E "BNL-OSG2_(LOCALGROUPDISK|SCRATCHDISK)"
rucio list-account-usage $ACCOUNT 2>/dev/null | grep BNL-OSG2_SCRATCHDISK
```

- LOCALGROUPDISK must show a limit (default 50 TB). If missing, the user
  needs `/atlas/usatlas` VOMS group membership.
- SCRATCHDISK: check available space for staging the upload.

### Check 5: pnfs mount

```bash
ls /pnfs/usatlas.bnl.gov/LOCALGROUPDISK/ 2>&1 | head -3
```

The LOCALGROUPDISK pnfs mount must be accessible at
`/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/` (not `atlaslocalgroupdisk`).
If not accessible, symlink farm will produce broken symlinks.

### Report pre-flight results

Report a summary table:

| Check | Status | Details |
|-------|--------|---------|
| Rucio account | OK/FAIL | account name |
| Grid proxy | OK/WARN/FAIL | time remaining, VOMS groups |
| RSE names | OK/FAIL | confirmed names |
| LGD quota | OK/FAIL | limit |
| Scratchdisk | OK/FAIL | limit, used |
| pnfs mount | OK/FAIL | path |

STOP if any check is FAIL.

## Phase 1: Upload and replicate (always runs)

Execute sequentially. Stop on any error and report.
Derive `$SCOPE` from the Rucio account (e.g., account `jdoe` → `$SCOPE` = `user.jdoe`).

### Step 1: Survey source files

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
> ```
> <list of files>
> ```
> If your analysis code expects these files (metadata, logs, config), the
> symlink farm will be missing them and your code may break. Options:
> 1. **Proceed anyway** — only `.root` files will be migrated
> 2. **Abort** — manually handle the extra files first
>
> In autonomous mode: proceed with warning noted in output.

Report: number of `.root` files, total size, any non-`.root` files.
Confirm with the user before proceeding.

### Step 2: Check for DID conflicts

```bash
rucio list-dids "$SCOPE:$(basename <first_file>)" 2>&1
```

If any file already exists as a DID under the user's scope, STOP and warn.
Options: (a) reuse existing DID if it has a scratchdisk replica — skip to
Step 4; (b) rename with a suffix (last resort).

### Step 3: Upload to scratchdisk

```bash
rucio upload --rse BNL-OSG2_SCRATCHDISK --scope $SCOPE "$source_dir"/*.root
```

**Source files are NOT modified or deleted.** ~30s per 4 GB file. For >50 files,
upload in batches. STOP on any error — nothing to clean up.

### Step 4: Create dataset and attach files

```bash
rucio add-dataset $SCOPE:$dataset_name
```

List uploaded DIDs to find the pattern:

```bash
rucio list-dids "$SCOPE:*" --type FILE --short 2>/dev/null | tail -5
```

Attach using a wildcard matching the uploaded files:

```bash
rucio attach $SCOPE:$dataset_name $SCOPE:<file_pattern>
```

Verify: `rucio list-files $SCOPE:$dataset_name` should show all files.

### Step 5: Add replication rule

```bash
RULE_ID=$(rucio add-rule $SCOPE:$dataset_name 1 BNL-OSG2_LOCALGROUPDISK)
echo "Rule ID: $RULE_ID"
```

**Expect long waits.** FTS queue: 1–12 hours (user priority). Actual transfer:
~5 min per 100 GB. 0/N locks for hours is normal. Do NOT proceed until
`State: OK`.

### Step 5b: Wait for replication

Poll the rule until state reaches `OK` or `STUCK`. Use the Monitor tool
with this script (substitute `$RULE_ID` from Step 5):

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
    echo "REPLICATION STUCK — check error with: rucio rule-info $RULE_ID"
    exit 1
  fi
  sleep 120
done
```

Use `timeout: 3600000` (1 hour). If it times out, re-run — FTS queue waits
of 1–12 hours are normal.

If `STUCK`, report the error and STOP. The user can check status later with
`/bnl-localgroupdisk:check-rule $RULE_ID`.

---

## Decision Point 1: Migration mode

After replication reaches `State: OK`, ask the user:

> **Migration mode:**
> 1. **Upload + symlink swap** (default) — build a symlink farm for transparent local access
> 2. **Upload only** — data is on LOCALGROUPDISK, stop here
>
> Which mode?

- **Upload only** → report rule ID, dataset name, total size. **DONE.**
- **Upload + symlink swap** → proceed to Decision Point 2.

## Decision Point 2: Symlink placement

Ask the user:

> **Symlink farm location:**
> 1. **Same-path swap** (default) — rename `source_dir` to `source_dir_orig`, place symlink farm at `source_dir`. Analysis code works without any changes.
> 2. **Different path** — place symlink farm at a separate location (you must provide the path).
>
> Which placement?

- **Same-path swap** → set `$farm_dir = $source_dir`. Go to **Phase 2: Symlink farm**.
- **Different path** → ask user for `$farm_dir`. Go to **Decision Point 3**.

## Decision Point 3: Code integration (different-path only)

This only applies when `$farm_dir != $source_dir`.

Ask the user:

> **Code integration:**
> 1. **Full integration** (default) — build symlink farm, scan codebase for references to the old path, update code, test with safe rollback.
> 2. **Symlink swap only** — build symlink farm at the new path, no code changes.
>
> **Note:** Full integration uses the `Edit` tool to modify source files in
> your repository. All changes are made on a git branch
> (`pre-lgd-migrate-<dataset>`) and can be rolled back cleanly.
> Do you approve?

- **Symlink swap only** → go to **Phase 2: Symlink farm** (skip rename step).
- **Full integration** (with user approval) → go to **Phase 3: Full integration**.

---

## Phase 2: Symlink farm

### Step 6: Get PFNs

```bash
rucio list-file-replicas $SCOPE:$dataset_name \
  --protocols root --pfns --rses BNL-OSG2_LOCALGROUPDISK > /tmp/pfns_${dataset_name}.txt
```

### Step 7: Build symlink farm

**If same-path swap** (`$farm_dir == $source_dir`):

Build the farm in a staging directory first, then do an atomic swap. This
avoids a window where neither the original nor the farm exists at `$source_dir`.

**Guard checks (before starting):**

1. If `${source_dir}_lgd_staging` exists (leftover from a previous attempt),
   remove it: `rm -rf "${source_dir}_lgd_staging"`.
2. If `${source_dir}_orig` exists (previous backup), STOP and ask the user:

   > `${source_dir}_orig` already exists (likely from a previous migration).
   > Options:
   > 1. **Remove it** and proceed (the data is already on LOCALGROUPDISK)
   > 2. **Abort** — investigate first
   >
   > Which option?

   If the user chooses to remove: `rm -rf "${source_dir}_orig"`, then proceed.

```bash
STAGING="${source_dir}_lgd_staging"
mkdir -p "$STAGING"
while read -r pfn; do
  pnfs_path="${pfn#root://dcgftp.usatlas.bnl.gov:1094/}"
  filename=$(basename "$pnfs_path")
  ln -s "$pnfs_path" "$STAGING/$filename"
done < /tmp/pfns_${dataset_name}.txt
```

Verify staging has the correct count before swapping:

```bash
ORIG_COUNT=$(ls -1 "$source_dir"/*.root 2>/dev/null | wc -l)
FARM_COUNT=$(ls -1 "$STAGING" | wc -l)
echo "Original: $ORIG_COUNT files, Farm: $FARM_COUNT symlinks"
```

If counts match, perform the swap:

```bash
mv "$source_dir" "${source_dir}_orig"
mv "$STAGING" "$source_dir"
```

If the second `mv` fails for any reason, immediately restore:

```bash
mv "${source_dir}_orig" "$source_dir"
rm -rf "$STAGING"
```

**If different path**:

```bash
mkdir -p "$farm_dir"
while read -r pfn; do
  pnfs_path="${pfn#root://dcgftp.usatlas.bnl.gov:1094/}"
  filename=$(basename "$pnfs_path")
  ln -s "$pnfs_path" "$farm_dir/$filename"
done < /tmp/pfns_${dataset_name}.txt
```

### Step 8: Verify

1. Symlink count matches source file count:
   ```bash
   ls -1 "$farm_dir" | wc -l
   ```
2. Spot-check one symlink resolves:
   ```bash
   ls -la "$farm_dir"/$(ls "$farm_dir" | head -1)
   ```
3. ROOT readability check:
   ```bash
   root -b -l -q -e 'auto f=TFile::Open("'"$farm_dir"'/$(ls $farm_dir | head -1)"); cout << (f && !f->IsZombie() ? "OK" : "FAIL") << endl;'
   ```

### Step 8b: Smoke test (same-path swap only)

For same-path swap, the original files are preserved at `${source_dir}_orig`.
Compare TTree entry counts between original and farm to verify data integrity:

```bash
root -b -l -q -e '
  #include <TChain.h>
  #include <TFile.h>
  #include <TKey.h>
  #include <iostream>
  using namespace std;
  auto f = TFile::Open("'"${source_dir}_orig"'/$(ls "${source_dir}_orig" | head -1)");
  if (!f || f->IsZombie()) { cout << "FAIL: cannot open original" << endl; return; }
  TIter next(f->GetListOfKeys());
  TKey *key;
  bool all_ok = true;
  while ((key = (TKey*)next())) {
    if (TString(key->GetClassName()) != "TTree") continue;
    TString name = key->GetName();
    TChain orig(name), farm(name);
    orig.Add("'"${source_dir}_orig"'/*.root");
    farm.Add("'"$farm_dir"'/*.root");
    Long64_t n_orig = orig.GetEntries(), n_farm = farm.GetEntries();
    cout << name << ": orig=" << n_orig << " farm=" << n_farm
         << (n_orig == n_farm ? " MATCH" : " MISMATCH") << endl;
    if (n_orig != n_farm) all_ok = false;
  }
  f->Close();
  cout << (all_ok ? "SMOKE TEST PASSED" : "SMOKE TEST FAILED") << endl;
'
```

- **PASSED**: report results, then ask:

  > Smoke test passed. The original files at `${source_dir}_orig` are no
  > longer needed. Delete them to free disk space?
  > 1. **Yes, delete** (default) — `rm -rf "${source_dir}_orig"`
  > 2. **Keep for now** — you can delete manually later
  >
  > In autonomous mode: delete `_orig`.

  Report final disk space freed (from `du -sh` in Step 1).

- **FAILED**: report the mismatch. **Do NOT delete `_orig`.** Offer to roll
  back the swap (`mv "$farm_dir" "${farm_dir}_lgd"; mv "${source_dir}_orig" "$source_dir"`).

**DONE for Phase 2.**

---

## Phase 3: Full integration (different-path with code changes)

This phase modifies source code. All changes are on a rollback-safe git branch.

### Step 6: Save working tree state

Check for uncommitted changes:

```bash
git status --porcelain
```

**If dirty working tree**, ask the user:

> You have uncommitted changes. Before creating a migration branch, choose:
> 1. **Commit first** (recommended) — commit your current work, then proceed
> 2. **Stash** — stash changes, proceed, restore after (risk: merge conflicts on restore)
>
> Which option?

- **Commit first**: stage and commit the user's current changes with a
  descriptive message (e.g., "WIP: save state before LOCALGROUPDISK migration").
  Show the commit hash, then proceed.
- **Stash**: run `git stash --include-untracked -m "pre-lgd-migrate-${dataset_name}"`.
  Record `STASH_CREATED=true` and the stash ref (`git stash list | head -1`).

**If clean working tree**, proceed directly. Set `STASH_CREATED=false`.

### Step 6b: Detect base branch and create migration branch

```bash
BASE_BRANCH=$(git symbolic-ref --short HEAD)
git checkout -b lgd-migrate-${dataset_name}
```

Record `$BASE_BRANCH` — used for all rollback operations (never hardcode `main`).

### Step 7: Get PFNs and build symlink farm

Same as Phase 2, Steps 6–8 (different-path variant — do NOT rename `$source_dir`).

### Step 8: Find and update path references in the codebase

**Goal:** Find every place in the codebase that references `$source_dir` or
contributes to constructing the path to it, and update those references to
point to `$farm_dir`.

Search the codebase for references to `$source_dir`. You are an agent with
code understanding — use grep, file reading, and code tracing as needed.
Do not stop at literal string matches.

**Edge cases to handle** (these are common in analysis codebases and easy to miss):

- **Constructed paths**: codebases often build data paths from variables,
  e.g., `base_dir + subdir + filename`. A grep for the full `$source_dir`
  will miss these. Search for the directory basename, parent directory name,
  and representative filenames (stems without `.root`) to find the
  construction site.
- **Multiple levels of indirection**: a base directory may be set in one
  file, used to construct a path in another, and passed as an argument to a
  third. Trace the full chain.
- **Config files and scripts**: paths may live in `.cfg`, `.json`, `.yaml`,
  `.sh`, or job submission files, not just source code.
- **Relative vs absolute**: the code may use `~/` or `$HOME` or a symlink
  that resolves to `$source_dir`. Check for these aliases.

**After searching, for each match:**

Read the surrounding code to understand context. Classify the hit and
propose the appropriate edit — a literal string replacement, a variable
value update, or a base-directory change, depending on how the path is
constructed. Present the classified list to the user and ask for
confirmation before applying any edits. Show `git diff --stat` after editing.

**If no references found:**

Ask the user: "No code references to `$source_dir` or its components were
found. Do you know which file(s) define the path to this data?"

- **If user provides file(s)**: read them, identify the path definition,
  propose the edit, apply with confirmation.
- **If user does not respond or says they don't know**: exit Phase 3 with
  clear instructions:

  ```
  ## Manual action required: <dataset_name>

  The symlink farm is ready at: $farm_dir
  But no code references to the old path were found automatically.

  To complete the migration, you need to:
  1. Find where your analysis code defines the path to this data
     (look for base directory variables, config files, or path
     construction logic)
  2. Update that path definition to point to: $farm_dir
  3. Test: run your analysis and verify output matches previous results

  The symlink farm and migration branch (lgd-migrate-<dataset>) are
  intact. Original data at $source_dir is unchanged.
  ```

  Then skip to Step 10 (summary) with `Test result: SKIPPED (no code refs found)`.

### Step 9: Test run

Two levels of testing, run sequentially.

**Level 1: ROOT-level verification (always run)**

Open a sample file from the symlink farm, verify it is not zombie, list the
TTrees it contains. For each TTree, compare entry counts between the
original directory and the farm using TChain. Report MATCH or MISMATCH for
each tree.

If MISMATCH on any tree, STOP — report the discrepancy and go to rollback.

**Level 2: Analysis-level test (if code was changed)**

If Step 8 modified code files, test whether the modified code still works
with the new paths. **Critical: never overwrite original analysis outputs** —
redirect all test output to a temp directory.

Read the modified code to understand how it is compiled and invoked. Try to
compile it (e.g., ACLiC for ROOT macros). If compilation succeeds and a
test run is possible without disruption (no Condor submission, no
long-running jobs, no writing to shared output directories), run it with
minimal input (e.g., one file batch, smallest available dataset slice).

**Edge cases:**
- If the code is part of a larger framework with its own build system,
  attempt the framework's build command rather than standalone ACLiC.
- If the test would require Condor, long runtime, or is unclear how to
  invoke, do not attempt it. Report what was verified and what remains:

  ```
  Verified: compilation OK, TChain entry counts match (<N> entries).
  Not tested: full analysis run (requires <reason>).
  Recommended: run <specific command> and compare output against previous results.
  ```

### Step 9b: Finalize or roll back

**If all tests pass:**
- Commit code changes:
  ```bash
  git add -A
  git commit -m "migrate ${dataset_name}: update paths to LOCALGROUPDISK symlink farm"
  ```
- Restore stash if `STASH_CREATED=true`:
  ```bash
  git stash pop
  ```
  If stash pop fails (merge conflict):
  - Report the conflicting files.
  - Ask the user to resolve. Do NOT resolve automatically.
  - Once resolved (or user says to drop the stash): proceed.
- Suggest: merge `lgd-migrate-${dataset_name}` into `$BASE_BRANCH` when
  satisfied, then optionally delete original files.

**If any test fails:**
- Report the error with full output.
- Roll back all code changes:
  ```bash
  git checkout "$BASE_BRANCH" -- .
  git checkout "$BASE_BRANCH"
  git branch -D lgd-migrate-${dataset_name}
  ```
- Restore stash if `STASH_CREATED=true`:
  ```bash
  git stash pop
  ```
  If stash pop fails (merge conflict): report conflicting files, ask user.
- Report:
  ```
  ## Migration test FAILED: <dataset_name>
  - Error: <error output>
  - Rollback: all code changes reverted, branch deleted
  - Stash: <restored / restored with conflicts / none>
  - Symlink farm at $farm_dir still intact (harmless)
  - Original files at $source_dir unchanged
  - Suggested next steps: <specific diagnosis>
  ```

### Step 10: Write summary

If the repository has `.claude/logs/` or a tracking doc area, write results
there. Otherwise output to the user.

```
## LOCALGROUPDISK Migration: <dataset_name>
- Source: $source_dir (<N> files, <size>)
- Dataset: $SCOPE:$dataset_name
- Rule ID: $RULE_ID
- Symlink farm: $farm_dir
- Code files modified: <list or "none">
- Test result: PASS / FAIL / SKIPPED
- Branch: lgd-migrate-${dataset_name} (base: $BASE_BRANCH)
- Stash: <committed before / stashed+restored / none>
- Original preserved at: $source_dir (unchanged)
```

**DONE for Phase 3.**

---

## Rollback

At no point are source files modified or deleted. Full rollback:

```bash
# Remove symlink farm
rm -rf "$farm_dir"

# If same-path swap, restore original
mv "${source_dir}_orig" "$source_dir"

# Remove Rucio rule (frees LOCALGROUPDISK space)
rucio delete-rule $RULE_ID

# Remove dataset
rucio erase $SCOPE:$dataset_name

# If full integration, revert code changes
git checkout "$BASE_BRANCH" -- .
git checkout "$BASE_BRANCH"
git branch -D lgd-migrate-${dataset_name}
# If stash exists: git stash pop
```

## Key facts (from pilot testing, May 2026)

- RSE names: `BNL-OSG2_LOCALGROUPDISK`, `BNL-OSG2_SCRATCHDISK` (note hyphen/underscore positions)
- LOCALGROUPDISK pnfs mount on SDCC: `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/`
- Files land at: `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<username>/<2-char-hash>/<2-char-hash>/<filename>`
- PFN prefix to strip: `root://dcgftp.usatlas.bnl.gov:1094/`
- Symlink farm files are readable without grid proxy on SDCC nodes
- LOCALGROUPDISK quota requires `/atlas/usatlas` VOMS group membership
- Default quota: 50 TB per user
- `rucio upload` copies files — source is never modified or deleted
- FTS queue wait for user-priority transfers: typically 1–12 hours; actual transfer is minutes
- Same-path swap is the recommended default: no code changes needed
