# USATLAS Marketplace — Maintenance Guide

## Repository layout

```text
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

## Skills for skill authoring

When authoring or editing skill files in this repository, invoke these installed
skills for authoritative guidance before writing:

- `plugin-dev:skill-development` — SKILL.md structure, frontmatter rules,
  progressive disclosure (SKILL.md vs references/ vs scripts/), trigger-phrase
  writing, and the full creation/validation/iteration workflow
- `superpowers-developing-for-claude-code:developing-claude-code-plugins` —
  plugin layout, dev-marketplace testing, and release process
- `superpowers-developing-for-claude-code:working-with-claude-code` — official
  Claude Code documentation reference for hooks, MCP, settings, and CLI

The canonical, tool-agnostic authoring guidance lives at
[agentskills.io](https://agentskills.io/llms.txt). The most relevant pages:

- [Specification](https://agentskills.io/specification) — frontmatter fields,
  directory structure, progressive disclosure, and the `skills-ref` validator
  (run it here via `pixi run validate-skills`).
- [Best practices](https://agentskills.io/skill-creation/best-practices) —
  scoping, calibrating control, gotchas/template/checklist patterns.
- [Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
  — writing `description` fields that trigger reliably.
- [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills)
  and [Using scripts](https://agentskills.io/skill-creation/using-scripts).

## Adding a skill

1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md`.
2. No changes to `marketplace.json` are needed — skills are discovered
   automatically from the `"skills": "./skills/"` path declared per plugin.
3. Stage the new files.
4. Run `pixi run pre-commit` to catch JSON/YAML/Markdown formatting issues.
5. Run `pixi run check-skills` to catch updates needed from new skills.

**Skill frontmatter** (per the
[Agent Skills specification](https://agentskills.io/specification)):

```yaml
---
name: skill-name # matches the directory name
description: >-
  Use when <triggering condition 1>, <condition 2>, ...
---
```

- The spec defines six valid fields: `name` and `description` (both required)
  plus optional `license`, `compatibility`, `metadata`, and `allowed-tools`. Do
  **not** invent top-level keys (e.g. `author:`, `attribution:`, `version:`) —
  route any such metadata through the `metadata:` map if it is genuinely needed.
- `name`: max 64 characters; lowercase letters, numbers, and hyphens only; no
  leading/trailing or consecutive hyphens; **must equal the skill's directory
  name**.
- `description`: max 1024 characters. Must start with "Use when" and describe
  **triggering conditions only** — never summarize the skill's content or
  workflow. A workflow summary in the description makes the model follow the
  summary instead of reading the skill body.
- **Repo convention:** keep skills to `name` + `description` only. Legal
  attribution for vendored content lives solely in
  `plugins/atlas/VENDORED-LICENSES.md`, never as a frontmatter key.

**Skill content guidelines:**

- Section order: Overview → When to Use → Key Concepts → Canonical Patterns →
  Gotchas → Interop → Docs.
- Deep skills (uproot, coffea, pyhf, histfitter) add a Worked Example and
  Troubleshooting table (~300–500 lines). Medium skills target ~150–250 lines.
- All ATLAS energy/momentum values are in MeV — note this in Gotchas.
- End with a `## Docs` section linking the canonical upstream documentation URL.
- No `attribution:` or vendoring comments inside skill files. Legal attribution
  for upstream content lives only in `plugins/atlas/VENDORED-LICENSES.md`.

**Progressive disclosure with `references/`:**

Skills that cover a broad API or deep domain knowledge should use the
three-level loading pattern:

1. **SKILL.md** (target <500 lines and <5000 tokens) — decision guide: overview,
   when to use, key concepts, canonical patterns, gotchas, and a "Reference
   Files" section with pointers.
2. **`references/*.md`** — deep content loaded on demand. Each file covers one
   topic (e.g., `systematic-types.md`, `config-api.md`, `helper-scripts.md`).
   Each reference file should include a trigger sentence ("Read this reference
   when…") followed by a Table of Contents near the top.
3. **`scripts/`** — executable code for deterministic/repetitive tasks (rare).
   Design scripts for agentic use: non-interactive (all input via flags/stdin),
   a useful `--help`, structured stdout (JSON/CSV) with diagnostics on stderr,
   and clear exit codes. Prefer PEP 723 inline metadata (`uv run --script`) for
   self-contained Python tools — see the `standalone-script` skill.
4. **`assets/`** — static resources (output templates, schemas, data files)
   loaded only when needed.

The "Reference Files" section in SKILL.md should list each reference with a
one-line description of its content and **when to read it** (e.g., "Read when
the user asks which systematic type to use"). This lets the model decide at
runtime whether loading the reference is worthwhile.

Good examples of this pattern: `awkward`, `xroofit`, `histfitter`.

**Writing style for skills:**

- Verify all API methods, CLI flags, and code examples against the actual source
  code. Do not invent methods or flags — grep the source to confirm they exist.
- Use imperative form in instructions ("Set `configMgr.analysisName`", not "You
  should set...").
- Prefer tables for reference material (CLI flags, method lists, property
  tables).
- Include realistic code examples that can be copy-pasted. Mark deprecated APIs
  and point to the replacement.
- When drawing from TWiki pages, tutorials, or upstream docs, rewrite from
  expert knowledge rather than copying verbatim. Cross-reference against source
  code to catch outdated or incorrect TWiki content.

## Adding a subagent

1. Create `plugins/atlas/agents/<agent-name>.md`.
2. Frontmatter fields: `name`, `description`, `tools` (list), `model`, `color`,
   and the optional `readme_description`. Agents follow the Claude Code subagent
   format, **not** the Agent Skills skill spec, so this field set differs from
   skill frontmatter.
   - `model` accepts an alias (`sonnet`, `opus`, `haiku`) or a pinned ID (e.g.
     `claude-sonnet-4-6`, `claude-opus-4-8`).
   - `readme_description` is read by `scripts/sync_skills.py` to build the
     Subagents table in the README; if omitted, the summary is derived from
     `description`.
3. No registration in `marketplace.json` is required for agents.

Example frontmatter:

```yaml
---
name: my-agent
description: >-
  Use when ...
readme_description: One-line summary for the README Subagents table.
tools:
  - Read
  - Bash
  - WebFetch
model: claude-sonnet-4-6
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
   Claude plugin manifest but with `"displayName"`,
   `"author": {"name": "USATLAS"}`, and path fields `"skills": "./skills/"` (and
   `"agents": "./agents/"` if the plugin has agents). No `"commands"` or
   `"hooks"` fields unless needed.

4. Add the new plugin's symlink instructions to `.codex/INSTALL.md`.

5. Create skill directories as described above.

## Editing marketplace.json

Skills are auto-discovered via `"skills": "./skills/"` in each plugin entry — no
manual list to maintain. After adding or removing a skill directory, run
`claude plugin validate .claude-plugin/marketplace.json` to confirm the manifest
is still valid.

To validate skills against the Agent Skills spec (frontmatter fields, naming,
structure), run the spec validator over all skills:

```bash
pixi run validate-skills
```

This wraps the [`skills-ref`](https://pypi.org/project/skills-ref/) reference
library (a `pypi-dependency` in `pixi.toml`, so `pixi install` provides it). The
library's CLI is installed as `agentskills`, so a single skill can be checked
directly with `pixi run agentskills validate plugins/<plugin>/skills/<name>`.

`validate-skills` complements `pixi run lint-skills` (this repo's section
ordering) and is included in `pixi run check-skills` alongside the README sync.

## MCP servers (atlas plugin only)

Configured in `plugins/atlas/.mcp.json`. First-time setup:

```bash
rucio-mcp init atlas                # one-time: writes ~/.config/rucio-mcp/rucio.cfg
export RUCIO_ACCOUNT=yourusername   # required, no default
pixi exec --spec rucio-mcp sh -c 'voms-proxy-init -voms atlas'  # valid proxy required
```

Health check: `RUCIO_ACCOUNT=yourusername rucio-mcp ping`

If ping fails with a CRL expiry error, refresh the CRLs:

```bash
pixi exec --spec rucio-mcp sh -c '$X509_CERT_DIR/refresh_crls.sh'
```

The three servers:

| Key              | Launch                                                           | Notes                     |
| ---------------- | ---------------------------------------------------------------- | ------------------------- |
| `rucio`          | `pixi exec --spec rucio-mcp sh -c 'rucio-mcp serve --read-only'` | RUCIO_ACCOUNT must be set |
| `ami`            | `pixi exec --spec ami-mcp sh -c 'ami-mcp serve'`                 | no extra env vars         |
| `atlasopenmagic` | `uvx atlasopenmagic-mcp serve`                                   | no extra env vars         |

## ATLAS software docs

`atlas-software-docs/` is a git submodule cloned locally for fast `grep`-based
structural orientation. **Never cite local paths in user-facing content.** All
documentation references must point to the hosted site:
`https://atlas-software.docs.cern.ch/`

The `atlas-docs-expert` subagent implements the two-tier lookup: grep locally
for page discovery → WebFetch the hosted URL for authoritative content.

## Pre-commit / formatting

```bash
pixi run pre-commit     # run all hooks on all files
```

Hooks enforce: JSON/YAML validity, trailing whitespace, mixed line endings,
Markdown prose wrapping (prettier, 80 cols), and spell-checking. The `codespell`
dictionary `"-L hist,gaus"` whitelists HEP-specific words.

## Commit conventions

Conventional Commits format:

```text
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
listed in `plugins/atlas/VENDORED-LICENSES.md`. Individual skill files carry no
attribution markers — the license file satisfies BSD 3-Clause requirements. When
updating a vendored skill, rewrite from expert knowledge rather than copying
upstream verbatim.
