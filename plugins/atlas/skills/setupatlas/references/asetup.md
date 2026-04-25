# asetup Reference

- Quick start guide:
  https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/AtlasSetup
- Full reference:
  https://twiki.cern.ch/twiki/bin/view/AtlasComputing/AtlasSetupReference

## Release name syntax

| Input                          | Meaning                         |
| ------------------------------ | ------------------------------- |
| `Athena,24.0.0`                | stable release 24.0.0           |
| `Athena,main,latest`           | latest nightly of main branch   |
| `--stable Athena,24.0,latest`  | latest stable 24.0.x            |
| `Athena,main,r07-07`           | nightly from July 7             |
| `Athena,main,r2024-07-07T2101` | exact nightly timestamp         |
| `none,gcc14,cmakesetup`        | compiler+cmake only, no release |

Tags can be comma- or space-separated.

## Configuration files (priority order)

asetup reads configuration in this order (each overrides the previous):

1. Built-in asetup defaults
2. Site config: `$AtlasSetupSiteCMake` or `$AtlasSetup/../asetupSite/.asetup`
3. `$HOME/.asetup`
4. `$PWD/.asetup`
5. `--inputconfig <file>` (skips HOME and PWD files if specified)
6. Command-line arguments (highest priority)

## Configuration file format

```ini
[defaults]
os = el9
arch = 64

[aliases]
# alias = comma-separated tags
sa07 = StatAnalysis,0.7,latest

[environment]
# Set before release env (unless --userpriority)
MY_VAR = foo
PATH = $HOME/bin:${PATH}

[epilog.sh]
source $HOME/mytools/setup.sh

[prolog.sh]
source myprolog.sh
```

## Common asetup options

| Option                 | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `--stable`             | Restrict to stable releases only                  |
| `--nightliesonly`      | Restrict to nightly releases only                 |
| `--reset`              | Undo all asetup changes, restore original shell   |
| `--simulate`           | Show what would be done without executing         |
| `--silent` / `--quiet` | Suppress all output                               |
| `--printLast`          | Print last saved session info for `$PWD`          |
| `--version`            | Print asetup version string                       |
| `--platform=<str>`     | Force platform, e.g. `x86_64-el9-gcc13-opt`       |
| `--releasebase=<dir>`  | Specify exact release path                        |
| `--testarea=<dir>`     | Set TestArea (creates CMakeLists.txt if absent)   |
| `--userpriority`       | Give `[environment]` section vars higher priority |
| `--inputconfig=None`   | Skip all private config files                     |
| `--helpGroup=All`      | Print all available options                       |
| `source <script>`      | Source script and add to saved session            |

## Environment variables set by asetup

| Variable                              | Description                                   |
| ------------------------------------- | --------------------------------------------- |
| `AtlasProject`                        | Project name (`Athena`, `AnalysisBase`, etc.) |
| `AtlasVersion`                        | Release number found                          |
| `AtlasBuildBranch`                    | Branch (`main`, `24.0`, `0.7`)                |
| `AtlasBuildStamp`                     | Build date-stamp of the release               |
| `AtlasReleaseType`                    | `stable` or `nightly`                         |
| `AtlasArea`                           | Full path to the project release              |
| `AtlasBaseDir` / `ATLAS_RELEASE_BASE` | Release base directory                        |
| `BINARY_TAG` / `CMTCONFIG`            | Platform string (`x86_64-el9-gcc13-opt`)      |
| `LCG_RELEASE_BASE`                    | LCG releases base path                        |
| `TestArea`                            | Current build directory path                  |
| `MAKEFLAGS`                           | Set to `-j<ncores> -l<ncores>` by default     |
| `SITEROOT`                            | Parent of release directory                   |

## Saved session

asetup automatically saves session info to `$PWD/.asetup.save`. Running `asetup`
with no arguments re-applies the last session. Use `asetup --printLast` to
inspect what is saved.

```bash
# Save and restore workflow
cd my_build_dir
asetup StatAnalysis,0.7,latest        # sets up and saves
# ... later in a new shell ...
cd my_build_dir
asetup                                # restores last session
```

## Platform string

Platform has four dash-separated parts: `<arch>-<os>-<compiler>-<mode>`

Examples: `x86_64-el9-gcc13-opt`, `x86_64-slc6-gcc62-opt`

Override with `--platform=<string>` or `--os=<os>`, `--gccversion=<ver>`,
`--opt` / `--dbg`.
