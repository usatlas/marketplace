# Particle Advanced Usage Patterns — Deep Reference

Read this reference when filtering the PDG table by quantum numbers or glob
patterns, working with antiparticles, using standalone `PDGID` queries,
converting generator-specific IDs (Geant3, Pythia, Corsika7) to PDG IDs, looking
up decay modes, classifying MC truth particles, or printing a full property
summary for a particle.

## Table of Contents

- [Search / filter with keyword args](#search--filter-with-keyword-args)
- [Antiparticles](#antiparticles)
- [PDGID standalone (fast, no full table load)](#pdgid-standalone-fast-no-full-table-load)
- [Particle and PDGID literals](#particle-and-pdgid-literals)
- [MC generator ID converters](#mc-generator-id-converters)
- [Decay modes (if available)](#decay-modes-if-available)
- [Use with generator truth (e.g. from pyhepmc)](#use-with-generator-truth-eg-from-pyhepmc)
- [Describe a particle](#describe-a-particle)

## Search / filter with keyword args

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

## Antiparticles

```python
pi_plus  = Particle.from_name("pi+")
pi_minus = pi_plus.invert()
print(pi_minus.pdgid)           # -211
print(pi_plus.is_self_conjugate)   # False
print(Particle.from_name("pi0").is_self_conjugate)  # True
```

## PDGID standalone (fast, no full table load)

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

## Particle and PDGID literals

```python
from particle import literals as lp
print(lp.pi_plus)                     # <Particle: name="pi+", pdgid=211, …>
print(lp.Lambda_b_0.J)               # 0.5

from particle.pdgid import literals as lid
print(lid.pi_plus)                    # <PDGID: 211>
print(lid.Lambda_b_0.has_bottom)      # True
```

## MC generator ID converters

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

## Decay modes (if available)

```python
b0 = Particle.from_name("B0")
for mode in b0.decay_modes:
    print(mode)
```

## Use with generator truth (e.g. from pyhepmc)

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

## Describe a particle

```python
p = Particle.from_pdgid(321)   # K+
print(p.describe())
# Name: K+   ID: 321   Latex: $K^{+}$
# Mass  = 493.677 ± 0.016 MeV
# Width = -1.0 MeV
# Q = +   J = 0.0   P = -   …
```
