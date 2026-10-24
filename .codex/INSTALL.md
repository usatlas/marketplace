# Installing USATLAS Marketplace for Codex

Enable USATLAS skills in Codex via native skill discovery.

The `atlas` and `hep-python-tools` plugins depend on skills
(`analysis-spec-builder`, `awkward-array`, `cli-creator`, `hist`, `servicex`,
`standalone-script`, `vector-awkward`) provided by the `iris-hep` plugin,
referenced from [iris-hep/marketplace](https://github.com/iris-hep/marketplace)
rather than vendored here. Codex has no equivalent of Claude Code's plugin
`dependencies` resolution, so clone that repository too and symlink its
`iris-hep/skills` directory the same way as below if you need those skills.

## Prerequisites

- Git

## Installation

1. **Clone the repository** (if you haven't already):

   ```bash
   git clone https://github.com/usatlas/marketplace.git ~/usatlas-marketplace
   ```

2. **Create the skills directory** and symlink each plugin:

   ```bash
   mkdir -p ~/.agents/skills

   ln -s ~/usatlas-marketplace/plugins/atlas/skills \
         ~/.agents/skills/atlas

   ln -s ~/usatlas-marketplace/plugins/af-uchicago/skills \
         ~/.agents/skills/af-uchicago

   ln -s ~/usatlas-marketplace/plugins/hep-python-tools/skills \
         ~/.agents/skills/hep-python-tools

   ln -s ~/usatlas-marketplace/plugins/af-bnl/skills \
         ~/.agents/skills/af-bnl
   ```

   **Windows (PowerShell):**

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   $base = "$env:USERPROFILE\usatlas-marketplace\plugins"
   $target = "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$target\atlas"            "$base\atlas\skills"
   cmd /c mklink /J "$target\af-uchicago"      "$base\af-uchicago\skills"
   cmd /c mklink /J "$target\hep-python-tools" "$base\hep-python-tools\skills"
   cmd /c mklink /J "$target\af-bnl"           "$base\af-bnl\skills"
   ```

3. **Optional: enable `iris-hep` skills** (needed by `atlas` and
   `hep-python-tools`) by cloning
   [iris-hep/marketplace](https://github.com/iris-hep/marketplace) alongside
   this repository and symlinking its `iris-hep/skills` directory:

   ```bash
   git clone https://github.com/iris-hep/marketplace.git ~/iris-hep-marketplace

   ln -s ~/iris-hep-marketplace/iris-hep/skills \
         ~/.agents/skills/iris-hep
   ```

   **Windows (PowerShell):**

   ```powershell
   git clone https://github.com/iris-hep/marketplace.git "$env:USERPROFILE\iris-hep-marketplace"
   cmd /c mklink /J "$target\iris-hep" "$env:USERPROFILE\iris-hep-marketplace\iris-hep\skills"
   ```

4. **Restart Codex** (quit and relaunch the CLI) to discover the skills.

## Verify

**macOS/Linux:**

```bash
ls -la ~/.agents/skills/
```

**Windows (PowerShell):**

```powershell
Get-ChildItem $env:USERPROFILE\.agents\skills
```

You should see four symlinks: `atlas`, `af-uchicago`, `af-bnl`,
`hep-python-tools`. If you also enabled `iris-hep` skills, you should see a
fifth symlink named `iris-hep`.

## Updating

```bash
cd ~/usatlas-marketplace && git pull
```

If you cloned `iris-hep/marketplace`, refresh it too:

```bash
cd ~/iris-hep-marketplace && git pull
```

Skills update instantly through the symlinks.

## Install only specific plugins

If you only want a subset, symlink only those plugins:

```bash
# ATLAS analysis skills only
ln -s ~/usatlas-marketplace/plugins/atlas/skills ~/.agents/skills/atlas
```

## Uninstalling

```bash
rm ~/.agents/skills/atlas
rm ~/.agents/skills/af-uchicago
rm ~/.agents/skills/af-bnl
rm ~/.agents/skills/hep-python-tools
```

Optionally delete the clone: `rm -rf ~/usatlas-marketplace`.
