---
name: managetier3sw
description: >-
  Use when installing, updating, or removing ATLAS software on a local Tier-3
  cluster, laptop, or desktop with manageTier3SW, configuring ATLASLocalRootBase
  for a non-CVMFS site, running local ATLAS software diagnostics, setting up
  local post-user scripts, or troubleshooting Tier-3 ATLAS software
  installations.
---

# manageTier3SW

## Overview

manageTier3SW installs, updates, and removes ATLAS software (ATLASLocalRootBase,
AtlasSetup, PandaClient, ROOT, Rucio, etc.) on laptops, desktops, or Tier-3
clusters where CVMFS is not available. It mirrors the CVMFS software stack into
a local directory managed by a non-privileged account, keeping the environment
identical to what `setupATLAS` provides on lxplus. If CVMFS is available, prefer
mounting `/cvmfs/atlas.cern.ch` directly — no local install is needed.

## When to Use

- Installing ATLAS software locally on a machine without CVMFS
- Updating or removing ATLAS software versions on a Tier-3 site
- Configuring local overrides for ALRB (custom post-setup scripts, local config)
- Running diagnostics to validate a Tier-3 ATLAS software installation
- Troubleshooting missing RPMs, broken Frontier-squid, or stale tool versions

## Key Concepts

**Non-privileged account**: Install under a dedicated service account (e.g.
`atlasadmin`). manageTier3SW only modifies the `atlasadmin` home directory and
`$ATLAS_LOCAL_ROOT_BASE` — no root privileges required for the software itself.

**ATLAS_LOCAL_ROOT_BASE**: The root of the local ATLAS software tree. All tools,
releases, and configuration live under this path. Set this environment variable
before sourcing `atlasLocalSetup.sh`.

**Custom content naming**: Any locally created content (scripts, configs, tool
wrappers) must use names beginning with `local` to avoid conflicts with upstream
updates.

**Automatic cleanup**: The `updateManageTier3SW.sh` cron job auto-removes
obsolete software versions during updates, keeping the installation current
without manual intervention.

## Canonical Patterns

### Initial Installation

Install in a dedicated non-privileged account:

```bash
# As the atlasadmin user
cd /path/to/atlasadmin
# Follow the manageTier3SW installation instructions for your OS
# The installer populates $ATLAS_LOCAL_ROOT_BASE
```

### Keeping Software Up to Date

Schedule `updateManageTier3SW.sh` as a daily cron job to pull new releases and
remove obsolete versions automatically:

```bash
# crontab entry (as atlasadmin)
0 3 * * * /path/to/updateManageTier3SW.sh
```

### Local Configuration Overrides

Create a local config directory to customize ALRB behavior without modifying
upstream files:

```bash
mkdir -p /path/to/localConfig
cp $ATLAS_LOCAL_ROOT_BASE/exampleLocalConfig/* /path/to/localConfig/
export ALRB_localConfigDir=/path/to/localConfig
```

### Post-Setup Scripts

Create site-wide scripts that run after every user's `setupATLAS` call. Place
them in `$ATLAS_LOCAL_ROOT_BASE/config`:

```bash
# $ATLAS_LOCAL_ROOT_BASE/config/localPostUserSetup.sh
# This runs after every setupATLAS invocation on this site
export MY_SITE_VAR="custom_value"
```

Users can bypass post-setup scripts when needed:

```bash
setupATLAS --noLocalPostSetup
```

### Running Diagnostics

Validate the full installation after setup or updates:

```bash
setupATLAS
diagnostics                                # interactive diagnostics menu
checkOS                                    # verify required RPMs are installed
db-fnget                                   # test Frontier-squid connectivity
toolTest -m validate all -T                # validate all installed tools
```

### Checking Installation Logs

Review what was installed and when:

```bash
ls $ATLAS_LOCAL_ROOT_BASE/logDir/installed
```

## Gotchas

- **CVMFS preferred**: If `/cvmfs/atlas.cern.ch` is mountable, use it directly
  instead of manageTier3SW — CVMFS is self-updating and requires no local
  maintenance.
- **Custom names must start with `local`**: Any user-created files or scripts in
  the managed tree must be prefixed with `local` to prevent upstream updates
  from overwriting them.
- **Cron job is essential**: Without `updateManageTier3SW.sh` running regularly,
  the installation drifts from the current CVMFS state and accumulates obsolete
  versions.
- **RPM dependencies**: `checkOS` identifies missing system-level RPMs that
  ATLAS software requires. Install these with the system package manager
  (requires root privileges, unlike the ATLAS software itself).
- **Frontier-squid**: `db-fnget` tests the local Frontier-squid proxy used for
  conditions database access. A failed test means conditions data lookups will
  fall back to direct connections or fail entirely.
- **All ATLAS energy/momentum values are in MeV**.

## Interop

- **setupATLAS**: Once manageTier3SW is installed, `setupATLAS` works
  identically to CVMFS-based sites — see the setupatlas skill.
- **CVMFS**: Sites with CVMFS access do not need manageTier3SW; mount
  `/cvmfs/atlas.cern.ch` and source `atlasLocalSetup.sh` directly.

| Domain                   | Contact                          |
| ------------------------ | -------------------------------- |
| Tier-3 software install  | atlas-adc-tier3-managers@cern.ch |
| ATLAS software (general) | hn-atlas-offlineSWHelp@cern.ch   |

## Docs

https://twiki.atlas-canada.ca/bin/view/AtlasCanada/ManageTier3SW
