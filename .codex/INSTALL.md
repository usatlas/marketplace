# Installing USATLAS Marketplace for Codex

Enable USATLAS skills in Codex via native skill discovery.

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

   ln -s ~/usatlas-marketplace/plugins/analysis-facilities/skills \
         ~/.agents/skills/analysis-facilities

   ln -s ~/usatlas-marketplace/plugins/hep-python-tools/skills \
         ~/.agents/skills/hep-python-tools

   ln -s ~/usatlas-marketplace/plugins/bnl-localgroupdisk/skills \
         ~/.agents/skills/bnl-localgroupdisk
   ```

   **Windows (PowerShell):**

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   $base = "$env:USERPROFILE\usatlas-marketplace\plugins"
   $target = "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$target\atlas"                "$base\atlas\skills"
   cmd /c mklink /J "$target\analysis-facilities"  "$base\analysis-facilities\skills"
   cmd /c mklink /J "$target\hep-python-tools"     "$base\hep-python-tools\skills"
   cmd /c mklink /J "$target\bnl-localgroupdisk"   "$base\bnl-localgroupdisk\skills"
   ```

3. **Restart Codex** (quit and relaunch the CLI) to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/
```

You should see four symlinks: `atlas`, `analysis-facilities`,
`bnl-localgroupdisk`, `hep-python-tools`.

## Updating

```bash
cd ~/usatlas-marketplace && git pull
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
rm ~/.agents/skills/analysis-facilities
rm ~/.agents/skills/bnl-localgroupdisk
rm ~/.agents/skills/hep-python-tools
```

Optionally delete the clone: `rm -rf ~/usatlas-marketplace`.
