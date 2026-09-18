# ATLAS Tools Reference

Complements `asetup.md`. Covers the full `lsetup` tool catalog, the complete
`acm` command reference, and the full utility command list available after
`setupATLAS`.

## lsetup tool catalog

See all available versions with `lsetup <tool> -h` or `showVersions`.

| Tool       | Description                            | Docs / Contact                                                     |
| ---------- | -------------------------------------- | ------------------------------------------------------------------ |
| `asetup`   | Athena/StatAnalysis release setup      | https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/AtlasSetup |
| `root`     | ROOT data analysis framework           | https://root.cern                                                  |
| `rucio`    | Distributed data management client     | https://rucio-ui.cern.ch                                           |
| `panda`    | PanDA distributed analysis client      | https://panda-wms.readthedocs.io                                   |
| `pyami`    | ATLAS Metadata Interface Python client | https://atlas-ami.cern.ch                                          |
| `scikit`   | scikit-hep Python ecosystem            | https://scikit-hep.org                                             |
| `views`    | Full LCG software release              | `lsetup "views"` for list                                          |
| `xrootd`   | XRootD data access                     |                                                                    |
| `xcache`   | XRootD local proxy cache               | https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Xcache          |
| `lcgenv`   | LCG environment tool                   | https://twiki.atlas-canada.ca/bin/view/AtlasCanada/Lcgenv          |
| `astyle`   | ATLAS ROOT style macros                | https://gitlab.cern.ch/atlas-publications-committee/atlasrootstyle |
| `eiclient` | Event Index client                     | https://twiki.cern.ch/twiki/bin/view/AtlasComputing/EventIndex     |

## acm command reference

`acm` (AtlasACM) is the ATLAS cmake/git build tool that wraps `asetup` and
manages source checkouts, compilation, and testing.

| Command                           | Description                                       |
| --------------------------------- | ------------------------------------------------- |
| `acmSetup [opts] <release>`       | Set up release + source area                      |
| `acm compile`                     | Build project (cmake --build)                     |
| `acm compile_pkg <pkg>`           | Build a single package                            |
| `acm find_packages`               | Reconfigure cmake (wipes CMakeCache)              |
| `acm test <pkg>`                  | Run ctests for a package                          |
| `acm clean [-f]`                  | cmake clean; `-f` also reruns find_packages       |
| `acm clone_project <repo>`        | Clone a GitLab project into source area           |
| `acm sparse_clone_project athena` | Sparse-clone the athena project                   |
| `acm add_pkg <path>`              | Include package(s) in compilation                 |
| `acm exclude_pkg <path>`          | Exclude package(s) from compilation               |
| `acm add_pkg_clients <path>`      | Add all packages that depend on the given one     |
| `acm switch <branch/tag> <path>`  | Check out specific version of a package           |
| `acm new_pkg <name>`              | Create a new cmake package                        |
| `acm new_skeleton <name>`         | Create a skeleton analysis package with algorithm |
| `acmSetup --unset`                | Undo the current setup                            |

Contact: atlas-sw-acm-users@cern.ch

## Utility commands

```bash
showVersions            # show installed software versions
queryC <name>           # find/query containers on CVMFS
installPip <pkg>        # install pip package into local area
installRpm <pkg>        # install RPM into local area
diagnostics             # diagnostic tools menu
advancedTools           # advanced tools menu
printMenu               # reprint the setupATLAS menu
helpMe                  # extended help with all tool documentation
```
