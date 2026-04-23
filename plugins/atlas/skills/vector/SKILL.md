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

| Concept                     | Notes                                                                          |
| --------------------------- | ------------------------------------------------------------------------------ |
| `vector.register_awkward()` | One-time call; mutates global behavior dict — call at module level             |
| Field name conventions      | `pt/phi/eta/mass` OR `px/py/pz/energy` — vector auto-detects                   |
| `Momentum4D`                | The most common type for HEP 4-vectors                                         |
| `.deltaR(other)`            | ΔR = √(Δη² + Δφ²) — available as method after behavior registration            |
| `.mass` property            | Invariant mass from E²-p² = m²                                                 |
| `vector.obj(...)`           | Single scalar Python object — fast in Numba, slow in plain Python loops        |
| `vector.array(...)`         | NumPy structured-array subclass — vectorized, good for fixed-shape collections |

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

**Scalar Python object (`vector.obj`) — single vector or Numba use**:

```python
# Scalar: useful for quick checks or as accumulators inside @nb.njit functions
v = vector.obj(pt=30.0, phi=0.5, eta=1.2, mass=0.105)  # single muon
print(v.px, v.py, v.pz, v.energy)
```

`vector.obj` returns a plain Python object, not a NumPy array. It is slow in
Python loops but compiles efficiently under `@nb.njit`.

**NumPy structured array (`vector.array`) — fixed-shape collections**:

```python
import numpy as np
# vector.array wraps np.ndarray with vector methods via structured dtype
muons = vector.array(
    {"pt": np.array([30.0, 45.0]), "phi": np.array([0.5, -1.2]),
     "eta": np.array([1.2, -0.8]), "mass": np.full(2, 0.105)}
)
print(muons.px, muons.energy)  # vectorized, operates on whole array
```

**Numba-compiled loop over awkward arrays — best for large ragged collections**:

```python
import numba as nb

@nb.njit
def sum_mass(array):
    out = np.empty(len(array), np.float64)
    for i, event in enumerate(array):
        total = vector.obj(px=0.0, py=0.0, pz=0.0, E=0.0)
        for vec in event:
            total = total + vec
        out[i] = total.mass
    return out

# array is a vector.Array (awkward) with Momentum4D records
masses = sum_mass(array)
```

JIT compilation has a cold-start cost but achieves ~500× speedup on large arrays
compared to equivalent Python loops.

## Gotchas

- **`register_awkward()` before any vector access**: Calling `.deltaR()` on an
  `ak.Array` without prior registration raises `AttributeError`. If you see
  this, you forgot the registration call.
- **`vector.obj` is a scalar, not an array**: It represents one vector. For
  arrays of vectors use `vector.array(...)` (NumPy backend) or
  `ak.zip(..., with_name="Momentum4D")` (awkward backend). Lists of `vector.obj`
  are slow in plain Python — use `vector.array` or Numba instead.
- **NumPy backend Numba support is incomplete**: `@nb.njit` works with
  `vector.obj` and `vector.Array` (awkward), but NumPy array (`vector.array`)
  support inside Numba is incomplete (upstream issue [#43]).
- **Field names must match exactly**: `energy` not `E`, `mass` not `m` for
  awkward arrays. Vector picks the convention from the field names — mixing
  `pt/phi/eta/energy` is fine; mixing `pt` and `px` is not. (`vector.obj`
  accepts `E` as an alias for energy.)
- **Units are your responsibility**: Vector does no unit conversion. If pT is in
  MeV, masses and energies are in MeV throughout. Divide by 1000 explicitly
  before presenting in GeV.
- **`with_name` is required for ak.zip** to get behavior:
  `ak.zip({...}, with_name="Momentum4D")`. Without it, records are plain dicts.
- **Addition of 4-vectors**: `j1 + j2` returns a new `Momentum4D` vector —
  invariant mass is then `(j1 + j2).mass`.

## Interop

- **awkward**: Required for jagged/variable-length collections;
  `register_awkward()` enables methods on `ak.Array` records
- **uproot**: Fields read from ROOT files usually need renaming to match vector
  conventions
- **hist**: Compute quantities with vector, then flatten and fill `Hist`
- **numpy**: `vector.array(...)` creates NumPy-backed vectors for fixed-shape
  data; vectorized but not suitable for variable-length/jagged structure
- **numba**: `@nb.njit` works with `vector.obj` and `vector.Array` (awkward);
  best for custom loops over large ragged arrays where awkward vectorization
  cannot express the logic

## Docs

https://vector.readthedocs.io/en/latest/
