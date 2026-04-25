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

### Setup

```bash
setupATLAS
lsetup eiclient
```

### Event lookup

Find which datasets contain a specific event:

```bash
ei_client GetEvent --run 123456 --event 789012
```

### Event picking

Given a file with run/event pairs, find datasets containing those events:

```bash
ei_client EventPicking --eventList events.txt --dataType AOD
```

Event list file format (one run/event pair per line):

```text
154514 21179
154514 29736
154558 448080
```

### List events in a dataset

```bash
ei_client GetEvents \
  --dataset data18_13TeV.00123456.physics_Main.merge.AOD.f1234_m5678
```

### Provenance query

Trace an event through all processing stages:

```bash
ei_client GetProvenance --run 123456 --event 789012
```

This returns the chain of datasets the event passed through, from RAW to the
final derivation.

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
- **Rucio**: Use Rucio (or the `rucio-mcp` server) to locate and download
  datasets identified by EI queries.
- **pyAMI**: Complements EI — pyAMI provides dataset-level metadata (tags,
  cross-sections), while EI provides event-level information.
- **setupATLAS**: `lsetup eiclient` requires a working ALRB environment — see
  the setupatlas skill.

Contact: See ATLAS Computing documentation

## Docs

https://twiki.cern.ch/twiki/bin/view/AtlasComputing/EventIndex

Tutorial: https://twiki.cern.ch/twiki/bin/view/AtlasComputing/EventIndexPicking
