---
name: decaylanguage
description: >-
  Use when working with decay chain descriptions in Python: parsing EvtGen or
  DecFiles decay descriptors, constructing decay chains programmatically,
  visualizing particle decay trees, or converting between decay descriptor
  formats for use with generator studies.
---

# decaylanguage

## Overview

decaylanguage is a Scikit-HEP library for working with particle decay
descriptors. It parses EvtGen `.dec` files, the Belle II DecFiles format, and
decay chain strings into Python objects. It is used in generator-level studies
and decay chain validation, particularly for B-physics and charm analyses where
complex multi-body decays must be described and inspected.

## When to Use

- Parsing EvtGen `.dec` files to inspect or modify decay branching fractions
- Constructing a decay chain description programmatically (e.g. for generator
  job options)
- Visualizing a decay tree as a graph for documentation or cross-checks
- Converting decay descriptors for input to EvtGen, Pythia, or other generators

## Canonical Patterns

### Parse a DecFile / EvtGen .dec file

```python
from decaylanguage import DecFileParser

parser = DecFileParser("my_decays.dec")
parser.parse()

# List all decays defined
for particle_name in parser.list_decay_mothers():
    print(particle_name)

# Get decay modes for a specific particle
modes = parser.list_decay_modes("B0")
for mode in modes:
    print(mode)   # tuple: (branching_fraction, [daughter_names], model, model_params)
```

### Build a decay chain

```python
from decaylanguage import DecayChain, DecayMode

# Construct a decay chain: B+ → D0 pi+, D0 → K- pi+
dm_b = DecayMode(0.069, "D0 pi+", model="PHSP")
dm_d = DecayMode(0.038, "K- pi+", model="PHSP")

chain = DecayChain("B+", {"B+": dm_b, "D0": dm_d})
```

### Visualize a decay chain

```python
from decaylanguage import DecayChainViewer

viewer = DecayChainViewer(chain.to_dict())
viewer.graph.render("decay_chain", format="pdf", cleanup=True)  # uses graphviz
```

### Work with decay descriptor strings

```python
from decaylanguage import DecayChainViewer

# Descriptor string as used in Gaudi/Gauss job options
descriptor = "[B0 -> (D- -> K+ pi- pi-) pi+]cc"
# Parse and display
```

## Gotchas

- **Requires graphviz** for visualization: `pip install graphviz` and the
  `graphviz` system binary must be in `PATH`.
- **EvtGen model names are not validated**: decaylanguage parses the syntax; it
  does not check whether the model name is a valid EvtGen model.
- **Branching fractions are not automatically normalized**: if you modify a
  `.dec` file, ensure the sum of BFs for each particle equals 1.0 (or the
  generator will complain).

## Interop

- **particle**: `decaylanguage` uses `particle` internally to resolve PDG IDs
  from names.
- **pyhepmc**: Use `decaylanguage` to verify decay chain structure against
  pyhepmc truth records.

## Docs

https://scikit-hep.org/decaylanguage/
