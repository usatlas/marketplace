---
name: eiclient
description: >-
  Use when working with the ATLAS Event Index: looking up which dataset contains
  a specific run/event number, picking events from a list of run/event pairs,
  tracing event provenance through processing stages (RAW to AOD to DAOD), or
  listing all events in a dataset.
---

# Event Index Client

## Overview

The Event Index (EI) client provides command-line access to the ATLAS Event
Index — a catalog that tracks every event processed by ATLAS. It enables
event-level lookup, event picking, and provenance queries across all processing
stages, from RAW through ESD, AOD, and DAOD.

## When to Use

- Finding which dataset contains a specific run/event number
- Picking a list of events and identifying all datasets that contain them
- Tracing an event through the full processing chain (provenance)
- Listing all events in a given dataset
- Preparing event lists for grid-based event picking with pathena

## Key Concepts

| Concept        | Notes                                                        |
| -------------- | ------------------------------------------------------------ |
| Event Index    | Central catalog of all ATLAS events across processing stages |
| Event lookup   | Find datasets containing a specific run + event number       |
| Event picking  | Given a list of run/event pairs, find matching datasets      |
| Provenance     | Trace an event through RAW → ESD → AOD → DAOD chain          |
| Run/event pair | Events are uniquely identified by (run number, event number) |

## Canonical Patterns

The `eiclient` package installs three commands — `event-lookup`, `event-list`,
and `dataset-list`. Run any with `-h` for the full option list.

### Setup

```bash
setupATLAS
lsetup eiclient
voms-proxy-init -voms atlas    # a valid grid proxy is required
```

### Event lookup — find the files/datasets containing an event

Events are given as `<run>:<event>` (or `<run> <event>`, quoted). The search
spans the indexed datasets and their provenance, returning the GUIDs of the
files that hold each event:

```bash
event-lookup 280862:659846
event-lookup 280862:659846 280862:123456      # several events
```

Narrow the search by dataset attributes:

```bash
event-lookup -d AOD -p data18_13TeV 280862:659846
```

### Event picking — many run/event pairs from a file

With no event arguments, `event-lookup` reads pairs from `--file` (or stdin),
one `<run> <event>` per line:

```bash
event-lookup -d AOD -F events.txt
```

`events.txt`:

```text
154514 21179
154514 29736
154558 448080
```

Pick the output format with `-c {plain,name,short,pretty,json}` and write to a
file with `-o`:

```bash
event-lookup -c json -o guids.json -F events.txt
```

### List events in a dataset

`event-list` lists metadata for — or counts — the events in one or more
datasets:

```bash
event-list data18_13TeV.00123456.physics_Main.merge.AOD.f1234_m5678
event-list -N <dataset>                       # -N: count only
event-list -B <lumiblock> -l 100 <dataset>    # filter by LumiBlock, limit rows
```

### List datasets for a run

`dataset-list` shows the indexed datasets for one or more runs:

```bash
dataset-list -d AOD -p data18_13TeV 280862
```

### Provenance

`event-lookup` already returns GUIDs from provenance (parent) datasets as well
as the searched datasets. Narrow the result with `-D/--guid-data-type` (e.g.
`-D RAW`) together with `-d/--data-type` to follow the RAW → AOD → DAOD chain.

## Gotchas

- **Grid credentials required**: A valid VOMS proxy is needed
  (`voms-proxy-init --voms atlas`).
- **Both run and event number required**: Event numbering is per-run, so always
  specify both run number and event number together.
- **Large event lists take time**: Processing thousands of run/event pairs may
  be slow — batch queries when possible.
- **Indexing lag**: Not all processing steps are indexed immediately after
  production — recently produced datasets may have incomplete provenance.
- **All ATLAS energy/momentum values are in MeV**: The Event Index itself stores
  metadata, not kinematics, but downstream datasets follow ATLAS conventions.

## Interop

- **panda/pathena**: Event lists from EI can be fed to pathena's
  `--eventPickEvtList` option for grid-based event picking.
- **Rucio**: Use Rucio to locate and download datasets identified by EI queries.
- **pyAMI**: Complements EI — pyAMI provides dataset-level metadata (tags,
  cross-sections), while EI provides event-level information.
- **setupATLAS**: `lsetup eiclient` requires a working ALRB environment — see
  the setupatlas skill.

Contact: See ATLAS Computing documentation

## Docs

https://twiki.cern.ch/twiki/bin/view/AtlasComputing/EventIndex

Tutorial: https://twiki.cern.ch/twiki/bin/view/AtlasComputing/EventIndexPicking
