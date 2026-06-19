---
name: astyle
description: >-
  Use when creating ATLAS publication-quality plots with the official ATLAS ROOT
  style macros (atlasrootstyle), applying SetAtlasStyle, placing ATLAS labels
  (Internal, Preliminary, Simulation), using ATLASLabel or myText helper
  functions, or following ATLAS publication plotting conventions in ROOT or
  PyROOT.
---

# ATLAS ROOT Style (astyle)

## Overview

The ATLAS ROOT style macros (`atlasrootstyle`) provide the official
publication-quality plotting style for all ATLAS papers, conference notes, and
internal documents. The package defines consistent fonts, colors, axis labels,
margins, and ATLAS label placement. Available via `lsetup astyle` or directly
from the GitLab repository.

## When to Use

- Creating plots for an ATLAS paper, conference note, or internal document
- Applying the official ATLAS style (fonts, margins, tick marks) to ROOT plots
- Placing "ATLAS", "ATLAS Preliminary", "ATLAS Internal", or other official
  labels on a canvas
- Using helper functions for text, lines, boxes, and marker legends on plots
- Setting up atlasrootstyle in a PyROOT or C++ ROOT macro

## Key Concepts

### Setup

```bash
setupATLAS
lsetup astyle
```

This adds the atlasrootstyle macro directory to the ROOT include path.

### Components

| File              | Purpose                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `AtlasStyle.C/h`  | Main style definitions: font, tick marks, margins                  |
| `AtlasLabels.C/h` | Functions for placing official ATLAS labels on plots               |
| `AtlasUtils.C/h`  | Utility functions: text, boxes, marker legends, TGraph error bands |

### Style Characteristics

- **Font**: Helvetica (ROOT font family 43, size 26 for axis labels)
- **Stat box**: Disabled by default
- **Tick marks**: Drawn on all four sides of the pad
- **Canvas**: 800x600 pixels by default
- **Margins**: Optimized for publication (left, right, top, bottom tuned for
  axis labels and titles)
- **Title**: Histogram title display suppressed — use `ATLASLabel` and `myText`
  instead

### ATLAS Label Categories

Label text follows ATLAS publication policy strictly:

| Label text                 | Usage                                  |
| -------------------------- | -------------------------------------- |
| `"ATLAS"`                  | Approved results in published papers   |
| `"ATLAS Preliminary"`      | Conference results not yet in a paper  |
| `"ATLAS Internal"`         | Results not for public distribution    |
| `"ATLAS Simulation"`       | Simulation-only results (no real data) |
| `"ATLAS Work in Progress"` | Early-stage results, not for approval  |

## Canonical Patterns

### C++ ROOT Macro

```cpp
#include "AtlasStyle.C"
#include "AtlasLabels.C"
#include "AtlasUtils.C"

void myPlot() {
    SetAtlasStyle();

    TCanvas *c = new TCanvas("c", "", 800, 600);
    TH1F *h = new TH1F("h", "", 50, 0, 500);
    // ... fill histogram ...

    h->GetXaxis()->SetTitle("m_{jj} [GeV]");
    h->GetYaxis()->SetTitle("Events / 10 GeV");
    h->Draw();

    // Place ATLAS label and luminosity text
    ATLASLabel(0.2, 0.85, "Internal");
    myText(0.2, 0.78, 1, "#sqrt{s} = 13 TeV, 140 fb^{-1}");
}
```

### PyROOT

```python
import ROOT

ROOT.gROOT.LoadMacro("AtlasStyle.C")
ROOT.gROOT.LoadMacro("AtlasLabels.C")
ROOT.gROOT.LoadMacro("AtlasUtils.C")
ROOT.SetAtlasStyle()

c = ROOT.TCanvas("c", "", 800, 600)
h = ROOT.TH1F("h", "", 50, 0, 500)
# ... fill histogram ...

h.GetXaxis().SetTitle("m_{jj} [GeV]")
h.GetYaxis().SetTitle("Events / 10 GeV")
h.Draw()

ROOT.ATLASLabel(0.2, 0.85, "Internal")
ROOT.myText(0.2, 0.78, 1, "#sqrt{s} = 13 TeV, 140 fb^{-1}")

c.SaveAs("my_plot.pdf")
```

### Helper Functions Reference

```cpp
// Apply the ATLAS style globally
SetAtlasStyle();

// Place official ATLAS label at (x, y) in NDC coordinates
ATLASLabel(x, y, "Internal");        // "ATLAS Internal"
ATLASLabel(x, y, "Preliminary");     // "ATLAS Preliminary"
ATLASLabel(x, y, "");               // "ATLAS" alone (papers)

// Place arbitrary text (isNDC defaults to true)
myText(x, y, color, "text");

// Draw legend-style boxes and markers with text
myBoxText(x, y, boxsize, mcolor, "text");
myMarkerText(x, y, mcolor, mstyle, "text", msize);
```

### Ratio Plot Pattern

```cpp
SetAtlasStyle();

TCanvas *c = new TCanvas("c", "", 800, 800);

// Upper pad for main distribution
TPad *pad1 = new TPad("pad1", "", 0, 0.35, 1, 1);
pad1->SetBottomMargin(0.02);
pad1->Draw();
pad1->cd();
h_data->Draw("E");
h_mc->Draw("HIST SAME");
ATLASLabel(0.2, 0.85, "Internal");

// Lower pad for ratio
c->cd();
TPad *pad2 = new TPad("pad2", "", 0, 0, 1, 0.35);
pad2->SetTopMargin(0.02);
pad2->SetBottomMargin(0.3);
pad2->Draw();
pad2->cd();
h_ratio->GetYaxis()->SetTitle("Data / MC");
h_ratio->GetYaxis()->SetRangeUser(0.5, 1.5);
h_ratio->Draw("E");
```

### Multi-Histogram with Legend

```cpp
SetAtlasStyle();

TCanvas *c = new TCanvas("c", "", 800, 600);
TLegend *leg = new TLegend(0.65, 0.65, 0.90, 0.85);
leg->SetBorderSize(0);
leg->SetFillStyle(0);
leg->SetTextFont(43);
leg->SetTextSize(20);

h1->SetLineColor(kBlue);
h2->SetLineColor(kRed);
h1->Draw("HIST");
h2->Draw("HIST SAME");
leg->AddEntry(h1, "Background", "l");
leg->AddEntry(h2, "Signal", "l");
leg->Draw();

ATLASLabel(0.2, 0.85, "Simulation");
myText(0.2, 0.78, 1, "#sqrt{s} = 13.6 TeV");
```

## Gotchas

- **Call `SetAtlasStyle()` before creating histograms or canvases**: Style
  settings apply at object creation time. Calling it afterward may not override
  all defaults.
- **Use `#include`, not `gROOT->LoadMacro()`** in compiled C++ macros after
  `lsetup astyle` — the macros are on the ROOT include path.
- **For PyROOT, use `gROOT.LoadMacro()`**: Python cannot use `#include`, so load
  macros explicitly at runtime.
- **NDC coordinates for labels**: `ATLASLabel` and `myText` use Normalized
  Device Coordinates (0–1 range). Typical placement is `x=0.2, y=0.85` for the
  ATLAS label.
- **No stat box**: The style disables the statistics box by default. To
  re-enable, call `gStyle->SetOptStat(1)` after `SetAtlasStyle()`.
- **Label text is policy**: Using the wrong label category (e.g. "ATLAS" on
  unapproved results) violates ATLAS publication policy — see the label table
  above.
- **All ATLAS energy/momentum values are in MeV** in the detector/analysis
  framework, but plot axis labels conventionally show GeV or TeV.

## Interop

- **setupATLAS / lsetup**: `lsetup astyle` is the standard way to configure the
  macros — see the setupatlas skill for environment setup.
- **ROOT**: atlasrootstyle targets ROOT 6; functions use ROOT C++ types
  (`TCanvas`, `TH1`, `TLegend`).
- **mplhep (matplotlib)**: For Python-native plotting with matplotlib, the
  mplhep skill covers `mplhep.style.use("ATLAS")` and `mplhep.atlas.label()` —
  the matplotlib equivalent of `SetAtlasStyle` and `ATLASLabel`. The label
  categories and publication policy rules are identical across both tools.
- **hist / uproot**: Use with mplhep for a pure-Python plotting workflow;
  atlasrootstyle is ROOT-specific.

## Docs

https://gitlab.cern.ch/atlas-publications-committee/atlasrootstyle
