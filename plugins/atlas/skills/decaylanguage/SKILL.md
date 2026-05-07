---
name: decaylanguage
description: >-
  Use when working with particle decay chains in Python: parsing EvtGen or
  DecFiles `.dec` decay descriptors with DecFileParser, building DecayChain and
  DecayMode objects programmatically, visualizing decay trees with
  DecayChainViewer, computing visible branching fractions, or converting AmpGen
  amplitude models to GooFit format. Also use when looking up LHCb or Belle II
  bundled decay tables, handling charge-conjugate decays, or filtering decay
  chains by minimum effective branching fraction.
---

# decaylanguage

## Overview

`decaylanguage` is a Scikit-HEP library for working with particle decay
descriptors. It parses EvtGen `.dec` files (LHCb and Belle II formats) into
Python objects, lets you build and inspect decay chains programmatically, and
renders them as Graphviz diagrams. It is most commonly used in generator-level
studies and decay chain validation for B-physics and charm analyses.

## Key Concepts

- **DecFile / `.dec` format**: EvtGen decay descriptor format. Each block is
  `Decay <particle>\n  <BF> <daughters> <model> <params>;\nEnddecay`.
- **`DecFileParser`**: parses one or more `.dec` files (or a raw string) into an
  internal Lark parse tree and exposes query methods. Particle names use
  **EvtGen conventions**, not PDG (e.g. `D*+`, `K_S0`, `B0`).
- **`DecayMode`**: one decay mode — branching fraction + `DaughtersDict` +
  optional model metadata.
- **`DaughtersDict`**: a `Counter[str]` mapping daughter names to
  multiplicities. Accepts a dict, list, or space-separated string.
- **`DecayChain`**: a tree of `DecayMode` objects rooted at a mother particle.
  The mother **must** be a key in the `decays` dict.
- **`DecayChainViewer`**: wraps a `DecayChain` or the dict returned by
  `build_decay_chains()` and renders it via `graphviz`.
- **Bundled data**: the package ships `DECAY_LHCB.DEC` and `DECAY_BELLE2.DEC`.
  Access them via `from decaylanguage.data import basepath`.

## Canonical Patterns

### Parse a bundled LHCb decay file

```python
from decaylanguage import DecFileParser
from decaylanguage.data import basepath

parser = DecFileParser(basepath / "DECAY_LHCB.DEC")
parser.parse()

# List all mother particles with defined decays
parser.list_decay_mother_names()[:10]

# Get daughter name lists for each decay mode of D*+
modes = parser.list_decay_modes("D*+")  # list[list[str]]

# Pretty-print branching fractions and models
parser.print_decay_modes("D*+")
```

### Parse your own .dec file

```python
parser = DecFileParser("my_decays.dec")
parser.parse()
```

### Parse a .dec snippet inline

```python
dec_text = """
Decay D*+
  0.677   D0  pi+   PHSP;
  0.307   D0  pi+   pi0   PHSP;
Enddecay
"""
parser = DecFileParser.from_string(dec_text)
parser.parse()
```

### Build a full nested decay chain (primary workflow)

`build_decay_chains()` is the main entry point for full analysis: it recursively
expands all sub-decays and returns a nested dict that both
`DecayChain.from_dict()` and `DecayChainViewer` understand.

```python
# Build the full nested chain dict for D*+
chain_dict = parser.build_decay_chains("D*+")

# Stop at stable particles (don't recurse into pi0)
chain_dict = parser.build_decay_chains("D*+", stable_particles=["pi0"])

# Prune negligible paths (< 1% effective BF)
chain_dict = parser.build_decay_chains("D*+", minimum_effective_bf=0.01)
```

### Construct a DecayChain programmatically

```python
from decaylanguage import DecayChain, DecayMode

dm_dst = DecayMode(0.677, "D0 pi+", model="PHSP")
dm_d0  = DecayMode(0.038, "K- pi+", model="PHSP")

# Mother must be a key in the decays dict
dc = DecayChain("D*+", {"D*+": dm_dst, "D0": dm_d0})

print(dc.bf)          # top-level BF: 0.677
print(dc.visible_bf)  # product of all BFs down the chain
print(dc.to_string()) # compact: "D*+ -> (D0 -> K- pi+) pi+"
dc.print_as_tree()    # ASCII tree
```

### Build a DecayChain from parser output

```python
from decaylanguage import DecayChain

chain_dict = parser.build_decay_chains("D*+")
dc = DecayChain.from_dict(chain_dict)
```

### Visualize a decay chain

`DecayChainViewer` accepts either a `DecayChain` object or the dict returned by
`build_decay_chains()`.

```python
from decaylanguage import DecayChainViewer

# From a DecayChain object
dcv = DecayChainViewer(dc)

# In Jupyter: just evaluate dcv — it renders SVG inline
dcv

# Save to file (requires graphviz binary in PATH)
dcv.graph.render("decay_chain", format="pdf", cleanup=True)

# Show effective BF on leaf nodes
dcv = DecayChainViewer(chain_dict, show_effective_bf=True)
```

### DaughtersDict usage

```python
from decaylanguage import DecayMode
from decaylanguage.decay import DaughtersDict

dd = DaughtersDict("K+ pi- pi- pi0")   # from string
dd = DaughtersDict(["K+", "pi-", "pi-", "pi0"])  # from list
dd = DaughtersDict({"K+": 1, "pi-": 2, "pi0": 1})  # from dict

dm = DecayMode(0.0938, dd, model="D_DALITZ")
print(dm.daughters.to_string())  # "K+ pi- pi- pi0"
```

### Custom EvtGen models not yet in decaylanguage

```python
parser.load_additional_decay_models("MY_CUSTOM_MODEL")
parser.parse()
```

### Amplitude model conversion (AmpGen → GooFit)

```bash
python -m decaylanguage.goofit models/DtoKpipipi_v2.txt > output.cu
```

```python
from decaylanguage.modeling.amplitudechain import AmplitudeChain

lines = AmplitudeChain.read_ampgen("models/DtoKpipipi_v2.txt")
```

## Gotchas

- **EvtGen names, not PDG names**: all particle names default to EvtGen
  convention (`K_S0`, `D*+`, `anti-B0`). Pass `pdg_name=True` to methods like
  `list_decay_modes()` to use PDG names instead.
- **`list_decay_modes()` returns daughter name lists only**: it returns
  `list[list[str]]` — no BFs or models. Use `print_decay_modes()` to inspect
  BFs, or `build_decay_chains()` for the full structured data.
- **Mother must be in the `decays` dict**: `DecayChain("D*+", {...})` raises
  `RuntimeError` if `"D*+"` is not a key in the second argument.
- **Graphviz system binary required**: `pip install graphviz` installs the
  Python bindings, but the `graphviz` executable must also be in `PATH`
  (`brew install graphviz` / `apt install graphviz`).
- **BFs are not auto-normalized**: if you modify modes, ensure each particle's
  BF sum equals 1.0 — EvtGen will complain otherwise.
- **EvtGen model names are not validated**: decaylanguage parses syntax only; it
  does not check whether a model name is actually known to EvtGen.
- **Charge conjugate decays are included by default**: `parser.parse()` sets
  `include_ccdecays=True`. Pass `include_ccdecays=False` to suppress them.

## Interop

- **particle**: used internally to resolve PDG IDs from EvtGen names; import
  `particle.Particle` alongside decaylanguage for cross-checks.
- **pyhepmc**: use decaylanguage to verify decay chain topology against HepMC
  truth records from simulation.
- **zfit / phasespace**: `DecayMode` metadata accepts a `zfit=` keyword for
  passing phasespace model hints, e.g.
  `DecayMode(0.5, "K+ K-", zfit={"B0": "gauss"})`.

## Docs

https://scikit-hep.org/decaylanguage/
