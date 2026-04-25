---
name: centralpage
description: >-
  Use when searching for ATLAS Monte Carlo or data samples: querying the PMG
  central sample database for MC datasets by process, generator, or campaign,
  looking up cross-sections and filter efficiencies, or identifying which
  centrally produced samples are available for a given physics process.
---

# Central Page

## Overview

The ATLAS Central Page is a tool for finding and querying Monte Carlo and data
samples in the PMG (Physics Modelling Group) central sample database. It helps
physicists locate the correct dataset containers for their analyses by searching
through centrally produced sample catalogs, cross-referencing with AMI for
dataset metadata.

## When to Use

- Searching for MC samples by physics process, generator, or campaign
- Looking up cross-sections, k-factors, and filter efficiencies for MC samples
- Identifying which MC campaigns (mc20, mc21, mc23) have a given process
- Finding the correct dataset container name for a specific signal or background

## Key Concepts

| Concept                | Notes                                                   |
| ---------------------- | ------------------------------------------------------- |
| PMG central database   | Authoritative catalog of centrally produced MC samples   |
| MC campaign            | Production campaign (mc20, mc21, mc23) with fixed config |
| Cross-section database | PMG-maintained xsec, k-factor, filter efficiency values  |
| DSID                   | Dataset ID — unique 6-digit number per MC process config |
| Generator              | Powheg, Sherpa, MadGraph, Pythia, Herwig, etc.           |

## Canonical Patterns

### Setup and launch

```bash
setupATLAS
lsetup centralpage

centralpage                      # interactive mode
centralpage --help              # show options
```

### Search for samples

```bash
# Search by process name
centralpage search "Ztautau"

# Search by generator
centralpage search "Sherpa ttbar"

# Filter by MC campaign
centralpage search "mc23 Powheg Zjets"
```

### Common queries

- Find all MC samples for a specific process (e.g. ttbar, diboson, Zjets)
- Find samples matching a specific generator (Powheg, Sherpa, MadGraph)
- Find samples by MC campaign (mc20, mc21, mc23)
- Look up cross-sections and filter efficiencies for a DSID

### Verify cross-sections

Always cross-check sample cross-sections against the PMG cross-section database
before using them in an analysis. The centralpage tool provides direct access to
these values, but verify against the latest PMG recommendations for your
analysis.

## Gotchas

- **Grid credentials required**: Full sample listing requires valid ATLAS grid
  credentials (`voms-proxy-init --voms atlas`).
- **Campaign coverage varies**: Not all MC campaigns have the same processes
  available — mc23 may lack samples that exist in mc20.
- **Cross-section verification**: Always verify cross-sections against the PMG
  cross-section database; values may be updated between production rounds.
- **Dataset naming conventions change**: Container naming patterns differ across
  MC campaigns — do not hardcode dataset name patterns.
- **All ATLAS energy/momentum values are in MeV**: Cross-sections are in pb, but
  kinematic values follow ATLAS MeV conventions.

## Interop

- **pyAMI**: Use alongside centralpage for detailed dataset metadata queries —
  pyAMI has a dedicated MCP server (`ami-mcp`).
- **Rucio**: Datasets found via centralpage can be located and downloaded with
  Rucio — Rucio has a dedicated MCP server (`rucio-mcp`).
- **atlasopenmagic**: The ATLAS Open Magic MCP server can also search for
  datasets and provides complementary search capabilities.
- **setupATLAS**: `lsetup centralpage` requires a working ALRB environment — see
  the setupatlas skill.

Contact: See PMG infrastructure team

## Docs

https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/central-page
