---
name: standalone-script
description: >-
  Use when generating a self-contained Python script with PEP 723 inline
  dependency metadata: writing the script block header, making a script runnable
  with uv run --script, combining with a Typer CLI for argument handling, or
  creating a one-off analysis tool that should not live inside a package and
  must declare its own dependencies inline.
---

# Standalone Script

## Overview

PEP 723 (Python 3.12+, backported via `uv`) lets a `.py` file declare its own
dependencies in a `# /// script` comment block. Running the script with
`uv run --script <file>` automatically installs deps into a temporary
environment. This is the right pattern for one-off analysis scripts, quick
tools, and anything you want to share as a single file.

## When to Use

- Writing a one-off analysis script that doesn't belong in a package
- Creating a self-contained tool to share with collaborators (single file, no
  `pip install` instructions)
- Combining with `hep-python-tools:cli-creator` for a proper CLI layer
- Replacing an ad-hoc `requirements.txt` + `python script.py` workflow

## Key Concepts

| Concept                           | Notes                                                      |
| --------------------------------- | ---------------------------------------------------------- |
| `# /// script` block              | Must be at the TOP of the file, before any imports         |
| `requires-python`                 | Minimum Python version for the script                      |
| `dependencies`                    | PEP 508 dependency specs — same syntax as `pyproject.toml` |
| `uv run --script <file>`          | Installs deps and runs in one step                         |
| `uv run --script --frozen <file>` | Skip re-resolution (faster for CI)                         |

## Canonical Pattern

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "uproot>=5",
#   "awkward>=2",
#   "hist>=2.7",
#   "vector>=1",
#   "typer>=0.9",
#   "mplhep",
# ]
# ///
"""Fetch jet pT from a local ROOT file and plot a histogram."""
from __future__ import annotations
from pathlib import Path
from typing import Annotated

import awkward as ak
import hist
import mplhep
import matplotlib.pyplot as plt
import typer
import uproot
import vector

vector.register_awkward()
mplhep.style.use("ATLAS")

app = typer.Typer()

@app.command()
def main(
    root_file: Annotated[Path, typer.Argument(help="Input ROOT file", exists=True)],
    tree: Annotated[str, typer.Option(help="TTree name")] = "reco",
    output: Annotated[Path, typer.Option(help="Output plot")] = Path("jet_pt.pdf"),
) -> None:
    """Plot jet pT distribution from ROOT_FILE."""
    with uproot.open(root_file) as f:
        jets = f[tree].arrays(["jet_pt", "jet_eta"], library="ak")

    selected = jets[ak.num(jets.jet_pt) >= 1]
    pts = ak.to_numpy(ak.flatten(selected.jet_pt)) / 1000  # MeV → GeV

    h = hist.Hist(hist.axis.Regular(50, 0, 500, name="pt", label=r"$p_T$ [GeV]"))
    h.fill(pt=pts)

    fig, ax = plt.subplots()
    h.plot1d(ax=ax)
    ax.set_ylabel("Events")
    fig.savefig(output)
    typer.echo(f"Saved: {output}")

if __name__ == "__main__":
    app()
```

**Run it**:

```bash
uv run --script my_analysis.py data.root --output jet_pt.pdf
```

**For testing with fewer files**:

```bash
uv run --script my_analysis.py data.root --nfiles 1
```

## Pinning Dependencies

For reproducibility in scripts that will be shared or run in CI:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "uproot==5.3.9",
#   "awkward==2.6.5",
# ]
# ///
```

Or use a lock-style spec comment and `--frozen` for CI:

```bash
uv run --script --frozen analysis.py input.root
```

## Gotchas

- **`# /// script` must be at the very top**: Before any imports, docstring
  even. If it's not the first non-blank content, `uv` won't find it.
- **Comments inside the block**: The `#` is part of the syntax — each line in
  the block starts with `# `. Remove the `#` and uv ignores it.
- **`uv run --script` re-resolves every time**: This is slow for packages with
  many deps. Use `--frozen` in CI or when you know the environment is stable.
- **Not the same as `uv run <file>`**: `--script` flag tells uv to treat the
  file as a PEP 723 script; without it, uv runs the file in the current
  project's virtualenv.
- **Python version**: The `requires-python` constraint is enforced — if your
  system Python is older, uv downloads a matching interpreter automatically (if
  using `uv` with Python management enabled).
- **Shebang alternative**: You can add `#!/usr/bin/env -S uv run --script` as
  the first line for a truly self-running script on Unix.

## Interop

- **cli-creator**: Combine PEP 723 header + Typer app for a complete
  self-contained CLI script
- **uv**: `uv run --script` is the primary runner; also works with `pixi run`
- **pixi**: `pixi run python script.py` works if deps are in the pixi
  environment; PEP 723 is not needed in that case

## Docs

- PEP 723:
  https://packaging.python.org/en/latest/specifications/inline-script-metadata/
- uv scripts guide: https://docs.astral.sh/uv/guides/scripts/
