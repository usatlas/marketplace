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

## Plugins

### `analysis-facilities`

Skills for USATLAS Analysis Facilities (UChicago AF, BNL AF, SLACK AF).

| Skill         | Description                                                                                 |
| ------------- | ------------------------------------------------------------------------------------------- |
| `uchicago-af` | HTCondor batch, JupyterLab, XCache, Rucio, ServiceX, Coffea-Casa, Triton at af.uchicago.edu |

More facility skills (BNL, SLACK) coming soon.

---

### `atlas`

ATLAS analysis plugin covering the full workflow from raw data to publication.

**Subagents** (invoked automatically or via `Agent(subagent_type=...)`):

| Subagent                   | Purpose                                                                            |
| -------------------------- | ---------------------------------------------------------------------------------- |
| `atlas-analysis-architect` | Designs end-to-end analysis pipelines; produces a structured specification         |
| `atlas-analysis-coder`     | Writes Python analysis code (uproot, ServiceX, coffea, hist)                       |
| `atlas-docs-expert`        | Answers ATLAS software questions; cites hosted docs at atlas-software.docs.cern.ch |
| `atlas-stats-expert`       | Statistical model design: pyhf/cabinetry workspaces, TRExFitter configs, limits    |
| `atlas-data-explorer`      | Dataset and file discovery via Rucio, AMI, and ATLAS Open Data MCPs                |

**Skills:**

| Category    | Skills                                                                            |
| ----------- | --------------------------------------------------------------------------------- |
| Orientation | `atlas-software`                                                                  |
| Statistics  | `pyhf`, `cabinetry`, `pyhs3`, `histfitter`, `trexfitter`, `roounfold`             |
| Frameworks  | `topcptoolkit`, `fastframes`                                                      |
| Data access | `servicex`, `analysis-spec-builder`, `fsspec-xrootd`                              |
| Core tools  | `uproot`, `awkward`, `coffea`, `hist`, `vector`                                   |
| Scikit-HEP  | `iminuit`, `fastjet`, `particle`, `hepunits`, `decaylanguage`, `pyhepmc`, `pylhe` |
| Interop     | `cpp-bindings`                                                                    |

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

Generic Python tooling skills for HEP workflows.

| Skill               | Description                                                     |
| ------------------- | --------------------------------------------------------------- |
| `cli-creator`       | Typer CLI scripts with modern `Annotated` syntax                |
| `standalone-script` | PEP 723 inline-metadata scripts runnable with `uv run --script` |

---

## Repository Layout

```
plugins/
  analysis-facilities/
    .claude-plugin/plugin.json
    skills/uchicago-af/SKILL.md
  atlas/
    .claude-plugin/plugin.json
    .mcp.json
    agents/                    # 5 subagents
    skills/                    # 25 skills
    VENDORED-LICENSES.md       # BSD 3-Clause attribution for upstream content
  hep-python-tools/
    .claude-plugin/plugin.json
    skills/                    # 2 skills
.claude-plugin/marketplace.json
```

## Contributing

Issues and PRs welcome at https://github.com/usatlas/marketplace

## License

MIT — see LICENSE for details. Vendored content from the IRIS-HEP marketplace is
BSD 3-Clause; see `plugins/atlas/VENDORED-LICENSES.md` for full attribution.
