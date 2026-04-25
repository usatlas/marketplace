# USATLAS Marketplace

Claude Code plugin marketplace for ATLAS physics analysis. Three plugins cover
USATLAS Analysis Facilities, the full ATLAS software and analysis stack, and
generic HEP Python tooling.

## Installation

```bash
# From GitHub
/plugins marketplace add usatlas/marketplace

# From a local clone
/plugins marketplace add /path/to/marketplace
```

Then install whichever plugins you need from the marketplace browser.

<!-- UPDATE:START -->

## Plugins

### `analysis-facilities`

Skills for working with USATLAS Analysis Facilities including UChicago, BNL, and
SLAC sites.

**Skills:**

| Skill         | Description                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| `uchicago-af` | Working with the UChicago ATLAS Analysis Facility, submitting HTCondor batch |

---

### `atlas`

ATLAS analysis plugin: grid/catalog MCPs (Rucio, AMI, ATLAS Open Data),
statistics (pyhf, cabinetry, HistFitter, TRExFitter, RooUnfold, pyhs3), analysis
frameworks (TopCPToolkit, FastFrames, ServiceX), Scikit-HEP tools, and ATLAS
software orientation.

**Subagents** (invoked automatically or via `Agent(subagent_type=...)`):

| Subagent                   | Purpose                                                                         |
| -------------------------- | ------------------------------------------------------------------------------- |
| `atlas-analysis-architect` | Designs end-to-end analysis pipelines; produces a structured specification      |
| `atlas-analysis-coder`     | Writes Python analysis code (uproot, ServiceX, coffea, hist)                    |
| `atlas-data-explorer`      | Dataset and file discovery via Rucio, AMI, and ATLAS Open Data MCPs             |
| `atlas-docs-expert`        | Answers ATLAS software questions; cites atlas-software.docs.cern.ch             |
| `atlas-stats-expert`       | Statistical model design: pyhf/cabinetry workspaces, TRExFitter configs, limits |

**Skills:**

| Skill                   | Description                                                                     |
| ----------------------- | ------------------------------------------------------------------------------- |
| `acm`                   | Building ATLAS software with acm (AtlasACM)                                     |
| `analysis-spec-builder` | Producing a structured ATLAS analysis specification document                    |
| `art`                   | Running or writing ART (ATLAS Release Tester) validation tests for ATLAS        |
| `astyle`                | Creating ATLAS publication-quality plots with the official ATLAS ROOT style     |
| `atlantis`              | Visualizing ATLAS detector events with the Atlantis event display               |
| `atlas-containers`      | Running ATLAS software inside containers via setupATLAS -c, choosing between    |
| `atlas-software`        | A question involves ATLAS software concepts                                     |
| `awkward`               | Working with jagged or variable-length arrays in Python HEP analysis            |
| `cabinetry`             | Building an ATLAS statistical analysis with cabinetry                           |
| `centralpage`           | Searching for ATLAS Monte Carlo or data samples                                 |
| `coffea`                | Writing a columnar ATLAS analysis with coffea                                   |
| `cpp-bindings`          | Writing Python bindings for C++ HEP code with nanobind or pybind11              |
| `decaylanguage`         | Working with decay chain descriptions in Python                                 |
| `eiclient`              | Working with the ATLAS Event Index                                              |
| `fastframes`            | You need a supported RDataFrame-based framework to process CP-algorithm NTuples |
| `fastjet`               | Running jet clustering in Python with fastjet or pyjet                          |
| `fsspec-xrootd`         | Accessing ROOT files on EOS, WLCG grid storage, or any XRootD endpoint from     |
| `hepunits`              | Writing unit-safe HEP code in Python                                            |
| `hist`                  | Creating, filling, slicing, or plotting histograms with the scikit-hep hist     |
| `histfitter`            | Setting up or running a HistFitter-based statistical analysis                   |
| `iminuit`               | You need to minimize a scalar cost function in Python using MINUIT2 via iminuit |
| `lcgenv`                | Setting up standalone LCG (CERN SFT) software packages via lcgenv or views:     |
| `managetier3sw`         | Installing, updating, or removing ATLAS software on a local Tier-3 cluster      |
| `mplhep`                | Creating ATLAS publication-quality plots with matplotlib using mplhep           |
| `panda`                 | Submitting ATLAS grid jobs with prun or pathena, monitoring tasks with pbook or |
| `particle`              | Looking up particle properties (mass, charge, PDG ID, lifetime, width) from the |
| `pyhepmc`               | Reading or writing HepMC3 event records in Python                               |
| `pyhf`                  | Building or running a HistFactory statistical model in Python                   |
| `pyhs3`                 | Reading, writing, or validating binned and/or unbinned statistical models in    |
| `pylhe`                 | Reading Les Houches Event (LHE) files in Python                                 |
| `quickfit`              | Fitting a RooWorkspace dataset with quickFit, generating an Asimov dataset with |
| `roounfold`             | Performing statistical unfolding for an ATLAS cross-section measurement:        |
| `servicex`              | Querying ATLAS xAOD data remotely via ServiceX                                  |
| `setupatlas`            | Setting up the ATLAS software environment with setupATLAS or                    |
| `statanalysis`          | Setting up the ATLAS StatAnalysis software release with asetup, choosing the    |
| `topcptoolkit`          | Using TopCPToolkit to process ATLAS DAOD files into analysis NTuples            |
| `trexfitter`            | Setting up or running a TRExFitter statistical analysis                         |
| `uproot`                | Reading or writing ROOT files in Python without a ROOT installation, or when    |
| `vector`                | Computing 4-vector quantities in Python                                         |
| `workspacecombiner`     | Combining multiple RooFit workspaces with workspaceCombiner, editing workspace  |
| `xcache`                | Setting up a local XCache disk caching proxy for XRootD root:// protocol        |
| `xmlanawsbuilder`       | Building a RooFit workspace from XML cards with xmlAnaWSBuilder or XMLReader    |
| `xroofit`               | Building RooFit statistical models with xRooFit, constructing workspaces with   |

**MCP servers** (configured in `plugins/atlas/.mcp.json`):

| Server           | Launch command                          | Purpose                             |
| ---------------- | --------------------------------------- | ----------------------------------- |
| `rucio`          | `pixi exec rucio-mcp serve --read-only` | Dataset and replica discovery       |
| `ami`            | `pixi exec ami-mcp serve`               | AMI metadata (cross-sections, tags) |
| `atlasopenmagic` | `uvx atlasopenmagic-mcp serve`          | ATLAS Open Data catalog             |

**Required environment variables for Rucio MCP:**

```bash
export RUCIO_ACCOUNT=yourusername        # required — no default
export RUCIO_AUTH_TYPE=x509_proxy        # default; or "oidc" / "userpass"
voms-proxy-init --voms atlas             # obtain a valid proxy first
```

---

### `hep-python-tools`

Generic Python tooling skills used across HEP workflows: Typer CLIs with
pixi/uv/Hatch, and PEP-723 standalone scripts.

**Skills:**

| Skill                | Description                                                                 |
| -------------------- | --------------------------------------------------------------------------- |
| `cli-creator`        | Building a Python command-line interface with Typer                         |
| `code-quality-tools` | Setting up code quality tooling for a HEP Python project                    |
| `python-packaging`   | Creating a new Python package, adding pyproject.toml to an existing project |
| `python-testing`     | Writing or configuring tests for a HEP Python project with pytest           |
| `standalone-script`  | Generating a self-contained Python script with PEP 723 inline dependency    |

## Repository Layout

```text
plugins/
  analysis-facilities/
    .claude-plugin/plugin.json
    skills/  # 1 skill
  atlas/
    .claude-plugin/plugin.json
    .mcp.json
    agents/  # 5 subagents
    skills/  # 43 skills
    VENDORED-LICENSES.md
  hep-python-tools/
    .claude-plugin/plugin.json
    skills/  # 5 skills
    VENDORED-LICENSES.md
.claude-plugin/marketplace.json
```

<!-- UPDATE:END -->

## Contributing

Issues and PRs welcome at https://github.com/usatlas/marketplace

## License

MIT — see LICENSE for details. Vendored content from the IRIS-HEP marketplace is
BSD 3-Clause; see `plugins/atlas/VENDORED-LICENSES.md` for full attribution.
