---
name: pyhepmc
description: >-
  Use when reading or writing HepMC3 event records in Python: opening HepMC2 or
  HepMC3 ASCII files from a Monte Carlo generator, iterating over events,
  accessing truth particles and vertices, filtering by status code or PDG ID, or
  writing modified events back to a HepMC file.
---

# pyhepmc

## Overview

pyhepmc provides Python bindings for the HepMC3 event record library. It reads
HepMC2 and HepMC3 ASCII files produced by Monte Carlo generators (Pythia8,
Sherpa, MadGraph, EvtGen) and exposes particles, vertices, and event metadata as
Python objects. It is the standard tool for truth-level generator studies in the
Scikit-HEP ecosystem.

## When to Use

- Reading generator-level truth events for particle-level analysis
- Extracting final-state particles for truth jet clustering with fastjet
- Inspecting decay chains or particle status codes
- Writing test events or modified events for generator validation

## Key Concepts

| Concept       | Notes                                           |
| ------------- | ----------------------------------------------- |
| `GenEvent`    | One event: particles + vertices + weights       |
| `GenParticle` | Four-vector + PDG ID + status code              |
| Status 1      | Final-state (stable) particles                  |
| Status 2      | Decayed particles (intermediate)                |
| Status 3      | Parton-level / documentation particles          |
| `GenVertex`   | Connects incoming and outgoing particles        |
| Weights       | Named weight dictionary (e.g. scale variations) |

## Canonical Patterns

### Read a HepMC3 file

```python
import pyhepmc

with pyhepmc.open("events.hepmc3") as f:
    for event in f:
        particles = event.particles
        vertices  = event.vertices
        weights   = event.weight_names   # list of weight names
```

### Filter final-state particles

```python
with pyhepmc.open("events.hepmc3") as f:
    for event in f:
        final_state = [p for p in event.particles if p.status == 1]
        # four-vector: p.momentum.px, .py, .pz, .e (in GeV)
        for p in final_state:
            pt = (p.momentum.px**2 + p.momentum.py**2)**0.5
            print(p.pid, pt)
```

### Identify particles by PDG ID

```python
from particle import Particle
import pyhepmc

with pyhepmc.open("events.hepmc3") as f:
    for event in f:
        b_hadrons = [p for p in event.particles
                     if abs(p.pid) in (511, 521, 531, 5122)]  # B0, B+, Bs, Lb
```

### Extract four-vectors for fastjet clustering

```python
import pyhepmc, fastjet as fj

with pyhepmc.open("events.hepmc3") as f:
    for event in f:
        pjs = [
            fj.PseudoJet(p.momentum.px, p.momentum.py, p.momentum.pz, p.momentum.e)
            for p in event.particles if p.status == 1 and abs(p.pid) != 12
            # exclude neutrinos (12, 14, 16) from clustering
        ]
        cs = fj.ClusterSequence(pjs, fj.JetDefinition(fj.antikt_algorithm, 0.4))
        jets = fj.sorted_by_pt(cs.inclusive_jets(ptmin=20.0))
```

### Write HepMC3 events

```python
with pyhepmc.open("output.hepmc3", "w") as out:
    with pyhepmc.open("input.hepmc3") as f:
        for event in f:
            # modify event here
            out.write(event)
```

### Access named weights (scale / PDF variations)

```python
with pyhepmc.open("events.hepmc3") as f:
    for event in f:
        w = dict(zip(event.weight_names, event.weights))
        nominal = w.get("Default", 1.0)
        mur_up  = w.get("MUR2_MUF1", 1.0)
```

## Gotchas

- **HepMC momentum units are GeV** (not MeV): pyhepmc follows HepMC3
  conventions, so `p.momentum.e` is in GeV. This is opposite to ATLAS NTuple
  branches, which are in MeV.
- **Status code conventions vary by generator**: status=1 for final-state is
  standard; beyond that, Pythia8 and Sherpa use generator-specific codes.
- **Neutrinos pass isolation cuts**: remember to exclude neutrino PDG IDs (12,
  14, 16) from visible-particle sums and jet clustering.
- **HepMC2 vs HepMC3**: `pyhepmc.open` auto-detects the format. HepMC2 files
  have an `HepMC::IO_GenEvent` header; HepMC3 files start with `HepMC::Version`.

## Interop

- **fastjet**: Extract final-state particles from `GenEvent`, build PseudoJets,
  cluster.
- **particle**: Identify PDG IDs (`p.pid`) with `Particle.from_pdgid(p.pid)`.
- **pylhe**: For parton-level LHE files; pyhepmc handles showered/hadronized
  events.
- **awkward**: Convert final-state particle lists to awkward arrays for
  vectorized analysis.

## Docs

https://scikit-hep.org/pyhepmc/
