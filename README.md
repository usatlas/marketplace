# USATLAS Analysis Facilities Marketplace

This marketplace provides the **analysis-facilities** plugin for Claude Code,
containing individual skills for each USATLAS Analysis Facility (UChicago, BNL,
SLACK). Each skill provides workflows and guidance for working with
facility-specific batch systems, JupyterLab, data access services, and
specialized tools.

## Installation

### From GitHub

```bash
/plugins marketplace add usatlas/marketplace
```

Then install the `analysis-facilities` plugin from the marketplace.

### Local Installation

If you have this repository cloned locally:

```bash
/plugins marketplace add /path/to/af-docs/af-skills
```

## Plugin Structure

The `analysis-facilities` plugin contains facility-specific skills:

- **uchicago-af** - UChicago ATLAS Analysis Facility (available now)
- **bnl-af** - BNL ATLAS Analysis Facility (coming soon)
- **slac-af** - SLACK ATLAS Analysis Facility (coming soon)

## Available Skills

### uchicago-af

Comprehensive workflow assistant for the UChicago ATLAS Analysis Facility,
including:

- Account setup and SSH access
- HTCondor batch job submission (short and long queues)
- JupyterLab with CPU/GPU resources
- Data access via XCache, Rucio, and CERN EOS
- ServiceX data delivery (Uproot and xAOD)
- Coffea Casa for distributed columnar analysis
- Triton Inference Server for ML model deployment
- Storage management ($HOME, $DATA, $SCRATCH)
- Common troubleshooting scenarios

**Invoke with**: The skill auto-loads when you mention UChicago AF, HTCondor
jobs at UChicago, JupyterLab at af.uchicago.edu, or related services.

## Coming Soon

Additional facility skills will be added to the `analysis-facilities` plugin:

- **bnl-af** - BNL ATLAS Analysis Facility workflows
- **slac-af** - SLACK ATLAS Analysis Facility workflows

## Documentation

Full documentation for USATLAS Analysis Facilities is available at:
https://usatlas.readthedocs.io/projects/af-docs/

## Contributing

This marketplace is maintained alongside the USATLAS Analysis Facilities
documentation. To report issues or suggest improvements:

- GitHub Issues: https://github.com/usatlas/af-docs/issues
- Email: atlas-us-chicago-tier3-admins@cern.ch (UChicago AF)

## License

MIT License - see LICENSE file for details.
