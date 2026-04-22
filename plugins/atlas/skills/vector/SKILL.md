---
name: vector
description: >-
  Use when computing 4-vector quantities in Python: invariant mass, deltaR,
  transverse momentum, boost, or any Lorentz vector arithmetic over collections
  of particles. Also use when registering scikit-hep vector behaviors on
  awkward-array records so that ak.zip objects gain Momentum4D methods, or when
  constructing vector objects from (pt, phi, eta, mass) or (px, py, pz, energy)
  field conventions.
---

# Vector

## Overview

The `vector` library provides Lorentz vector arithmetic for NumPy arrays,
awkward-array records, and scalar objects. The key design: register behaviors on
`ak.Array` records once, then use physics methods (`.deltaR()`, `.mass`,
`.boost(...)`) directly without manual kinematic math.

## When to Use

- Computing invariant mass or transverse mass of particle combinations
- Computing deltaR between two objects for overlap removal or matching
- Boosting to the rest frame of a parent particle
- Any operation that would otherwise require manual `px = pt * cos(phi)` etc.

## Key Concepts

| Concept                     | Notes                                                               |
| --------------------------- | ------------------------------------------------------------------- |
| `vector.register_awkward()` | One-time call; mutates global behavior dict — call at module level  |
| Field name conventions      | `pt/phi/eta/mass` OR `px/py/pz/energy` — vector auto-detects        |
| `Momentum4D`                | The most common type for HEP 4-vectors                              |
| `.deltaR(other)`            | ΔR = √(Δη² + Δφ²) — available as method after behavior registration |
| `.mass` property            | Invariant mass from E²-p² = m²                                      |

## Canonical Patterns

**Register behaviors (do once at module top)**:

```python
import vector
vector.register_awkward()
```

**Build a Momentum4D record array from NTuple columns**:

```python
import awkward as ak
jets = ak.zip(
    {"pt": events["jet_pt"], "phi": events["jet_phi"],
     "eta": events["jet_eta"], "mass": events["jet_m"]},
    with_name="Momentum4D",
)
# Now jets.deltaR(other), jets.mass, jets.px, etc. all work
```

**Invariant mass of all jet pairs**:

```python
combos = ak.combinations(jets, 2, axis=1)
j1, j2 = ak.unzip(combos)
mjj = (j1 + j2).mass / 1000  # MeV → GeV
```

**deltaR between every electron–jet pair (for overlap removal)**:

```python
pairs = ak.cartesian({"e": electrons, "j": jets}, axis=1)
dr = pairs.e.deltaR(pairs.j)
non_overlapping = jets[~ak.any(dr < 0.4, axis=1)]  # remove jets near any electron
```

**Boost to rest frame of a parent**:

```python
# parent must be a vector object
boosted = daughter.boost(-parent.to_beta3())
```

**Pure NumPy (no awkward)** — for scalar or fixed-shape arrays:

```python
v = vector.obj(pt=30.0, phi=0.5, eta=1.2, mass=0.105)  # muon
print(v.px, v.py, v.pz, v.energy)
```

## Gotchas

- **`register_awkward()` before any vector access**: Calling `.deltaR()` on an
  `ak.Array` without prior registration raises `AttributeError`. If you see
  this, you forgot the registration call.
- **Field names must match exactly**: `energy` not `E`, `mass` not `m`. Vector
  picks the convention from the field names — mixing `pt/phi/eta/energy` is
  fine; mixing `pt` and `px` is not.
- **Units are your responsibility**: Vector does no unit conversion. If pT is in
  MeV, masses and energies are in MeV throughout. Divide by 1000 explicitly
  before presenting in GeV.
- **`with_name` is required for ak.zip** to get behavior:
  `ak.zip({...}, with_name="Momentum4D")`. Without it, records are plain dicts.
- **Addition of 4-vectors**: `j1 + j2` returns a new `Momentum4D` vector —
  invariant mass is then `(j1 + j2).mass`.

## Interop

- **awkward**: Required — `register_awkward()` enables methods on `ak.Array`
  records
- **uproot**: Fields read from ROOT files usually need renaming to match vector
  conventions
- **hist**: Compute quantities with vector, then flatten and fill `Hist`
- **numpy**: `vector.array(...)` creates NumPy-backed vectors for fixed-shape
  data

## Docs

https://vector.readthedocs.io/en/latest/
