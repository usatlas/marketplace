---
name: fastjet
description: >-
  Use when running jet clustering in Python with the Scikit-HEP fastjet package
  (or migrating from the deprecated pyjet): calling anti-kt or Cambridge/Aachen
  algorithms on particle four-vectors, accessing jet constituents, computing jet
  substructure variables (N-subjettiness, soft drop), clustering jets from
  generator-level events read with pyhepmc or pylhe, or processing many events
  over awkward arrays with the array-oriented (columnar) interface to avoid slow
  Python loops.
---

# fastjet

## Overview

fastjet is the standard jet-finding library in HEP. The Scikit-HEP `fastjet`
PyPI package provides official Python bindings to the complete FastJet C++
library and Awkward Array. It exposes the anti-kt, Cambridge/Aachen, and kt
clustering algorithms. In ATLAS physics analyses the main use is truth-level jet
clustering for generator studies or jet substructure calculations on
particle-level events.

The older `pyjet` package is a **separate, archived, deprecated** project (it
wrapped only `fjcore` over NumPy structured arrays) — it is _not_ an older name
for `fastjet`. Use `fastjet` for all new work.

The library provides two interfaces: the **array-oriented (columnar)
interface**, which accepts `awkward` arrays directly and handles many events at
once without Python loops, and the **classic (object-oriented) interface**,
which mirrors the C++ API and operates one event at a time on lists of
`PseudoJet` objects. Prefer the columnar interface whenever you are iterating
over events.

## When to Use

- Clustering particle-level or parton-level events from a Monte Carlo generator
- Computing jet substructure variables (N-subjettiness, soft drop) for truth
  jets
- Validating detector-level jets against truth clustering
- Grooming jets for boosted object analyses

## Key Concepts

| Concept                       | Notes                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------- |
| `fastjet.ClusterSequence`     | Dispatch point: pass `ak.Array` → columnar; pass `list[PseudoJet]` → classic    |
| `AwkwardClusterSequence`      | Internal type created for columnar input; `inclusive_jets()` returns `ak.Array` |
| `fastjet.PseudoJet`           | Four-vector container (px, py, pz, E) — classic interface only                  |
| `fastjet.JetDefinition`       | Algorithm + R parameter, e.g. `antikt_algorithm` with R=0.4                     |
| `fastjet.ClusterSequenceArea` | Adds jet area computation (needed for pileup subtraction) — classic only        |
| `fastjet.Selector`            | Filter jets by pT, eta, etc. — classic interface                                |
| Jet constituents (columnar)   | `cluster.constituents()` returns jagged `ak.Array` of particles per jet         |
| Jet constituents (classic)    | `jet.constituents()` returns list of PseudoJets                                 |
| User index                    | `pseudo_jet.set_user_index(i)` links back to the original particle              |

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

jets = fj.sorted_by_pt(cs.inclusive_jets(ptmin=25.0))   # 25 GeV (use 25000.0 MeV for ATLAS)

for j in jets:
    print(f"pT={j.pt():.1f} GeV  eta={j.eta():.2f}  phi={j.phi():.2f}")
    print(f"  {len(j.constituents())} constituents")
```

### Columnar interface — single event (px/py/pz/E fields)

Pass an `ak.Array` directly; no `PseudoJet` construction loop needed. Output is
also an `ak.Array` (`MomentumArray4D`), not a list.

```python
import fastjet
import awkward as ak

particles = ak.Array([
    {"px": 1.2,  "py": 3.2,  "pz":   5.4, "E":  23.5},
    {"px": 32.2, "py": 64.21, "pz": 543.34, "E": 755.12},
    {"px": 32.45, "py": 63.21, "pz": 543.14, "E": 835.56},
])

jetdef = fastjet.JetDefinition(fastjet.antikt_algorithm, 0.4)
cluster = fastjet.ClusterSequence(particles, jetdef)

jets = cluster.inclusive_jets(min_pt=25.0)  # MomentumArray4D; 25 GeV (use 25000.0 MeV for ATLAS)
print(jets.pt, jets.eta, jets.phi)
```

### Columnar interface — multi-event (jagged awkward array)

The columnar interface is designed for many events at once. Pass a jagged array
(outer dim = events, inner dim = particles per event); output is also jagged.

```python
import fastjet
import awkward as ak

# Each sub-array is one event; lengths may differ (jagged)
events = ak.Array([
    [{"px": 1.2,  "py": 3.2,  "pz":   5.4, "E":  23.5},
     {"px": 32.2, "py": 64.21, "pz": 543.34, "E": 755.12}],
    [{"px": 32.45, "py": 63.21, "pz": 543.14, "E": 835.56},
     {"px": -1.2, "py": -3.2, "pz": -5.4, "E": 23.5}],
])

jetdef = fastjet.JetDefinition(fastjet.antikt_algorithm, 0.4)
cluster = fastjet.ClusterSequence(events, jetdef)

jets = cluster.inclusive_jets(min_pt=25.0)  # jagged: [[jets_ev0], [jets_ev1]]; 25 GeV (use 25000.0 MeV for ATLAS)
print(ak.num(jets, axis=1))   # number of jets per event
print(jets.pt)                # pT of all jets, jagged
```

### Columnar interface — pt/eta/phi/M coordinates with vector

```python
import fastjet
import awkward as ak
import vector
vector.register_awkward()

events = ak.Array(
    [
        [{"pt": 71.8, "eta": 2.72, "phi": 1.11, "M": 0.14},
         {"pt": 3.42, "eta": 1.24, "phi": 1.21, "M": 0.0}],
        [{"pt": 55.0, "eta": -1.5, "phi": 0.5,  "M": 0.14}],
    ],
    with_name="Momentum4D",
)

jetdef = fastjet.JetDefinition(fastjet.antikt_algorithm, 0.4)
cluster = fastjet.ClusterSequence(events, jetdef)
jets = cluster.inclusive_jets(min_pt=25.0)  # 25 GeV (use 25000.0 MeV for ATLAS)
```

### Columnar interface — accessing constituents without a Python loop

```python
# constituents() returns a jagged array: [event][jet] → ak.Array of particles
constituents = cluster.constituents(min_pt=25.0)  # 25 GeV (use 25000.0 MeV for ATLAS)
# constituents[event_i][jet_j] is an ak.Array of the contributing particles
# e.g. sum constituent pT:
print(ak.sum(constituents.pt, axis=-1))
```

### Jet substructure: N-subjettiness

fjcontrib is compiled into the `fastjet` extension but is **not** exposed as a
`fastjet.contrib` submodule with `Nsubjettiness`/`SoftDrop` classes. Instead it
is reached through methods on the (columnar) cluster sequence, with the contrib
axes/measure definitions passed as strings:

```python
import fastjet
import awkward as ak

cluster = fastjet.ClusterSequence(events, jetdef)

# tau_N for N in njets, computed per jet; returns an ak.Array
tau = cluster.njettiness(
    njets=[1, 2, 3],
    measure_definition="NormalizedMeasure",   # or "UnnormalizedMeasure"
    axes_definition="OnePass_KT_Axes",
    beta=1.0,
    R0=0.8,
)
```

### Soft drop grooming

```python
# kwarg is symmetry_cut (the z_cut), not zcut
groomed = cluster.exclusive_jets_softdrop_grooming(
    njets=1, beta=0.0, symmetry_cut=0.1, R0=0.8
)
```

### Jet area (for pileup)

```python
ghost_area = fj.AreaDefinition(fj.active_area, fj.GhostedAreaSpec(5.0))
cs_area = fj.ClusterSequenceArea(pseudojets, jet_def, ghost_area)
for j in cs_area.inclusive_jets(ptmin=25.0):  # 25 GeV (use 25000.0 MeV for ATLAS)
    print(f"area = {j.area():.3f}")
```

## Gotchas

- **Prefer the columnar interface over per-particle loops**: Building
  `PseudoJet` objects one-by-one in a Python loop
  (`[fj.PseudoJet(p.px, ...) for p in particles]`) crosses the Python
  interpreter on every particle and every event. Pass an `ak.Array` to
  `ClusterSequence` directly — this pushes the conversion into C++ and processes
  all events without Python overhead.
- **Jet area is classic-only**: `ClusterSequenceArea` and `AreaDefinition`
  operate on `PseudoJet` lists (SWIG interface); there is no awkward/columnar
  area path. Substructure (N-subjettiness, soft drop) _is_ available on the
  columnar cluster sequence via methods (`njettiness`,
  `exclusive_jets_softdrop_grooming`) — not via classic `PseudoJet` loops.
- **No `fastjet.contrib` submodule**: fjcontrib is compiled in but is not
  exposed as importable classes. There is no `from fastjet import contrib`, no
  `Nsubjettiness`/`SoftDrop` class. Use the cluster-sequence methods above with
  string axes/measure definitions.
- **Units**: fastjet has no built-in unit system — ensure all four-vectors use
  the same units (usually GeV).
- **`phi()` range**: fastjet returns phi in `[0, 2π)`; some downstream code
  expects `(-π, π]`. Use `PseudoJet.phi_std()` (range `(-π, π]`) or subtract
  `2π` if needed.
- **pyjet is deprecated**: the older `pyjet` package (archived, NumPy structured
  arrays, `fjcore` only) is _not_ an older name for `fastjet`. Migrate to the
  Scikit-HEP `fastjet` package.
- **`inclusive_jets` kwarg differs by interface**: columnar uses `min_pt=`;
  classic (`PseudoJet`-based) uses `ptmin=`.
- **`with_name="Momentum4D"` required for pt/eta/phi/M input**: Without
  `vector.register_awkward()` and `with_name="Momentum4D"`, the columnar
  interface only auto-detects `(px, py, pz, E)` field names.

## Interop

- **pyhepmc**: Read HepMC3 events, extract final-state particles into an
  `ak.Array` with `(px, py, pz, E)` fields, then pass directly to
  `ClusterSequence` using the columnar interface.
- **pylhe**: Read LHE parton-level events for parton-jet matching studies.
- **vector / awkward**: Use `vector.register_awkward()` +
  `with_name="Momentum4D"` to pass `(pt, eta, phi, M)` arrays to the columnar
  interface. Classic interface still requires converting to `PseudoJet` objects
  first.

## Docs

Python bindings: https://fastjet.readthedocs.io/ — FastJet C++:
https://fastjet.fr/
