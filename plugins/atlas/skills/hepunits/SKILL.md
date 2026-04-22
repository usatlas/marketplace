---
name: hepunits
description: >-
  Use when writing unit-safe HEP code in Python: converting between MeV and GeV,
  checking that a cut threshold or histogram range uses the right unit, or
  making unit constants explicit instead of hardcoding 1000 or 1e3 throughout
  analysis code.
---

# hepunits

## Overview

hepunits provides a set of physical unit constants (MeV, GeV, TeV, mm, ns, etc.)
as plain Python floats, following the CLHEP/Geant4 convention where the base
units are MeV, mm, and ns. Multiplying by a unit constant converts a value to
the system base; dividing by a unit constant converts out. It is a lightweight
way to write self-documenting, unit-safe analysis code without a full unit
library.

## When to Use

- Writing cuts, histogram ranges, or mass comparisons that need to be readable
  and unit-safe
- Documenting whether a number is in MeV or GeV without relying on comments
- Normalizing generator-level or reco-level values to a common unit system

## Key Concepts

| Base unit | Value                  |
| --------- | ---------------------- |
| `MeV`     | 1.0 (base energy unit) |
| `GeV`     | 1000.0                 |
| `TeV`     | 1_000_000.0            |
| `keV`     | 0.001                  |
| `mm`      | 1.0 (base length)      |
| `cm`      | 10.0                   |
| `m`       | 1000.0                 |
| `ns`      | 1.0 (base time)        |
| `ps`      | 0.001                  |

## Canonical Patterns

### Readable cuts

```python
from hepunits import GeV, MeV, TeV

# Explicit units in cut thresholds
jet_pt_cut = 25.0 * GeV      # = 25000.0 (MeV, ATLAS NTuple units)
met_cut    = 200.0 * GeV     # = 200000.0
mass_higgs = 125.09 * GeV    # PDG Higgs mass

# Apply to ATLAS NTuple branch (already in MeV)
mask = (jet_pt > jet_pt_cut) & (met > met_cut)
```

### Converting to plot units (GeV)

```python
from hepunits import GeV

jet_pt_gev = jet_pt / GeV    # MeV → GeV (divide by 1000)
```

### Histogram range with units

```python
import hist
from hepunits import GeV

h = hist.Hist(hist.axis.Regular(
    50, 0 * GeV, 1000 * GeV,
    name="pt", label=r"$p_T$ [GeV]",
))
# Fill in MeV, but the axis records that range was defined in MeV via GeV constants
h.fill(pt=jet_pt / GeV)
```

### Mass window

```python
from hepunits import MeV
from particle import Particle

m_z = Particle.from_name("Z0").mass   # already in MeV
window_lo = m_z - 10 * MeV
window_hi = m_z + 10 * MeV
mask = (inv_mass > window_lo) & (inv_mass < window_hi)
```

## Gotchas

- **hepunits base unit is MeV, not GeV**: `1 * GeV == 1000.0`. When filling
  histograms always decide on one unit system and convert explicitly.
- **Not a quantity system**: hepunits constants are plain floats — there is no
  dimension checking. If you mix up multiplication and division, nothing will
  raise an error.
- **ATLAS NTuples store energies in MeV**: dividing by `GeV` converts to GeV;
  multiplying by `GeV` goes the wrong direction.

## Interop

- **particle**: `Particle.mass` returns MeV, consistent with hepunits base
  units.
- **vector / awkward**: No built-in integration; apply unit conversions before
  constructing four-vectors.

## Docs

https://scikit-hep.org/hepunits/
