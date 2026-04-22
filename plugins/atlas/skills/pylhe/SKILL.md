---
name: pylhe
description: >-
  Use when reading Les Houches Event (LHE) files in Python: iterating over
  parton-level events from MadGraph or other generators, extracting initial- and
  final-state parton four-vectors, reading event weights, or cross- checking
  hard-process kinematics before showering.
---

# pylhe

## Overview

pylhe reads Les Houches Event (LHE) files — the standard ASCII format for
parton-level events produced by matrix-element generators such as
MadGraph5_aMC@NLO, Sherpa, and Powheg. It exposes events, particles, and header
metadata as Python objects and integrates with awkward for vectorized
processing. It is used for parton-level studies, cross-section validation, and
checking generator weights before showering.

## When to Use

- Inspecting parton-level events from a matrix-element generator before
  showering
- Computing parton-level kinematic distributions to compare with NLO
  cross-sections
- Reading event weights (scale and PDF variations) from LHE reweighting blocks
- Checking that the generator configuration (process, cuts) matches expectations

## Key Concepts

| Concept                     | Notes                                         |
| --------------------------- | --------------------------------------------- |
| `pylhe.read_lhe(path)`      | Iterator over `LHEEvent` objects              |
| `LHEEvent.particles`        | List of `LHEParticle` objects                 |
| `LHEParticle.status`        | -1 = incoming, 1 = outgoing, 2 = intermediate |
| `LHEParticle.id`            | PDG ID                                        |
| `LHEParticle.px/py/pz/e/m`  | Four-momentum + mass (GeV)                    |
| `pylhe.read_lhe_init(path)` | Reads header metadata (process info, xsec)    |
| `pylhe.to_awkward(events)`  | Converts event iterator to awkward array      |

## Canonical Patterns

### Iterate over events

```python
import pylhe

for event in pylhe.read_lhe("events.lhe.gz"):   # .gz supported
    outgoing = [p for p in event.particles if p.status == 1]
    for p in outgoing:
        pt = (p.px**2 + p.py**2)**0.5
        print(p.id, pt, p.e)
```

### Read header (cross-section, generator metadata)

```python
init = pylhe.read_lhe_init("events.lhe.gz")
print(init["initInfo"])   # dict with beam energies, PDF IDs, etc.
for proc in init["procInfo"]:
    print(proc["xSection"], proc["xSecErr"])   # in pb
```

### Convert to awkward for vectorized analysis

```python
import pylhe, awkward as ak

events = pylhe.to_awkward(pylhe.read_lhe("events.lhe.gz"))

# events["particles"] is a jagged array
outgoing = events["particles"][events["particles", "status"] == 1]
pt = (outgoing["px"]**2 + outgoing["py"]**2)**0.5
```

### Parton-level invariant mass

```python
import pylhe, numpy as np

masses = []
for event in pylhe.read_lhe("events.lhe.gz"):
    outgoing = [p for p in event.particles if p.status == 1]
    e   = sum(p.e  for p in outgoing)
    px  = sum(p.px for p in outgoing)
    py  = sum(p.py for p in outgoing)
    pz  = sum(p.pz for p in outgoing)
    m2  = e**2 - px**2 - py**2 - pz**2
    masses.append(m2**0.5 if m2 > 0 else 0.0)
```

## Gotchas

- **LHE units are GeV** (not MeV): consistent with HepMC3 and fastjet, but
  opposite to ATLAS NTuples.
- **Compressed files**: `.lhe.gz` is supported; plain `.lhe` and `.lhe.gz` are
  auto-detected.
- **LHE does not contain shower/hadronization**: particles in LHE are
  parton-level — no hadrons, no pile-up.
- **Reweighting blocks (rwgt)**: MadGraph NLO LHE files contain reweighting
  blocks for scale/PDF variations; `pylhe` exposes these in `event.reweight`.

## Interop

- **particle**: Identify parton PDG IDs with `Particle.from_pdgid(p.id)`.
- **pyhepmc**: pylhe handles pre-shower parton-level events; pyhepmc handles
  post-shower truth records.
- **fastjet**: After extracting parton four-vectors, build PseudoJets for
  parton-jet matching studies.

## Docs

https://scikit-hep.org/pylhe/
