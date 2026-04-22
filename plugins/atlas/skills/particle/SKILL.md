---
name: particle
description: >-
  Use when looking up particle properties (mass, charge, PDG ID, lifetime,
  width) from the PDG tables in Python: converting between particle names and
  PDG IDs, filtering decay modes, checking if a particle is stable, or working
  with Monte Carlo generator output where particle codes need to be identified.
---

# particle

## Overview

The `particle` library provides the full PDG particle table in Python. It wraps
PDG IDs, masses, charges, lifetimes, decay modes, and particle names in a
queryable object model. It is the standard Scikit-HEP tool for particle
identification tasks that would otherwise require hardcoding PDG ID tables.

## When to Use

- Identifying particles in Monte Carlo truth records by PDG ID
- Looking up masses for four-vector construction
- Filtering generator-level events by particle type or stability
- Checking antiparticle relations and charge conjugation

## Key Concepts

| Concept                    | Notes                                                       |
| -------------------------- | ----------------------------------------------------------- |
| `Particle.from_pdgid(id)`  | Look up by integer PDG ID (e.g. 211 = π+)                   |
| `Particle.from_name(name)` | Look up by name string (e.g. "K+", "B0")                    |
| `Particle.findall(fn)`     | Filter PDG table; accepts a lambda or a name-glob string    |
| `p.mass`                   | Mass in MeV (float) — divide by 1000 for GeV                |
| `p.charge`                 | Charge in units of e (float)                                |
| `p.lifetime`               | Lifetime in ns; `inf` for stable particles                  |
| `p.is_stable`              | True if lifetime is effectively infinite                    |
| `p.pdgid`                  | `PDGID` object with `.is_meson`, `.is_baryon`, `.is_lepton` |
| `p.invert()`               | Returns the antiparticle                                    |

## Canonical Patterns

### Look up by PDG ID

```python
from particle import Particle

p = Particle.from_pdgid(211)   # π+
print(p.name)                   # "pi+"
print(p.mass)                   # mass in MeV (float)
print(p.charge)                 # charge in units of e (float)
print(p.lifetime)               # lifetime in ns (float or inf)
print(p.ctau)                   # c*tau in mm
print(p.is_stable)              # True if lifetime is effectively infinite
```

### Look up by name

```python
p = Particle.from_name("K+")
print(p.pdgid)                  # 321
print(p.mass)                   # 493.677 MeV
```

### Search / filter

```python
# All B mesons
b_mesons = Particle.findall(lambda p: p.pdgid.is_meson and abs(int(p.pdgid)) // 100 == 5)

# All stable particles
stable = Particle.findall(lambda p: p.is_stable)

# Particles with a given name pattern
kaons = Particle.findall("K*")  # string glob
```

### Antiparticles

```python
pi_plus  = Particle.from_name("pi+")
pi_minus = pi_plus.invert()     # antiparticle
print(pi_minus.pdgid)           # -211
```

### Decay modes (if available)

```python
from particle import Particle

b0 = Particle.from_name("B0")
for mode in b0.decay_modes:
    print(mode)
```

### Use with generator truth (e.g. from pyhepmc)

```python
from particle import Particle

def is_b_hadron(pdgid: int) -> bool:
    try:
        p = Particle.from_pdgid(pdgid)
        return p.pdgid.is_meson and (abs(pdgid) // 100 % 10 == 5 or
                                     abs(pdgid) // 1000 % 10 == 5)
    except Exception:
        return False
```

## Gotchas

- **Masses in MeV, not GeV**: `p.mass` returns MeV consistent with PDG tables —
  divide by 1000 for GeV.
- **`pdgid` is not a plain int**: it's a `PDGID` object with `.is_meson`,
  `.is_baryon`, `.is_lepton` attributes. Use `int(p.pdgid)` if you need a plain
  integer.
- **Unknown PDG IDs raise exceptions**: wrap lookups in `try/except` when
  processing Monte Carlo output, where generator-specific codes (e.g. `9999999`)
  may appear.
- **Decay mode coverage is incomplete**: not all particles have decay modes in
  the PDG table.

## Interop

- **pyhepmc**: Extract PDG IDs from `HepMC3::GenParticle` truth records and
  identify them with `Particle`.
- **decaylanguage**: Uses `particle` internally for decay descriptor parsing.
- **hepunits**: Use alongside `particle` for unit-safe mass comparisons.

## Docs

https://scikit-hep.org/particle/
