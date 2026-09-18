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

## Gotchas

- **Masses in MeV, not GeV**: `p.mass` returns MeV — divide by 1000 for GeV.
  This is consistent with all other ATLAS/Scikit-HEP tools.
- **`pdgid` is not a plain int**: it's a `PDGID` object. Use `int(p.pdgid)` or
  `p.pdgid.numerator` if you need a plain integer for numpy/awkward comparisons.
- **Unknown PDG IDs raise `ParticleNotFound`**: wrap lookups with
  `try/except ParticleNotFound` when processing MC output, where
  generator-specific codes (e.g. `9999999`) appear. `PDGID.is_valid` and
  `PDGID.is_generator_specific` let you pre-filter without exceptions.
- **No decay-mode data on `Particle`**: identity/mass/width only — there is no
  `decay_modes` attribute. Use the `decaylanguage` skill (`.dec` file parsing)
  for branching fractions and decay chains.
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

## Reference Files

For deeper detail beyond what this skill covers, read the reference files in
`references/`:

- **`references/advanced-usage.md`** — Filtering the PDG table by quantum
  numbers or glob patterns, antiparticle handling, standalone `PDGID` queries,
  MC generator ID converters (Geant3, Pythia, Corsika7), decay mode lookups, MC
  truth classification, and full particle description printouts. Read when the
  common `from_pdgid`/`from_name` lookups in this file aren't enough — e.g.
  filtering the whole PDG table, converting generator-specific codes, or
  classifying truth particles by quantum number.

## Docs

https://github.com/scikit-hep/particle#readme
