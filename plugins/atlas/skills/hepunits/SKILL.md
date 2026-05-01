---
name: hepunits
description: >-
  Use when writing unit-safe HEP code in Python: converting between MeV and GeV,
  expressing cross-sections or luminosities with explicit units, computing ctau
  or decay lengths from particle lifetimes, checking that cut thresholds or
  histogram ranges carry correct units, or bridging hepunits values with Pint
  quantities.
---

# hepunits

## Overview

hepunits provides physical unit constants and physical constants as plain Python
floats, following the CLHEP/Geant4 convention. Base units include **MeV**
(energy), **mm** (length), **ns** (time), **eplus** (charge), and **kelvin**
(temperature) — see the full table below. Multiplying by a unit constant
converts a value into the system base; dividing converts back out.

## When to Use

- Writing cuts, histogram ranges, or mass comparisons that need to be readable
  and unit-safe
- Expressing cross-sections, luminosities, or decay lengths with explicit units
- Computing ctau or other derived quantities from physical constants
- Bridging hepunits float values with Pint quantities

## Key Concepts

### Module Structure

hepunits exposes two sub-modules, both re-exported at the top level:

| Module               | Contents                                            |
| -------------------- | --------------------------------------------------- |
| `hepunits.units`     | All unit constants (length, energy, time, angle, …) |
| `hepunits.constants` | Physical and mathematical constants                 |

```python
from hepunits import GeV, MeV, c_light         # top-level (most common)
from hepunits.units import picosecond, micrometer
from hepunits.constants import c_light
import hepunits.units as u                      # namespace alias
```

### Base units

| Quantity    | Base unit | Value in base |
| ----------- | --------- | ------------- |
| Energy      | `MeV`     | 1.0           |
| Length      | `mm`      | 1.0           |
| Time        | `ns`      | 1.0           |
| Charge      | `eplus`   | 1.0           |
| Temperature | `kelvin`  | 1.0           |

### Energy units

| Symbol | Value (MeV) |
| ------ | ----------- |
| `eV`   | 1e-6        |
| `keV`  | 0.001       |
| `MeV`  | 1.0         |
| `GeV`  | 1000.0      |
| `TeV`  | 1_000_000.0 |
| `PeV`  | 1e9         |
| `EeV`  | 1e12        |

### Length units

`fermi` (fm), `angstrom`, `nanometer`, `micrometer`, `mm`, `cm`, `m`, `km`

### Time units

`femtosecond`, `picosecond`, `ns`, `microsecond`, `ms`, `s`, `minute`, `day`

### Frequency

`Hz`, `kHz`, `MHz`, `GHz`, `THz` — all as `s⁻¹` in CLHEP units

### Angle

`radian`, `degree` (note: `360 * degree == two_pi * radian`)

### Cross-section and luminosity

`barn`, `millibarn`, `microbarn`, `nanobarn`, `picobarn`, `fm2`

`invpb`, `invfb` (inverse cross-section, for luminosity)

### Area / volume

`mm2`, `cm2`, `km2`, `meter2`, `mm3`, `cm3`, `m3`

### Electromagnetic

`gauss`, `tesla`, `weber`, `maxwell`, `ohm`, `coulomb`

### Radiation

`gray`, `sievert`, `curie`, `becquerel`

### SI prefixes (multiplicative scalars)

`yocto`, `micro`, `milli`, `kilo`, `mega`, `giga`, `tera`, `yotta`

Binary: `kibi`, `tebi`

```python
from hepunits import mega, micro
assert 4 * mega == 1.0 / 0.25 / micro   # True
```

### Physical constants

| Name                         | Description             |
| ---------------------------- | ----------------------- |
| `c_light`                    | Speed of light in mm/ns |
| `h_Planck`                   | Planck constant         |
| `hbar`                       | Reduced Planck constant |
| `hbarc_sq`                   | (ħc)²                   |
| `Avogadro`                   | 6.02214076e23 mol⁻¹     |
| `pi_sq`, `two_pi`, `half_pi` | π-derived constants     |

## Canonical Patterns

### Readable cuts

```python
from hepunits import GeV, MeV

jet_pt_cut = 25.0 * GeV    # stored as MeV internally
met_cut    = 200.0 * GeV

mask = (jet_pt > jet_pt_cut) & (met > met_cut)
```

### Converting to plot units (GeV)

```python
from hepunits import GeV

jet_pt_gev = jet_pt / GeV    # divide to convert out of base units
```

### Namespace alias style

```python
from hepunits import units as u

total_length = 1 * u.meter + 5 * u.cm   # 1050.0 mm
in_meters = total_length / u.meter       # 1.05
```

### ctau from particle lifetime

```python
from hepunits.constants import c_light
from hepunits.units import picosecond, micrometer

tau_Bs = 1.5 * picosecond       # lifetime in ns (CLHEP base)
ctau_Bs = c_light * tau_Bs      # result in mm
print(ctau_Bs / micrometer)     # → ~449.7 µm
```

### Mass window using physical constants

```python
from hepunits import MeV
from particle import Particle

m_z = Particle.from_name("Z0").mass    # already in MeV
window_lo = m_z - 10 * MeV
window_hi = m_z + 10 * MeV
mask = (inv_mass > window_lo) & (inv_mass < window_hi)
```

### Histogram range with units

```python
import hist
from hepunits import GeV

h = hist.Hist(hist.axis.Regular(
    50, 0 * GeV, 1000 * GeV,
    name="pt", label=r"$p_T$ [GeV]",
))
h.fill(pt=jet_pt / GeV)    # fill after converting to GeV
```

### Cross-section in pb

```python
from hepunits import picobarn

xs = 40.0 * picobarn    # 40 pb stored in CLHEP cross-section units
```

### Pint integration (optional dependency)

```python
import pint
import hepunits
from hepunits.pint import to_clhep, from_clhep

ureg = pint.UnitRegistry()

g = 9.8 * ureg.meter / ureg.second**2
to_clhep(g)                                       # convert Pint → CLHEP float
from_clhep(hepunits.c_light, ureg.meter / ureg.second)  # CLHEP float → Pint Quantity
```

Note: `to_clhep` raises `ValueError` for unsupported dimensions (e.g. kelvin).

## Gotchas

- **Base unit is MeV, not GeV**: `1 * GeV == 1000.0`. ATLAS NTuples store
  energies in MeV — divide by `GeV` to plot in GeV; multiplying goes the wrong
  way.
- **Plain floats, no dimension checking**: Mixing up `*` and `/` silently
  produces wrong numbers. No exception is raised.
- **`particle` interop**: `Particle.mass` returns MeV, consistent with CLHEP
  base units.
- **Pint is optional**: `hepunits.pint` is only importable when `pint` is
  installed. Not all dimensions are supported by `to_clhep`.

## Interop

- **particle**: `Particle.mass` in MeV, directly compatible.
- **vector / awkward**: No built-in integration; apply conversions before
  constructing four-vectors.
- **Pint**: `hepunits.pint.to_clhep` / `from_clhep` bridge the two systems.

## Docs

https://github.com/scikit-hep/hepunits/#readme
