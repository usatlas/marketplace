# xmlAnaWSBuilder Advanced Configurations

Read this reference when importing an externally-built PDF (e.g. from
HistFactory), setting up a counting-experiment channel, or implementing a
blinded-analysis side-band fit.

## Table of Contents

- [External PDF import](#external-pdf-import)
- [Counting experiments](#counting-experiments)
- [Blinded analysis](#blinded-analysis)

## External PDF import

For a pdf-level card that references an externally provided PDF (e.g. one
already built by HistFactory) instead of declaring a `UserDef` model inline:

```xml
<Model Type="External" Input="bkg.root" WSName="combined"
  ModelName="channel_model" ObservableName="obs_x_channel"/>
```

Keep the observable name consistent with HistFactory when importing external
PDFs — renaming it breaks the binned model.

## Counting experiments

```xml
<Channel Name="sr" Type="counting" Lumi="20.3">
  <Data NumData="9" Observable="obs_sr:[0,1]"/>
  <Sample Name="signal" Norm="0.5" ImportSyst=":common:" SharePdf="counting">
  </Sample>
</Channel>
```

- `Type="counting"` creates a `RooUniform` PDF per process.
- `Binning` is always 1 and is ignored if provided.
- `NumData` attribute sets event count directly without a data file.

## Blinded analysis

```xml
<!-- Top-level: enable blinding -->
<Combination ... Blind="true">

<!-- Category-level: specify blinded range -->
<Data ... BlindRange="120,130"/>
```

Events in `BlindRange` are vetoed. Side-band fits use:

```cpp
pdf->createNLL(*data, ..., Range("SBLo,SBHi"), SplitRange())
```

Remove `SBLo` or `SBHi` if the blinded range touches the observable boundary.
