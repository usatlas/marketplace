# EventSelection DSL Reference

The `selectionCuts` value in each `EventSelection:` block is a mini-language:
one keyword per line, processed top-to-bottom. All pT and mass thresholds are in
**MeV**.

`$` is a placeholder for any comparison operator: `>=`, `>`, `==`, `<`, `<=`.

## Keyword table

| Keyword               | Options                                                                                                  | Effect                                                                                                                                                                          |
| --------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EL_N`                | `ptmin $ ref`<br>`sel ptmin $ ref`                                                                       | Count electrons with pT > `ptmin`; compare to `ref`. Optional `sel` applies an extra electron selection (e.g. `tight`).                                                         |
| `MU_N`                | `ptmin $ ref`<br>`sel ptmin $ ref`                                                                       | Count muons with pT > `ptmin`; compare to `ref`. Optional `sel` applies an extra muon selection.                                                                                |
| `SUM_EL_N_MU_N`       | `ptmin $ ref`<br>`ptminEL ptminMU $ ref`<br>`selEL selMU ptminEL ptminMU $ ref`                          | Count electrons+muons above pT thresholds; compare to `ref`. Separate electron/muon pT cuts and selections are supported.                                                       |
| `SUM_EL_N_MU_N_TAU_N` | `ptmin $ ref`<br>`ptminEL ptminMU ptminTAU $ ref`<br>`selEL selMU selTAU ptminEL ptminMU ptminTAU $ ref` | Count electrons+muons+taus above pT thresholds; compare to `ref`.                                                                                                               |
| `JET_N`               | `ptmin $ ref`<br>`sel ptmin $ ref`                                                                       | Count jets with pT > `ptmin`; compare to `ref`. Optional `sel` applies an extra jet selection (e.g. `passesOR`).                                                                |
| `JET_N_BTAG`          | `$ ref`<br>`tagger:WP $ ref`<br>`sel $ ref`<br>`sel tagger:WP $ ref`                                     | Count b-tagged jets; compare to `ref`. Optional `sel` applies an extra jet selection. Optional `tagger:WP` specifies the b-tagger and WP (e.g. `DL1dv01:FixedCutBEff_77`).      |
| `JET_N_GHOST`         | `ghost $ ref`<br>`ghost ptmin $ ref`                                                                     | Count jets containing `ghost` particles (B, C, W, Z, H, T, TAU) with pT > `ptmin`; compare to `ref`. Use `X!Y` to require X-ghosts and veto Y-ghosts.                           |
| `LJET_N`              | `ptmin $ ref`<br>`sel ptmin $ ref`                                                                       | Count large-R jets with pT > `ptmin`; compare to `ref`.                                                                                                                         |
| `LJET_N_GHOST`        | `ghost $ ref`<br>`ghost ptmin $ ref`                                                                     | Count large-R jets containing `ghost` particles; compare to `ref`.                                                                                                              |
| `LJETMASS_N`          | `massmin $ ref`<br>`sel massmin $ ref`                                                                   | Count large-R jets with mass > `massmin` (MeV); compare to `ref`.                                                                                                               |
| `LJETMASSWINDOW_N`    | `low high $ ref`<br>`sel low high $ ref`                                                                 | Count large-R jets with `low` < mass < `high` (MeV); compare to `ref`. Append `veto` to veto the window instead.                                                                |
| `PH_N`                | `ptmin $ ref`<br>`sel ptmin $ ref`                                                                       | Count photons with pT > `ptmin`; compare to `ref`.                                                                                                                              |
| `TAU_N`               | `ptmin $ ref`<br>`sel ptmin $ ref`                                                                       | Count tau-jets with pT > `ptmin`; compare to `ref`.                                                                                                                             |
| `OBJ_N`               | `obj ptmin $ ref`                                                                                        | Count objects from container `obj` (or `obj.sel`) with pT > `ptmin`; compare to `ref`. Generic fallback for any container.                                                      |
| `MET`                 | `$ ref`                                                                                                  | Compare MET to `ref` (MeV).                                                                                                                                                     |
| `MWT`                 | `$ ref`                                                                                                  | Compare transverse W mass (lepton + MET) to `ref` (MeV).                                                                                                                        |
| `MET+MWT`             | `$ ref`                                                                                                  | Compare MET + transverse W mass to `ref` (MeV).                                                                                                                                 |
| `MLL`                 | `$ ref`                                                                                                  | Compare dilepton invariant mass to `ref` (MeV).                                                                                                                                 |
| `MLLWINDOW`           | `low high`<br>`low high veto`                                                                            | Select (or veto) events where `low < m(ll) < high` (MeV). To select a Z window: `MLLWINDOW 81000 101000`. To veto it: `MLLWINDOW 101000 81000`.                                 |
| `MLL_OSSF`            | `low high`<br>`low high veto`                                                                            | Like `MLLWINDOW` but restricted to opposite-sign same-flavour lepton pairs.                                                                                                     |
| `OS`                  | —                                                                                                        | Require exactly two opposite-sign leptons.                                                                                                                                      |
| `SS`                  | —                                                                                                        | Require exactly two same-sign leptons.                                                                                                                                          |
| `EVENTFLAG`           | `sel`                                                                                                    | Fold an existing selection flag `sel` into this region's output branch. Useful to avoid saving the source flag separately.                                                      |
| `GLOBALTRIGMATCH`     | —<br>`postfix`                                                                                           | Require the event passes global trigger matching. Optional `postfix` selects a named trigger matching setup defined by the `postfix` option in the `Trigger:` block.            |
| `RUN_NUMBER`          | `$ ref`                                                                                                  | Compare run number (randomised for MC) to `ref`.                                                                                                                                |
| `IMPORT`              | `subreg`                                                                                                 | Apply all cuts from subregion `subreg`. The subregion name must start with `SUB`.                                                                                               |
| `SAVE`                | —                                                                                                        | Emit a `pass_<region>_%SYS%` flag at the current point in the cut sequence. Required for the final event filter. Can also appear mid-sequence to save an intermediate decision. |

## Region patterns

### Subregions and `IMPORT`

Prefix a `selectionName` with `SUB` to define a reusable preselection. These are
not used as event filters; they only produce a decision flag that other regions
can `IMPORT`.

```yaml
EventSelection:
  - &common                          # YAML anchor for shared options
    electrons: "AnaElectrons.tight"
    jets: "AnaJets.passesOR"
    btagDecoration: "ftag_select_DL1dv01_FixedCutBEff_77"
    selectionName: "SUBpresel"       # prefix with SUB → not filtered on
    selectionCuts: |
      JET_N passesOR 25000 >= 4
      JET_N_BTAG passesOR >= 2
      SAVE

  - << *common                       # merge anchor → copies all options above
    selectionName: "ejets"           # overrides selectionName only
    selectionCuts: |
      IMPORT SUBpresel               # inherit the preselection cuts
      EL_N tight 27000 == 1
      MU_N tight 27000 == 0
      SAVE

  - << *common
    selectionName: "mujets"
    selectionCuts: |
      IMPORT SUBpresel
      EL_N tight 27000 == 0
      MU_N tight 27000 == 1
      SAVE
```

The resulting output branches are `pass_SUBpresel_%SYS%`, `pass_ejets_%SYS%`,
and `pass_mujets_%SYS%`.

### Per-region b-tag counting

`JET_N_BTAG` uses the b-tagging decoration configured in the `FlavourTagging:`
block by default. To override it per-line:

```
JET_N_BTAG passesOR DL1dv01:FixedCutBEff_70 >= 1
```

### Trigger matching with multiple postfixes

When running two trigger matching setups (e.g. loose and tight leptons), the
`postfix` option distinguishes them in `GLOBALTRIGMATCH`:

```
GLOBALTRIGMATCH tight    # uses trigger matching setup with postfix='tight'
GLOBALTRIGMATCH loose    # uses trigger matching setup with postfix='loose'
```

## Docs

<https://topcptoolkit.docs.cern.ch/latest/settings/eventselection/>
