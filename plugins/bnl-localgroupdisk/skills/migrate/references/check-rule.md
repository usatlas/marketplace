# Monitor a Rucio replication rule (standalone)

Monitor a Rucio replication rule by polling `rucio rule-info` until the state
reaches OK (complete) or STUCK (failed). Use after adding a replication rule to
BNL-OSG2_LOCALGROUPDISK, or to resume monitoring a rule from a previous session.

The main `migrate` workflow runs this automatically (Phase 1, Step 5b). Use this
reference standalone only when resuming an interrupted session, or
troubleshooting. If the rule ID is not provided, ask the user.

## Key Concepts

- **State: OK** — all files replicated to LOCALGROUPDISK. Proceed to PFN
  extraction and symlink farm (`references/build-symlinks.md`).
- **State: REPLICATING** — transfers in progress. Locks field shows
  `OK/REPLICATING/STUCK: X/Y/Z` — X files done, Y transferring, Z failed. X=0,
  Y>0 for >1 hour is normal (FTS queue delay).
- **State: STUCK** — some transfers failed repeatedly. Check the `Error:` field.
  Common causes: source replica expired, RSE unavailable, quota exceeded.
- **Locks** — per-file transfer status. The three numbers are
  OK/REPLICATING/STUCK counts.

## Patterns

First bootstrap the ATLAS environment and Rucio as described in the "Environment
setup" section of the main `SKILL.md` (which defers to the `setupatlas` skill).

### Quick check

```bash
rucio rule-info <RULE_ID> 2>/dev/null \
  | grep -E "State:|Locks|Error|Updated|Name"
```

Replace `<RULE_ID>` with the rule ID argument.

### Long-running monitor

If the rule is still REPLICATING, set up a Monitor to watch for completion:

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
    echo "REPLICATION STUCK"
    exit 1
  fi
  sleep 120
done
```

Use `timeout: 3600000` on the Bash tool call (1 hour). If it times out, re-run.

## Gotchas

- **STUCK does not always mean permanent failure**: FTS can mark transfers stuck
  temporarily. Check the `Error:` field — if it mentions a transient issue
  (e.g., "source busy"), the rule may auto-recover. Report the error text to the
  user rather than assuming the worst.
- **0/N locks for hours is normal**: user-priority FTS transfers are
  deprioritized. Queue waits of 1–12 hours are expected at BNL. Actual data
  transfer once FTS picks it up takes only minutes (~5 min per 100 GB).
- **Error: not None** — always report the full error text to the user.

After replication reaches OK, build the symlink farm
(`references/build-symlinks.md`), or let the main `migrate` workflow continue to
the next phase automatically.
