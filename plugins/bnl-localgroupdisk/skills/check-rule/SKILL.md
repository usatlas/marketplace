---
description: >
  Monitor a Rucio replication rule until it completes (state OK) or gets stuck.
  Use after adding a replication rule to BNL-OSG2_LOCALGROUPDISK.
disable-model-invocation: false
arguments: [rule_id]
argument-hint: "<rule_id>"
allowed-tools: Bash
---

# Check Rucio replication rule status

Monitor rule `$rule_id` until replication completes.

If `$rule_id` is not provided, ask the user.

## Quick check

Substitute the rule ID from the argument into this command:

```bash
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh >/dev/null 2>&1
lsetup rucio >/dev/null 2>&1
rucio rule-info <RULE_ID> 2>/dev/null | grep -E "State:|Locks|Error|Updated|Name"
```

Replace `<RULE_ID>` with the `$rule_id` argument value.

## Interpreting the output

- **State: OK** — replication complete. All files are on LOCALGROUPDISK. Proceed
  to PFN extraction and symlink farm.
- **State: REPLICATING, Locks OK/REPLICATING/STUCK: X/Y/0** — transfers in
  progress. X files done, Y still transferring. If Y>0 and X=0 for >1 hour,
  the FTS queue is just slow (normal for user-priority transfers).
- **State: STUCK** — some transfers failed repeatedly. Check `Error:` field.
  Common causes: source replica expired, RSE unavailable, quota exceeded.
- **Error: not None** — report the error text to the user.

## Long-running monitor

If the rule is still REPLICATING, set up a Monitor to watch for completion.
Substitute the `$rule_id` argument value for `<RULE_ID>` below:

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

The script uses `$rule_id` from the skill argument. Use `timeout: 3600000` on the Bash tool call (1 hour). If it times out, re-run. FTS queue waits
of 1–12 hours are normal for user transfers at BNL.
