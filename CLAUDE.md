# USATLAS Marketplace — Maintenance Guide

## Repository layout

```
plugins/
  <plugin-name>/
    .claude-plugin/plugin.json   # Claude Code plugin manifest
    .cursor-plugin/plugin.json   # Cursor plugin manifest
    .mcp.json                    # MCP server config (atlas only)
    agents/<name>.md             # subagent definitions
    skills/<name>/SKILL.md       # skill definitions
.claude-plugin/marketplace.json  # Claude Code registry of all plugins
.codex/INSTALL.md                # Codex native skill discovery instructions
```

The root `skills/` directory is unused — all skills live under `plugins/`.

## Adding a skill

1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md`.
2. Add `"<skill-name>"` to `"skills"` array in `.claude-plugin/marketplace.json`
   under the correct plugin entry. The array order is the display order.
3. Run `pixi run pre-commit` to catch JSON/YAML/Markdown formatting issues.

**Skill frontmatter rules (strictly enforced by Claude Code):**

```yaml
---
name: skill-name          # letters, numbers, hyphens only
description: >-
    Use when <triggering condition 1>, <condition 2>, ...
---
```

- Only `name` and `description` are valid frontmatter fields. Any other field
  (e.g. `attribution:`, `author:`) will cause the skill to fail to load.
- `description` must start with "Use when" and describe triggering conditions
  only — never summarize the skill's content or workflow.
- Max ~1024 characters total across both fields.

**Skill content guidelines:**

- Section order: Overview → When to Use → Key Concepts → Canonical Patterns →
  Gotchas → Interop → Docs.
- Deep skills (uproot, coffea, pyhf) add a Worked Example and Troubleshooting
  table (~300–400 lines). Medium skills target ~150–250 lines.
- All ATLAS energy/momentum values are in MeV — note this in Gotchas.
- End with a `## Docs` section linking the canonical upstream documentation URL.
- No `attribution:` or vendoring comments inside skill files. Legal attribution
  for upstream content lives only in `plugins/atlas/VENDORED-LICENSES.md`.

## Adding a subagent

1. Create `plugins/atlas/agents/<agent-name>.md`.
2. Frontmatter fields: `name`, `description`, `tools` (list), `model`, `color`.
3. No registration in `marketplace.json` is required for agents.

Example frontmatter:

```yaml
---
name: my-agent
description: >-
    Use when ...
tools:
  - Read
  - Bash
  - WebFetch
model: claude-sonnet-4-5
color: purple
---
```

## Adding a plugin

When adding a plugin, create manifests for **all three tools** in parallel.

1. Create `plugins/<plugin-name>/.claude-plugin/plugin.json`:
   ```json
   {
     "name": "<plugin-name>",
     "description": "...",
     "homepage": "https://...",
     "repository": "https://github.com/usatlas/marketplace",
     "license": "MIT",
     "keywords": ["..."]
   }
   ```
2. Add an entry to `.claude-plugin/marketplace.json` `"plugins"` array with
   `"name"`, `"description"`, `"source"` (`"./plugins/<plugin-name>"`),
   `"skills"`, and `"keywords"`.
3. Create `plugins/<plugin-name>/.cursor-plugin/plugin.json` mirroring the
   Claude plugin manifest but with `"displayName"`, `"author": {"name": "USATLAS"}`,
   and path fields `"skills": "./skills/"` (and `"agents": "./agents/"` if the
   plugin has agents). No `"commands"` or `"hooks"` fields unless needed.

4. Add the new plugin's symlink instructions to `.codex/INSTALL.md`.

5. Create skill directories as described above.

## Editing marketplace.json

After any skill add/remove, verify the `"skills"` array matches the actual
`plugins/<plugin>/skills/` directory contents:

```bash
# Quick parity check for the atlas plugin
diff \
  <(python3 -c "import json; [print(s) for s in json.load(open('.claude-plugin/marketplace.json'))['plugins'][1]['skills']]") \
  <(ls plugins/atlas/skills/ | sort)
```

## MCP servers (atlas plugin only)

Configured in `plugins/atlas/.mcp.json`. Users must set:

```bash
export RUCIO_ACCOUNT=yourusername   # required, no default
export RUCIO_AUTH_TYPE=x509_proxy   # default; alternatives: oidc, userpass
voms-proxy-init --voms atlas        # valid proxy required for rucio MCP
```

The three servers:

| Key | Launch | Notes |
|---|---|---|
| `rucio` | `pixi exec rucio-mcp serve --read-only` | RUCIO_ACCOUNT must be set |
| `ami` | `pixi exec ami-mcp serve` | no extra env vars |
| `atlasopenmagic` | `uvx atlasopenmagic-mcp serve` | no extra env vars |

## ATLAS software docs

`atlas-software-docs/` is a git submodule cloned locally for fast `grep`-based
structural orientation. **Never cite local paths in user-facing content.**
All documentation references must point to the hosted site:
`https://atlas-software.docs.cern.ch/`

The `atlas-docs-expert` subagent implements the two-tier lookup:
grep locally for page discovery → WebFetch the hosted URL for authoritative content.

## Pre-commit / formatting

```bash
pixi run pre-commit     # run all hooks on all files
```

Hooks enforce: JSON/YAML validity, trailing whitespace, mixed line endings,
Markdown prose wrapping (prettier, 80 cols), and spell-checking. The
`codespell` dictionary `"-L hist,gaus"` whitelists HEP-specific words.

## Commit conventions

Conventional Commits format:

```
feat(atlas): add <skill-name> skill
feat(atlas,hep-python-tools): ...
fix(<plugin>): ...
docs: ...
chore: ...
refactor: ...
```

No `Co-Authored-By` lines in commit messages.

## Vendored content (IRIS-HEP)

Skills adapted from the IRIS-HEP marketplace (Gordon Watts, Ben Galewsky) are
listed in `plugins/atlas/VENDORED-LICENSES.md`. Individual skill files carry
no attribution markers — the license file satisfies BSD 3-Clause requirements.
When updating a vendored skill, rewrite from expert knowledge rather than
copying upstream verbatim.
