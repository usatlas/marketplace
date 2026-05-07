# TopCPToolkit Troubleshooting

## Common warning messages

### Muon trigger efficiency map warning

```
ToolSvc.MuonTrigEff WARNING Could not find what you are looking for in the
efficiency map. The trigger you are looking for, year and mc are not consistent,
or the trigger is unavailable in this data period. Returning efficiency = 0.
```

**Cause**: Mismatch between Run 2 and Run 3 muon ID working-point
recommendations, or a trigger chain that is unavailable for the specified data
period.

**Fix**: Check that your muon ID WP is supported — see
[MuonCP docs](https://atlas-mcp.docs.cern.ch/guidelines/release22/index.html#wps-for-run3).
Also verify the trigger chains in `triggerChainsPerYear` match the actual
data-taking years of your sample.

### `TruthParticleFixerAlg` / `TruthVertexFixerAlg` flood

**Cause**: Running on a newer p-tag (>p7017) derivation where `barcode()` has
been removed from truth particles in favour of `uid()`.

**Fix**: Safe to ignore. Disable the warnings by setting the relevant flag in
`CommonServices`.

## Common crashes

### `Exactly two leptons are required to check whether the event is OS or SS!`

**Cause**: The `OS` or `SS` keyword appears in an `EventSelection` that does not
enforce exactly two leptons.

**Fix**: Add the appropriate `EL_N` / `MU_N` / `SUM_EL_N_MU_N` cuts to ensure
exactly two leptons before the `OS`/`SS` check.

### `Failed to retrieve NSW hits!`

```
MuonSelectionAlg_loose...FATAL Failed to retrieve NSW hits!! If you're using
DxAODs (with smart slimming for muons), you should use p-tags >= p5834.
```

**Fix**: Update to a more recent p-tag, or set `ExcludeNSWFromPrecisionLayers`
to `True` in `MuonSelectionTool` config (only for testing — not for physics).

### `Unrecognised FTAG MC-to-MC generator setup None, aborting.`

**Cause**: Sample metadata is missing or corrupt.

**Fix**: Check the `GeneratorInfo` field in the TCT flags printout at the top of
the job log. If it is `None`, the derivation metadata is the issue. Report it.

### `ValueError: invalid generator type`

**Cause**: The detected generator version is not supported by the current FTAG
MC-to-MC recommendations.

**Fix**: Set a supported generator version manually via the `generator` property
in the `Jets.FlavourTaggingEventSF` block. Contact your FTAG group liaison for
the correct value for your sample.

### `Unknown trigger 'my_jet_trigger' found while parsing trigger combination`

**Cause**: Jet triggers are not supported by
`TrigGlobalEfficiencyCorrectionTool` for matching/scale factors. Passing jet
triggers in `triggerChainsPerYear` causes TCT to attempt setting up matching,
which fails.

**Fix**: For jet triggers that need only selection (not matching/SFs), use
`triggerChainsForSelection` instead of `triggerChainsPerYear`, or set
`noGlobalTriggerEff: True`.

### `Sample is FastSim but no AF3 calibration is available yet`

**Cause**: Running on an AF3 (fast simulation) sample with Egamma
recommendations that do not yet include AF3.

**Fix**: As a temporary workaround, set `forceFullSimConfig: True` in the
electrons block. This is not correct for physics — use only until AF3
recommendations are available.

### `ValueError: No CDI MCMC map available for generator: xxx with GN2v01`

**Cause**: The generator type in your sample metadata is not supported by the
current FTAG calibration data interface for the chosen tagger.

**Fix**: Set the `generator` option in `Jets.FlavourTaggingEventSF` to a
supported generator string. See the
[MCMCGeneratorHelper](https://acode-browser1.usatlas.bnl.gov/lxr/source/athena/PhysicsAnalysis/JetTagging/JetTagPerformanceCalibration/CalibrationDataInterface/python/MCMCGeneratorHelper.py)
for the list of supported strings.

## Unexpected output

### No events pass the GRL selection in MC

**Cause**: A metadata issue in the derivation causes TCT to treat the MC sample
as data.

**Symptom**: The `SimFlavour` field may be missing (observed in p5631). Events
pass GRL for data but fail for this MC.

**Fix**: Report the issue. As a workaround, inspect the flags printout
(`metaConfig.pretty_print`) to confirm what TCT detected.

### Systematically-varied vector branches contain default values

This is expected behaviour in the single-TTree format. For each systematic, some
objects may fail selection (e.g. JVT, overlap removal). Those entries are still
present in the vector but filled with a default value. **Always apply the
corresponding `object_select_NAME_%SYS%` flag** before using object kinematics.

### Objects not sorted by pT

Also expected: CP algorithms cannot preserve pT ordering across systematics.
Sort offline if needed (e.g.
`jets = jets[ak.argsort(jets.pt, ascending=False)]`).

## Migrating from AnalysisTop

### Where is `top-xaod`?

AnalysisTop (`top-xaod`) is compiled into AnalysisBase and runs without
compilation. TCT requires cloning and compiling from source — there is no
equivalent turnkey binary.

### Output format differences

TCT produces a **single TTree** for all systematics, not per-systematic trees.
Each systematically-varying quantity has a `%SYS%`-suffixed branch. Objects have
`object_select_NAME_%SYS%` boolean flags that must be applied. This format does
not work with `TTree::Draw` — use FastFrames, uproot, or coffea instead.

### Equivalent of `CustomEventSaver`

Write a `ConfigBlock` in Python and register it with `AddConfigBlocks`. For a
single large algorithm, follow the
[AnalysisSWTutorial](https://atlas-software.docs.cern.ch/analysis/analysis_tutorial/AnalysisSWTutorial/alg_basic_algorithm/)
and add it via `AddConfigBlocks`. Split complex savers into separate
single-purpose algorithms — it makes them easier to debug and reuse.

### Equivalent of `CustomObjectLoader`

Standard CP algorithms cover most object-definition needs. If you need a
radically non-standard object type, discuss it with your PA group first — most
cases can be handled by configuring the existing `WorkingPoint` options.

## Debugging tips

### Enable verbose output for a specific algorithm

In your Python analysis module:

```python
myAlgo = config.createAlgorithm('CP::SomeAlg', 'myName')
myAlgo.OutputLevel = 2  # 2=DEBUG, 1=VERBOSE, 3=INFO
```

### Inspect sample metadata

```bash
meta-reader -m peeker --hideContentList --hideTrigger <file.pool.root>
```

### Run interactively (AthAnalysis only)

```bash
runTop_el.py -i inputs.txt -o output --interactive
# Then at the prompt:
# >>> self.getEventAlgo("NTupleMaker").OutputLevel = 2
# >>> exit()
```
