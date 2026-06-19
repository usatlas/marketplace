---
name: atlantis
description: >-
  Use when visualizing ATLAS detector events with the Atlantis event display:
  launching the Atlantis GUI, opening JiveXML event files, producing JiveXML
  output from Athena reconstruction, or troubleshooting Java runtime issues in
  containerized environments.
---

# Atlantis

## Overview

Atlantis is the ATLAS event display — a Java-based graphical tool for
visualizing detector events in 2D projections. It reads JiveXML files produced
by the Athena JiveXML algorithm and provides interactive exploration of tracks,
calorimeter deposits, muon hits, and jets across multiple detector views.

## When to Use

- Visualizing reconstructed ATLAS events interactively
- Inspecting individual tracks, calorimeter clusters, or muon segments in 2D
  projections
- Producing event display images for talks, papers, or analysis documentation
- Debugging reconstruction output by examining event geometry

## Key Concepts

| Concept          | Notes                                                       |
| ---------------- | ----------------------------------------------------------- |
| JiveXML          | XML format for event display data, produced by Athena       |
| Y-X projection   | Transverse view (beam axis perpendicular to screen)         |
| R-Z projection   | Longitudinal view (beam axis horizontal)                    |
| phi-eta view     | Unrolled detector view in pseudorapidity vs azimuthal angle |
| Interactive cuts | Apply pT, eta, or object-type filters directly in the GUI   |

## Canonical Patterns

### Setup and launch

```bash
setupATLAS
lsetup atlantis

atlantis                         # launch GUI
atlantis file.xml               # open specific JiveXML event file
atlantis --file file.xml        # alternative syntax
```

### Producing JiveXML files from Athena

Add the JiveXML algorithm to an Athena job to write event display data:

```python
from AthenaCommon.AlgSequence import AlgSequence
topSequence = AlgSequence()
from JiveXML.JiveXMLConf import JiveXML__AlgoJiveXML
topSequence += JiveXML__AlgoJiveXML()
```

This writes one `.xml` file per event in the run directory. Control output with
algorithm properties:

```python
jivexml = JiveXML__AlgoJiveXML()
jivexml.AtlasRelease = "24.0.0"
jivexml.WriteToFile = True
jivexml.OnlineMode = False
topSequence += jivexml
```

### Working with the GUI

- **Navigate events**: Use the event browser toolbar to step through events in a
  JiveXML file or directory
- **Select objects**: Click on tracks or clusters to inspect properties (pT,
  eta, phi, charge)
- **Apply cuts**: Use the cut panel to filter objects by pT threshold, eta
  range, or object type
- **Export images**: File → Save Canvas to export the current view as PNG or EPS

## Gotchas

- **Java runtime required**: Atlantis is Java-based. Ensure a JRE is available
  in the environment (`java -version` to check).
- **Singularity/Apptainer issues**: Known Java display problems when running
  inside containers — set `DISPLAY` correctly or use VNC/X11 forwarding.
- **Large XML files**: Complex events with many tracks and clusters produce
  large JiveXML files. Limit output to events of interest in Athena.
- **All ATLAS energy/momentum values are in MeV**: Values displayed in the GUI
  follow ATLAS conventions.
- **Custom objects**: JiveXML output may need specific Athena configuration to
  include non-standard reconstruction objects.

## Interop

- **setupATLAS**: `lsetup atlantis` requires a working ALRB environment — see
  the setupatlas skill.
- **Athena**: JiveXML files are produced by Athena reconstruction jobs; the
  JiveXML algorithm must be added to the job sequence.

Contact: hn-atlas-AtlantisDisplay@cern.ch

## Docs

https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/Atlantis

Additional info: http://atlantis.web.cern.ch
