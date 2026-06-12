# Pre-flight checks (standalone)

Run all prerequisite checks before migrating files to BNL-OSG2_LOCALGROUPDISK.
Reports a summary table with OK/WARN/FAIL status for each check. Stops the
migration if any check is FAIL.

The main `migrate` workflow runs these automatically. Use this reference
standalone only when troubleshooting a previous failure, or verifying the
environment ahead of time (e.g. after requesting `/atlas/usatlas` VOMS group
membership, to confirm it took effect).

## Key Concepts

- **Rucio scope**: `user.<account>` — derived from the account name returned by
  `rucio whoami`. Used as prefix for all DIDs.
- **VOMS group `/atlas/usatlas`**: required for LOCALGROUPDISK quota allocation.
  Without it, `rucio add-rule` to LGD will fail with "insufficient quota."
- **RSE naming**: `BNL-OSG2_LOCALGROUPDISK` and `BNL-OSG2_SCRATCHDISK` — note
  exact hyphen and underscore positions.
- **pnfs mount path**: `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/` on SDCC (not
  `atlaslocalgroupdisk`).

## Checks

First bootstrap the ATLAS environment and Rucio as described in the "Environment
setup" section of the main `SKILL.md` (which defers to the `setupatlas` skill).
Then run all 5 checks and report a summary table.

### 1. Rucio identity

```bash
echo "=== RUCIO IDENTITY ==="
rucio whoami 2>/dev/null
```

Record the `account` name — this is the Rucio scope prefix (e.g.,
`user.<account>`).

### 2. Grid proxy

```bash
voms-proxy-info --all 2>&1
```

Check:

- Proxy exists and has >2 hours remaining (>24h recommended for large uploads)
- VOMS attributes include `/atlas/usatlas` — **required for LOCALGROUPDISK
  quota**
- If missing `/atlas/usatlas`: user must request membership via ATLAS IAM
  (`https://atlas-auth.cern.ch/`), then
  `voms-proxy-init -voms atlas:/atlas/usatlas`

### 3. RSE names

```bash
rucio list-rses 2>/dev/null | grep -i "BNL-OSG2"
```

Expected: `BNL-OSG2_LOCALGROUPDISK` and `BNL-OSG2_SCRATCHDISK`.

### 4. Quota

Use the account name from Check 1:

```bash
ACCOUNT=$(rucio whoami 2>/dev/null | grep "account" | awk '{print $2}')
rucio list-account-limits $ACCOUNT 2>/dev/null \
  | grep -E "BNL-OSG2_(LOCALGROUPDISK|SCRATCHDISK)"
```

- LOCALGROUPDISK should show a limit (default 50 TB). If missing, the user is
  not in `/atlas/usatlas` VOMS group.
- SCRATCHDISK is the upload staging area. Check available space with
  `rucio list-account-usage $ACCOUNT 2>/dev/null | grep BNL-OSG2_SCRATCHDISK`.

### 5. pnfs mount

```bash
ls /pnfs/usatlas.bnl.gov/LOCALGROUPDISK/ 2>&1 | head -3
```

The LOCALGROUPDISK pnfs mount must be accessible. On BNL SDCC nodes it is at
`/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/` (not `atlaslocalgroupdisk`).

User files land under
`/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/rucio/user/<account>/`.

### Summary format

Report results as:

| Check             | Status       | Details                     |
| ----------------- | ------------ | --------------------------- |
| Rucio account     | OK/FAIL      | account name                |
| Grid proxy        | OK/WARN/FAIL | time remaining, VOMS groups |
| RSE names         | OK/FAIL      | confirmed names             |
| LGD quota         | OK/FAIL      | limit                       |
| Scratchdisk quota | OK/FAIL      | limit, used                 |
| pnfs mount        | OK/FAIL      | path                        |

If any check is FAIL, explain what the user needs to do before proceeding.

## Gotchas

- **NO LGD QUOTA**: the most common pre-flight failure. The user needs
  `/atlas/usatlas` VOMS group membership — request at
  `https://atlas-auth.cern.ch/`, wait for approval, then re-init proxy with
  `voms-proxy-init -voms atlas:/atlas/usatlas -valid 96:00`.
- **Missing VOMS attributes**: even if the user has the group membership,
  `voms-proxy-init -voms atlas` (without `:/atlas/usatlas`) may not include the
  group. Use the explicit form.
- **Proxy expiry during long uploads**: use `-valid 96:00` since FTS replication
  can take up to 12 hours.
- **pnfs path**: the mount on SDCC is `/pnfs/usatlas.bnl.gov/LOCALGROUPDISK/`,
  not `/pnfs/usatlas.bnl.gov/atlaslocalgroupdisk/`.
