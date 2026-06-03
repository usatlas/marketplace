---
name: bnl-localgroupdisk-check-rule
description: >-
  Use when monitoring a Rucio replication rule until it completes (state OK) or
  gets stuck after adding a rule to BNL-OSG2_LOCALGROUPDISK.
---

## Overview

Monitor a Rucio replication rule by polling `rucio rule-info` until the
state reaches OK (complete) or STUCK (failed). Use after adding a
replication rule to BNL-OSG2_LOCALGROUPDISK, or to resume monitoring a
rule from a previous session.

If the rule ID is not provided, ask the user.

## When to Use

- After `rucio add-rule` returns a rule ID and you need to wait for
  replication to finish
- When a previous migration session was interrupted during replication and
  you need to check whether it completed
- Inside `/bnl-localgroupdisk:migrate`, this logic runs automatically —
  call standalone only when resuming or troubleshooting

## Key Concepts

- **State: OK** — all files replicated to LOCALGROUPDISK. Proceed to PFN
  extraction and symlink farm.
- **State: REPLICATING** — transfers in progress. Locks field shows
  `OK/REPLICATING/STUCK: X/Y/Z` — X files done, Y transferring, Z
  failed. X=0, Y>0 for >1 hour is normal (FTS queue delay).
- **State: STUCK** — some transfers failed repeatedly. Check the `Error:`
  field. Common causes: source replica expired, RSE unavailable, quota
  exceeded.
- **Locks** — per-file transfer status. The three numbers are
  OK/REPLICATING/STUCK counts.

## Canonical Patterns

### Quick check

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
rucio rule-info <RULE_ID> 2>/dev/null \
  | grep -E "State:|Locks|Error|Updated|Name"
```

Replace `<RULE_ID>` with the rule ID argument.

### Long-running monitor

If the rule is still REPLICATING, set up a Monitor to watch for
completion:

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
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
    echo "REPLICATION STUCK"
    exit 1
  fi
  sleep 120
done
```

Use `timeout: 3600000` on the Bash tool call (1 hour). If it times out,
re-run.

## Gotchas

- **STUCK does not always mean permanent failure**: FTS can mark transfers
  stuck temporarily. Check the `Error:` field — if it mentions a transient
  issue (e.g., "source busy"), the rule may auto-recover. Report the error
  text to the user rather than assuming the worst.
- **0/N locks for hours is normal**: user-priority FTS transfers are
  deprioritized. Queue waits of 1–12 hours are expected at BNL. Actual
  data transfer once FTS picks it up takes only minutes (~5 min per
  100 GB).
- **Error: not None** — always report the full error text to the user.

## Interop

- FTS queue wait for user-priority transfers: typically 1–12 hours at
  BNL; actual transfer is minutes per 100 GB.
- After replication reaches OK, use
  `/bnl-localgroupdisk:build-symlinks` to create a symlink farm, or let
  `/bnl-localgroupdisk:migrate` continue to the next phase automatically.

## Docs

- [bnl-localgroupdisk plugin](https://github.com/FlamyFlame/claude-bnl-localgroupdisk)
- [BNL SDCC storage documentation](https://usatlas.github.io/af-docs/bnl/storage/)
