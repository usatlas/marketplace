---
name: particle
description: >-
  Use when looking up particle properties (mass, charge, width, PDG ID,
  lifetime, spin, parity) from the PDG tables in Python: converting between
  particle names and PDG IDs, filtering decay modes, checking if a particle is
  stable, querying quantum numbers (J, P, C, G, I), working with MC generator
  output where particle codes need to be identified or converted (Geant3,
  Pythia, Corsika7, EvtGen), or using particle/PDGID literals in analysis code.
---

# particle

## Overview

The `particle` library provides the full PDG particle table in Python. It wraps
PDG IDs, masses, widths, charges, lifetimes, decay modes, quantum numbers, and
particle names in a queryable object model. It is the standard Scikit-HEP tool
for particle identification tasks that would otherwise require hardcoding PDG ID
tables.

Two main classes:

- `PDGID` — wraps an integer PDG ID with classification queries. Useful for fast
  truth-particle filtering without loading the full table.
- `Particle` — wraps a full PDG table entry with mass, width, quantum numbers,
  decay modes, and name formatting.

## When to Use

- Identifying particles in Monte Carlo truth records by PDG ID
- Looking up masses or widths for four-vector construction or selection cuts
- Filtering generator-level events by particle type, stability, or quantum
  numbers
- Converting between generator-specific IDs (Geant3, Pythia, Corsika7, EvtGen)
  and PDG IDs
- Checking antiparticle relations and charge conjugation
- Displaying human-readable or LaTeX particle names in plots

## Key Concepts

| Attribute / method             | Notes                                                        |
| ------------------------------ | ------------------------------------------------------------ |
| `Particle.from_pdgid(id)`      | Look up by integer PDG ID (e.g. 211 = π+)                    |
| `Particle.from_name(name)`     | Look up by name string (e.g. "K+", "B0")                     |
| `Particle.from_evtgen_name(n)` | Look up by EvtGen name (e.g. "J/psi")                        |
| `Particle.findall(fn, **kw)`   | Filter PDG table; callable, name-glob, or keyword args       |
| `Particle.finditer(fn, **kw)`  | Same as findall but returns an iterator                      |
| `p.mass`                       | Mass in MeV (float or None) — divide by 1000 for GeV         |
| `p.width`                      | Decay width in MeV (float or None)                           |
| `p.charge`                     | Charge in units of e (float)                                 |
| `p.lifetime`                   | Lifetime in ns; `inf` for stable particles                   |
| `p.ctau`                       | c·τ in mm                                                    |
| `p.is_stable`                  | True if lifetime is effectively infinite                     |
| `p.is_self_conjugate`          | True for particles that are their own antiparticle (e.g. π0) |
| `p.J`, `p.P`, `p.C`, `p.G`     | Spin, parity, charge-conjugation, G-parity quantum numbers   |
| `p.I`                          | Isospin quantum number                                       |
| `p.spin_type`                  | `SpinType` enum (Scalar, Vector, …)                          |
| `p.pdgid`                      | `PDGID` object — see PDGID properties below                  |
| `p.invert()`                   | Returns the antiparticle                                     |
| `p.describe()`                 | Full human-readable property summary                         |
| `p.latex_name`                 | LaTeX string (e.g. `"$\\pi^{+}$"`)                           |
| `p.programmatic_name`          | Python identifier-safe name (e.g. `"pi_plus"`)               |

**PDGID properties** (on `p.pdgid` or standalone `PDGID(id)`):

| Property                 | Meaning                                |
| ------------------------ | -------------------------------------- |
| `.is_valid`              | PDG ID is a recognised particle        |
| `.is_meson`              | Is a meson                             |
| `.is_baryon`             | Is a baryon                            |
| `.is_lepton`             | Is a lepton                            |
| `.is_hadron`             | Is a hadron (meson or baryon)          |
| `.has_bottom`            | Contains a b quark                     |
| `.has_charm`             | Contains a c quark                     |
| `.has_strange`           | Contains an s quark                    |
| `.is_nucleus`            | Is a nuclear PDG ID                    |
| `.is_generator_specific` | Generator-internal code (e.g. 9999999) |
| `.J`                     | Total spin (float or None)             |
| `.charge`                | Charge in units of e                   |

## Canonical Patterns

### Look up by PDG ID

```python
from particle import Particle

p = Particle.from_pdgid(211)   # π+
print(p.name)                   # "pi+"
print(p.mass)                   # 139.57039 MeV
print(p.width)                  # width in MeV (or None)
print(p.charge)                 # 1.0 (units of e)
print(p.lifetime)               # lifetime in ns
print(p.ctau)                   # c*tau in mm
print(p.is_stable)              # False
print(p.J, p.P)                 # spin and parity
print(p.latex_name)             # "$\\pi^{+}$"
```

### Look up by name or EvtGen name

```python
p = Particle.from_name("K+")
print(p.pdgid, p.mass)          # 321, 493.677 MeV

p = Particle.from_evtgen_name("J/psi")
print(p.name, p.pdgid)          # "J/psi(1S)", 443
```

### Search / filter with keyword args

```python
# All neutral beauty hadrons (particle=True excludes antiparticles)
Particle.findall(lambda p: p.pdgid.has_bottom and p.charge == 0, particle=True)

# By PDG name (exact)
Particle.findall(pdg_name="pi")           # pi0, pi+, pi-

# By quantum numbers
Particle.findall(J=1, P=-1)              # spin-1 negative-parity particles (vectors)

# K+ and K- by glob pattern
Particle.findall("K*")

# Strange mesons with c*tau > 1 m — use hepunits for unit safety
from hepunits import meter
Particle.findall(
    lambda p: p.pdgid.is_meson and p.pdgid.has_strange and p.ctau > 1 * meter,
    particle=True,
)
# → [K(L)0, K+]

# finditer is lazy — prefer it for large scans
for p in Particle.finditer(lambda p: p.pdgid.has_charm):
    print(p.name, p.mass)
```

### Antiparticles

```python
pi_plus  = Particle.from_name("pi+")
pi_minus = pi_plus.invert()
print(pi_minus.pdgid)           # -211
print(pi_plus.is_self_conjugate)   # False
print(Particle.from_name("pi0").is_self_conjugate)  # True
```

### PDGID standalone (fast, no full table load)

```python
from particle import PDGID

pid = PDGID(211)
print(pid.is_meson, pid.has_strange)  # True, False
print(pid.is_valid)                   # True

bad = PDGID(99999999)
print(bad.is_valid)                   # False (generator-specific code)

# Standalone functions mirror PDGID properties
from particle.pdgid import is_meson, has_bottom
print(is_meson(211))                  # True
print(has_bottom(5122))               # True (Lambda_b)
```

### Particle and PDGID literals

```python
from particle import literals as lp
print(lp.pi_plus)                     # <Particle: name="pi+", pdgid=211, …>
print(lp.Lambda_b_0.J)               # 0.5

from particle.pdgid import literals as lid
print(lid.pi_plus)                    # <PDGID: 211>
print(lid.Lambda_b_0.has_bottom)      # True
```

### MC generator ID converters

```python
from particle import Particle, Geant3ID, PythiaID, Corsika7ID

# Geant3 → PDG
g3id = Geant3ID(8)
p = Particle.from_pdgid(g3id.to_pdgid())
print(p.name)   # "pi+"

# Pythia → PDG
pythiaid = PythiaID(211)
p = Particle.from_pdgid(pythiaid.to_pdgid())

# Corsika7 → PDG
cid = Corsika7ID(5)
p = Particle.from_pdgid(cid.to_pdgid())
print(p.name)   # "mu+"

# Bidirectional map (Pythia ↔ PDG)
from particle.converters import Pythia2PDGIDBiMap
from particle import PDGID, PythiaID
pyid = Pythia2PDGIDBiMap[PDGID(9010221)]
pdgid = Pythia2PDGIDBiMap[PythiaID(10221)]
```

### Decay modes (if available)

```python
b0 = Particle.from_name("B0")
for mode in b0.decay_modes:
    print(mode)
```

### Use with generator truth (e.g. from pyhepmc)

```python
from particle import PDGID

def classify_truth_particle(pdgid: int) -> str:
    pid = PDGID(pdgid)
    if not pid.is_valid:
        return "generator_specific"
    if pid.is_lepton:
        return "lepton"
    if pid.has_bottom:
        return "b_hadron"
    if pid.has_charm:
        return "c_hadron"
    return "other"
```

### Describe a particle

```python
p = Particle.from_pdgid(321)   # K+
print(p.describe())
# Name: K+   ID: 321   Latex: $K^{+}$
# Mass  = 493.677 ± 0.016 MeV
# Width = -1.0 MeV
# Q = +   J = 0.0   P = -   …
```

## Gotchas

- **Masses in MeV, not GeV**: `p.mass` returns MeV — divide by 1000 for GeV.
  This is consistent with all other ATLAS/Scikit-HEP tools.
- **`pdgid` is not a plain int**: it's a `PDGID` object. Use `int(p.pdgid)` or
  `p.pdgid.numerator` if you need a plain integer for numpy/awkward comparisons.
- **Unknown PDG IDs raise `ParticleNotFound`**: wrap lookups with
  `try/except ParticleNotFound` when processing MC output, where
  generator-specific codes (e.g. `9999999`) appear. `PDGID.is_valid` and
  `PDGID.is_generator_specific` let you pre-filter without exceptions.
- **Decay mode coverage is incomplete**: not all particles have decay modes in
  the PDG table; `b0.decay_modes` may be an empty list.
- **`findall` vs `finditer`**: `findall` returns a sorted list; `finditer`
  returns a lazy iterator — prefer `finditer` for large scans to avoid
  materialising the full result.
- **`particle=True/False` kwarg**: without it, `findall` returns both particles
  and antiparticles. Pass `particle=True` to restrict to particles only.
- **Width of stable particles**: `p.width` returns `None` or negative sentinel
  for particles where no width is meaningful. Check `p.is_stable` first.

## Interop

- **pyhepmc**: Extract PDG IDs from `GenParticle.pid` in HepMC3 truth records;
  classify with `PDGID` or `Particle`.
- **decaylanguage**: Uses `particle` internally for decay descriptor parsing;
  shares the same particle name conventions.
- **hepunits**: Use alongside `particle` for unit-safe comparisons —
  `p.ctau > 1 * meter` works because `ctau` is in hepunits-native mm.
- **vector / awkward**: Convert `p.mass` (MeV) to GeV before passing to
  four-vector constructors that expect GeV.

## Docs

https://github.com/scikit-hep/particle#readme
