# TRExFitter: Worked Example (ttH→bb Search)

Read this reference when the user wants a complete, realistic multi-region,
multi-sample config to adapt (regions, samples, NormFactors, and systematics
wired together end to end), rather than the minimal skeleton in SKILL.md.

## Worked Example: ttH→bb Search (2 regions, 3 samples)

```
Job: "ttH_bb"
  CmeLabel: "13 TeV"
  POI: "mu_ttH"
  ReadFrom: HIST
  HistoPath: "hists"
  OutputDir: "output/ttH_bb"
  LumiLabel: "139 fb^{-1}"
  Lumi: 139.0
  MCstatThreshold: 0.05
  SystPruningShape: 0.02
  SystPruningNorm: 0.01

Fit: "Fit_ttH"
  FitType: SPLUSB
  FitRegion: CRSR
  FitBlind: FALSE
  POIAsimov: 1
  UseMinos: mu_ttH

Limit: "Limit_ttH"
  LimitType: ASYMPTOTIC

Significance: "Sig_ttH"
  SignificanceType: ASYMPTOTIC
  POIAsimov: 1

Region: "SR_lj"
  Type: SIGNAL
  HistoName: "h_mbb"
  Label: "SR (l+jets)"
  ShortLabel: "SR"
  VariableTitle: "m_{bb} [GeV]"

Region: "CR_ttbar"
  Type: CONTROL
  HistoName: "h_mbb"
  Label: "t#bar{t} CR"
  ShortLabel: "CR"

Sample: "ttH"
  Type: SIGNAL
  HistoFile: "ttH125"
  FillColor: 632
  NormalizedByTheory: TRUE

Sample: "ttbar"
  Type: BACKGROUND
  HistoFile: "ttbar"
  FillColor: 4

Sample: "Wjets"
  Type: BACKGROUND
  HistoFile: "Wjets"
  FillColor: 5

Sample: "Data"
  Type: DATA
  HistoFile: "data"

NormFactor: "mu_ttH"
  Title: "#mu_{ttH}"
  Nominal: 1
  Min: -10
  Max: 20
  Samples: ttH

NormFactor: "mu_ttbar"
  Title: "#mu_{t#bar{t}}"
  Nominal: 1
  Min: 0
  Max: 5
  Samples: ttbar

Systematic: "Lumi"
  Title: "Luminosity uncertainty"
  Type: OVERALL
  OverallUp: 0.017
  OverallDown: -0.017
  Samples: ttH, ttbar, Wjets

Systematic: "JES"
  Title: "Jet energy scale"
  Type: HISTO
  HistoNameUp: "h_mbb_JES_up"
  HistoNameDown: "h_mbb_JES_dn"
  Samples: ttH, ttbar, Wjets
  Symmetrisation: TWOSIDED
  Smoothing: 40

Systematic: "bTagB"
  Title: "b-tagging (b-jet eff.)"
  Type: HISTO
  HistoNameUp: "h_mbb_bTag_up"
  HistoNameDown: "h_mbb_bTag_dn"
  Samples: ttH, ttbar, Wjets
  Symmetrisation: TWOSIDED

Systematic: "ttbar_XS"
  Title: "t#bar{t} cross section"
  Type: OVERALL
  OverallUp: 0.06
  OverallDown: -0.06
  Samples: ttbar
```

Run the full pipeline:

```bash
trex-fitter h  config/ttH_bb.config
trex-fitter wd config/ttH_bb.config
trex-fitter f  config/ttH_bb.config
trex-fitter prl config/ttH_bb.config
trex-fitter s  config/ttH_bb.config
```

Post-fit outputs land in `output/ttH_bb/`: `Fits/`, `Plots/`, `Tables/`,
`Pulls/`, `Limits/`, `Significance/`.
