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

| Concept                | Notes                                                    |
| ---------------------- | -------------------------------------------------------- |
| PMG central database   | Authoritative catalog of centrally produced MC samples   |
| MC campaign            | Production campaign (mc20, mc21, mc23) with fixed config |
| Cross-section database | PMG-maintained xsec, k-factor, filter efficiency values  |
| DSID                   | Dataset ID — unique 6-digit number per MC process config |
| Generator              | Powheg, Sherpa, MadGraph, Pythia, Herwig, etc.           |

## Canonical Patterns

The Central Page organises samples under PMG **hashtags** arranged in levels
(`PMGL1`–`PMGL4`; level 3 = "Baseline"). The `centralpage` command navigates
those levels positionally — there is **no `search` subcommand**.

### Setup

```bash
setupATLAS
lsetup centralpage
voms-proxy-init --voms atlas     # listing/querying requires a valid grid proxy
centralpage --help
```

### List available hashtags

A scope is required (`centralpage -l` alone errors with "Scope required"):

```bash
centralpage -s <scope> -l           # list hashtags for the scope
centralpage -s <scope> -P 3 -l      # only the level-3 (Baseline) hashtags
```

### Browse samples by hashtag level

Pass hashtags positionally as `L1 L2 L3 L4` to drill down to the samples:

```bash
centralpage -s <scope> <L1> <L2> <L3> <L4>
```

Add detail to the output:

- `-m` / `--metadata` — also print dataset metadata (cross-section, filter eff.)
- `-a` / `--aod` — also print AODs (standard tags) for each sample
- `-p` / `--phys` — also print DAOD_PHYS containers
- `-L` / `--physlite` — also print DAOD_PHYSLITE containers
- `-f <fmt>` / `--outformat` — restrict to a single output format
- `-t` / `--table` — emit a LaTeX table

### Reverse lookup — find the hashtags for a known dataset

```bash
centralpage -d <dataset_name>
```

### Verify cross-sections

The metadata shown with `-m` comes from the PMG database, but always re-check
cross-sections, k-factors, and filter efficiencies against the latest PMG
recommendations before using them in an analysis.

## Gotchas

- **Hashtag levels, not free text**: the CLI navigates PMG hashtags positionally
  (`L1 L2 L3 L4`) or by `-d <dataset>`; there is no free-text `search` command.
  Use `-s <scope> -l` to discover the valid hashtags first.
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

- **ami-mcp**: The AMI MCP server (`ami-mcp`) provides LLM-friendly access to
  the same PMG cross-section database and dataset metadata that centralpage
  queries. Prefer `ami-mcp` for programmatic lookups of cross-sections,
  k-factors, filter efficiencies, and dataset tags within a Claude session — it
  returns structured results without requiring `lsetup`. Requires `~/.globus`
  credentials and a valid VOMS proxy (`voms-proxy-init --voms atlas`).
- **Rucio**: Datasets found via centralpage can be located and downloaded with
  Rucio — Rucio has a dedicated MCP server (`rucio-mcp`).
- **atlasopenmagic**: The ATLAS Open Magic MCP server can also search for
  datasets and provides complementary search capabilities.
- **setupATLAS**: `lsetup centralpage` requires a working ALRB environment — see
  the setupatlas skill.

Contact: See PMG infrastructure team

## Docs

https://gitlab.cern.ch/atlas-physics/pmg/infrastructure/central-page
