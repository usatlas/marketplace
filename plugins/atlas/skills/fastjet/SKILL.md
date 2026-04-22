---
name: fastjet
description: >-
    Use when running jet clustering in Python with fastjet or pyjet: calling
    anti-kt or Cambridge/Aachen algorithms on particle four-vectors, accessing
    jet constituents, computing jet substructure variables (tau_N, softdrop),
    or clustering jets from generator-level events read with pyhepmc or pylhe.
---

# fastjet

## Overview

fastjet is the standard jet-finding library in HEP. The Python bindings (`fastjet` PyPI package, also known as `pyjet` in older versions) expose the anti-kt, Cambridge/Aachen, and kt clustering algorithms. In ATLAS physics analyses the main use is truth-level jet clustering for generator studies or jet substructure calculations on particle-level events.

## When to Use

- Clustering particle-level or parton-level events from a Monte Carlo generator
- Computing jet substructure variables (N-subjettiness, soft drop) for truth jets
- Validating detector-level jets against truth clustering
- Grooming jets for boosted object analyses

## Key Concepts

| Concept | Notes |
|---|---|
| `fastjet.ClusterSequence` | Core clustering object; constructed from PseudoJets + JetDefinition |
| `fastjet.PseudoJet` | Four-vector container (px, py, pz, E) |
| `fastjet.JetDefinition` | Algorithm + R parameter, e.g. `anti_kt` with R=0.4 |
| `fastjet.ClusterSequenceArea` | Adds jet area computation (needed for pileup subtraction) |
| `fastjet.Selector` | Filter jets by pT, eta, etc. |
| Jet constituents | `jet.constituents()` returns list of PseudoJets |
| User index | `pseudo_jet.set_user_index(i)` links back to the original particle |

## Canonical Patterns

### Cluster jets from a list of particles

```python
import fastjet as fj
import numpy as np

# Four-vectors: (px, py, pz, E) per particle
px = np.array([...])
py = np.array([...])
pz = np.array([...])
E  = np.array([...])

pseudojets = [fj.PseudoJet(px[i], py[i], pz[i], E[i]) for i in range(len(px))]

jet_def = fj.JetDefinition(fj.antikt_algorithm, 0.4)
cs = fj.ClusterSequence(pseudojets, jet_def)

jets = fj.sorted_by_pt(cs.inclusive_jets(ptmin=25.0))   # pT > 25 GeV

for j in jets:
    print(f"pT={j.pt():.1f} GeV  eta={j.eta():.2f}  phi={j.phi():.2f}")
    print(f"  {len(j.constituents())} constituents")
```

### From awkward arrays (vectorized construction)

```python
import fastjet as fj, awkward as ak, vector
vector.register_awkward()

# particles is an ak.Array with fields px, py, pz, E
def cluster_event(particles):
    pjs = [fj.PseudoJet(float(p.px), float(p.py), float(p.pz), float(p.E))
           for p in particles]
    cs = fj.ClusterSequence(pjs, fj.JetDefinition(fj.antikt_algorithm, 0.4))
    return fj.sorted_by_pt(cs.inclusive_jets(ptmin=20.0))
```

### Jet substructure: N-subjettiness

```python
import fastjet as fj

# requires fastjet contrib (fjcontrib)
from fastjet import contrib

tau_calc = contrib.Nsubjettiness(1, contrib.OnePass_KT_Axes(),
                                  contrib.UnnormalizedMeasure(beta=1.0))

for jet in jets:
    tau1 = tau_calc(jet)
```

### Soft drop grooming

```python
from fastjet import contrib

sd = contrib.SoftDrop(beta=0.0, zcut=0.1, R=1.0)
groomed_jets = [sd(j) for j in jets]
```

### Jet area (for pileup)

```python
ghost_area = fj.AreaDefinition(fj.active_area, fj.GhostedAreaSpec(5.0))
cs_area = fj.ClusterSequenceArea(pseudojets, jet_def, ghost_area)
for j in cs_area.inclusive_jets(ptmin=25.0):
    print(f"area = {j.area():.3f}")
```

## Gotchas

- **Units**: fastjet has no built-in unit system — ensure all four-vectors use the same units (usually GeV).
- **`phi()` range**: fastjet returns phi in `[0, 2π)`; some downstream code expects `(-π, π]`. Use `fj.PseudoJet.phi_std()` or subtract `2π` if needed.
- **pyjet vs fastjet**: the older `pyjet` package uses `numpy` structured arrays; the newer `fastjet` package (from Scikit-HEP) uses `PseudoJet` objects and is the recommended path.
- **fjcontrib availability**: substructure tools (`Nsubjettiness`, `SoftDrop`) require the `fastjet` package built with contrib support, or a separate `fjcontrib` install.
- **No automatic batching**: fastjet processes one event at a time; loop over events explicitly.

## Interop

- **pyhepmc**: Read HepMC3 events, extract final-state particles, build PseudoJets.
- **pylhe**: Read LHE parton-level events for parton-jet matching studies.
- **vector / awkward**: Convert awkward four-vector arrays to PseudoJets event-by-event.

## Docs

https://fastjet.fr/  
Python bindings: https://scikit-hep.org/fastjet/
