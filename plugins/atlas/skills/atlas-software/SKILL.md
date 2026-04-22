---
name: atlas-software
description: >-
    Use when a question involves ATLAS software concepts: Athena framework,
    event data model, CP algorithms, derivation formats (DAOD), CMake build
    system, CVMFS software releases, analysis releases, ASG tools, or any
    ATLAS-internal software infrastructure. This skill routes to the right
    resource or subagent; for deep lookup delegate to atlas-docs-expert.
---

# ATLAS Software Orientation

## Overview

This skill is a routing map for ATLAS software questions. For any topic below, the authoritative source is the hosted documentation at **https://atlas-software.docs.cern.ch/**. For deep questions, delegate to the `atlas-docs-expert` subagent which searches the docs and fetches current content.

## Major Concepts and Hosted Links

### Athena Framework
The C++ event processing framework underlying all ATLAS reconstruction and analysis.
- Algorithms, tools, services: https://atlas-software.docs.cern.ch/docs/AthenaFramework/
- `AthAnalysisAlgorithm` for analysis: https://atlas-software.docs.cern.ch/docs/AthenaFramework/

### Event Data Model (EDM)
How physics objects are stored in xAOD files.
- xAOD EDM overview: https://atlas-software.docs.cern.ch/docs/XAOD/
- Container types (`xAOD::JetContainer`, `xAOD::ElectronContainer`, etc.)
- Auxiliary stores and decorations (`SG::AuxElement::Decorator<T>`)
- Reading with `SG::ReadHandle<T>` and `SG::WriteHandle<T>`

### CP Algorithms (Combined Performance)
Recommended tools for object calibration, scale factors, and systematic uncertainties.
- CP algorithm overview: https://atlas-software.docs.cern.ch/docs/CPAlgorithms/
- Each physics object has a group-recommended WP and tool:

| Object | CP tool interface | Recommended WP |
|---|---|---|
| Jets | `IJetCalibrationTool`, `IJetUncertaintiesTool` | AntiKt4EMPFlow |
| Electrons | `IEgammaCalibrationAndSmearingTool` | TightLH + gradient iso |
| Muons | `IMuonCalibrationAndSmearingTool` | Medium + FCLoose iso |
| b-jets | `IBTaggingEfficiencyTool` | DL1dv01 77% |
| MET | `IMETMaker` | Tight/Loose |
| Taus | `ITauSmearingTool` | Medium |

### Derivation Formats (DAOD)
Slimmed xAOD files produced by the ATLAS derivation framework.
- Derivation framework: https://atlas-software.docs.cern.ch/docs/DerivationFramework/
- **DAOD_PHYSLITE**: primary analysis format — smaller, CP-recommended variables pre-applied
- **DAOD_PHYS**: full DAOD — use when PHYSLITE lacks required variables
- Specialized: DAOD_BPHY (B-physics), DAOD_EGAM (egamma), DAOD_JETM (jets), HIGG* (Higgs)
- Check available variables: `checkxAOD.py file.pool.root`

### ASG Tools (Analysis Software Group)
Dual-use tools that work both in Athena and standalone.
- ASG tool framework: https://atlas-software.docs.cern.ch/docs/ASGTools/
- `AsgTool` base class — lighter than Gaudi tools, works in AnalysisBase
- Property system: `declareProperty("Name", m_prop = default, "Description")`

### CMake Build System
- Package structure: https://atlas-software.docs.cern.ch/docs/CMakeBuild/
- `atlas_subdir(PackageName)` declares the package
- `atlas_depends_on_subdirs(...)` declares dependencies
- Build: `cmake -DATLAS_BUILD_PACKAGE=PackageName ../source && make`

### CVMFS and Software Releases
- Software at: `/cvmfs/atlas.cern.ch/repo/sw/software/`
- Setup: `asetup AthAnalysis,25.2.X` or `asetup AnalysisBase,25.2.X`
- Run 3 analysis recommendation: **AnalysisBase 25.2.X** for standalone analysis
- Run 2 legacy: **AthAnalysis 22.2.X** for Athena-based analysis
- Release notes: https://atlas-software.docs.cern.ch/docs/Releases/

### Analysis Releases (for non-Athena Python workflows)
- TopCPToolkit: wraps CP algorithms for NTuple production → `atlas:topcptoolkit`
- FastFrames: RDataFrame-based → `atlas:fastframes`
- coffea + uproot: no Athena dependency → `atlas:coffea`, `atlas:uproot`

## When to Go Deeper

For any topic above, delegate to the **`atlas-docs-expert` subagent**:
- It searches the local docs mirror to locate the relevant page
- Fetches current content from the hosted site
- Provides specific code examples from the official docs

## Common Entry Points

| Question type | Start here |
|---|---|
| "How do I set up a CP tool in Athena?" | `atlas-docs-expert` |
| "What object collection name do I use in PHYSLITE?" | `atlas-docs-expert` |
| "How do I build my ATLAS package?" | `atlas-docs-expert` |
| "What framework for my analysis?" | `atlas:topcptoolkit`, `atlas:fastframes`, `atlas:coffea` |
| "How do I find my dataset?" | `atlas-data-explorer` |
| "How do I fit my workspace?" | `atlas-stats-expert` |
