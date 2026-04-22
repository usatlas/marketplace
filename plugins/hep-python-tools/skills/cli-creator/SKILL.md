---
name: cli-creator
description: >-
  Use when building a Python command-line interface with Typer: adding arguments
  and options to a script, creating subcommands, wiring an entry point into
  pyproject.toml, validating CLI inputs with callbacks, or adding a CLI layer to
  an existing analysis script or HEP workflow.
---

# CLI Creator

## Overview

Typer builds Python CLIs from type-annotated functions with minimal boilerplate.
It auto-generates `--help`, handles type coercion, and integrates with Rich for
pretty output. For HEP analysis scripts, use Typer for any script that takes
more than one or two parameters.

## When to Use

- Adding a proper CLI to an analysis script (dataset name, nfiles, output dir,
  etc.)
- Creating multi-subcommand tools (e.g., `myscript process`, `myscript plot`)
- Exposing a package entry point in `pyproject.toml`
- Replacing `argparse` or manual `sys.argv` parsing
- Combining with PEP 723 standalone scripts (invoke
  `hep-python-tools:standalone-script`)

## Key Concepts

| Concept                           | Notes                                                                |
| --------------------------------- | -------------------------------------------------------------------- |
| `typer.Argument`                  | Positional — required unless `default=...`                           |
| `typer.Option`                    | Keyword (`--name`) — always has a default                            |
| `Annotated[T, typer.Option(...)]` | **Modern syntax** (Typer ≥ 0.9) — preferred                          |
| `pathlib.Path`                    | Use as type annotation for file/dir args — Typer validates existence |
| `typer.Typer()` + `app()`         | Multi-command entry point                                            |

## Canonical Patterns

**Single-command script (most common in analysis)**:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "rich"]
# ///
from __future__ import annotations
from pathlib import Path
from typing import Annotated
import typer

app = typer.Typer()

@app.command()
def main(
    dataset: Annotated[str, typer.Argument(help="Rucio dataset name")],
    output: Annotated[Path, typer.Option(help="Output directory")] = Path("output"),
    nfiles: Annotated[int, typer.Option(help="Max files (0 = all)")] = 1,
    verbose: Annotated[bool, typer.Option("--verbose/--no-verbose")] = False,
) -> None:
    """Process ATLAS data from DATASET and write histograms to OUTPUT."""
    output.mkdir(parents=True, exist_ok=True)
    if verbose:
        typer.echo(f"Processing {dataset}, max_files={nfiles or 'all'}")
    # ... analysis code ...

if __name__ == "__main__":
    app()
```

**Multi-command tool**:

```python
app = typer.Typer()

@app.command()
def process(dataset: str, output: Path = Path(".")):
    """Run the analysis and write NTuples."""
    ...

@app.command()
def plot(input_dir: Path, output: Path = Path("plots")):
    """Read NTuples and produce plots."""
    ...
```

**pyproject.toml entry point**:

```toml
[project.scripts]
my-analysis = "my_package.cli:app"
```

**Optional path argument with existence check**:

```python
input_file: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False)]
```

**Enum for restricted choices**:

```python
from enum import Enum
class Backend(str, Enum):
    xaod = "xaod"
    uproot = "uproot"

backend: Annotated[Backend, typer.Option()] = Backend.xaod
```

## Gotchas

- **Use `Annotated[T, typer.Option(...)]` not `= typer.Option(...)`**: The old
  signature still works but is deprecated in Typer ≥ 0.9 and will be removed.
- **`bool` flags auto-generate pairs**:
  `Annotated[bool, typer.Option("--flag/--no-flag")]` creates two flags. If you
  only write `bool` with no `Option(...)`, Typer makes `--flag` only (sets True
  if present).
- **`Path` validation happens at parse time**: If you annotate with `Path` and
  add `exists=True`, Typer validates before your function runs — handy but may
  surprise you in tests.
- **`app()` not `typer.run(fn)`**: For multi-command tools, always define a
  `Typer()` app. `typer.run()` is only for single-function one-liners.
- **Rich output**: `typer.echo()` wraps `print()`; for richer output use
  `from rich import print` or `typer.style()`.

## Interop

- **standalone-script**: Combine the PEP 723 header with a Typer app for
  self-contained analysis scripts that anyone can run with `uv run --script`
- **pixi / hatch**: Entry points declared in `pyproject.toml` are available
  after `pixi install` or `hatch env create`
- **Rich**: Typer uses Rich under the hood; `from rich.progress import track`
  adds progress bars with no extra config

## Docs

https://typer.tiangolo.com/
