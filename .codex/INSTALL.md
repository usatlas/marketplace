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

3. **Restart Codex** (quit and relaunch the CLI) to discover the skills.

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
`hep-python-tools`.

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
rm ~/.agents/skills/af-uchicago
rm ~/.agents/skills/af-bnl
rm ~/.agents/skills/hep-python-tools
```

Optionally delete the clone: `rm -rf ~/usatlas-marketplace`.
