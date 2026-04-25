#!/usr/bin/env python3
"""Sync README.md Plugins and Repository Layout sections from the filesystem.

Usage:
    python scripts/sync_skills.py           # update README in-place
    python scripts/sync_skills.py --check   # exit 1 if README is out of date
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"

START_MARKER = "<!-- UPDATE:START -->"
END_MARKER = "<!-- UPDATE:END -->"


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract name and description from YAML frontmatter (no external deps)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = m.group(1)
    result: dict[str, str] = {}

    name_m = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    if name_m:
        result["name"] = name_m.group(1).strip()

    def _read_field(field: str) -> str | None:
        """Read any YAML scalar form: >- block, inline, or wrapped continuation."""
        # Explicit block scalar (>- or >)
        block = re.search(
            rf"^{field}:\s*(?:>-|>)\s*\n((?:[ \t]+\S[^\n]*\n?)+)",
            fm,
            re.MULTILINE,
        )
        if block:
            return " ".join(ln.strip() for ln in block.group(1).splitlines() if ln.strip())
        # Inline single-line value
        inline = re.search(rf"^{field}:\s*(.+)$", fm, re.MULTILINE)
        if inline:
            return inline.group(1).strip()
        # Prettier may wrap a plain value onto indented continuation lines
        # without a >- marker; fold them into a single space-joined string.
        wrapped = re.search(
            rf"^{field}:\s*\n((?:[ \t]+\S[^\n]*\n?)+)",
            fm,
            re.MULTILINE,
        )
        if wrapped:
            return " ".join(ln.strip() for ln in wrapped.group(1).splitlines() if ln.strip())
        return None

    for field in ("description", "readme_description"):
        val = _read_field(field)
        if val is not None:
            result[field] = val

    return result


def _short_desc(description: str) -> str:
    """Shorten 'Use when X, Y, Z ...' to a compact one-clause summary.

    Strategy: strip the 'Use when' prefix, then split at the first colon that
    is not part of '://' (avoids cutting into URL schemes), if that colon falls
    in a reasonable range.  Otherwise truncate at a word boundary near 80 chars.
    """
    desc = re.sub(r"^[Uu]se when\s+", "", description)
    desc = re.sub(r"\s+", " ", desc).strip()
    # Find a natural split point: colon that is not followed by //
    colon_m = re.search(r":(?!//)", desc)
    if colon_m and 15 <= colon_m.start() <= 70:
        desc = desc[: colon_m.start()]
    elif len(desc) > 80:
        desc = desc[:80].rsplit(" ", 1)[0] + "..."
    # Remove dangling open parenthesis from a mid-paren split
    desc = re.sub(r"\s*\([^)]*$", "", desc)
    if desc:
        desc = desc[0].upper() + desc[1:]
    return desc.rstrip(".,;")


# ---------------------------------------------------------------------------
# Markdown table builder
# ---------------------------------------------------------------------------


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [
        max(len(h), max((len(r[i]) for r in rows), default=0))
        for i, h in enumerate(headers)
    ]

    def fmt(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([fmt(headers), sep, *[fmt(r) for r in rows]])


# ---------------------------------------------------------------------------
# Content generators
# ---------------------------------------------------------------------------


def _plugins_section(marketplace: dict) -> list[str]:
    parts: list[str] = ["## Plugins\n"]

    for entry in marketplace["plugins"]:
        name = entry["name"]
        plugin_dir = ROOT / "plugins" / name

        plugin_info = json.loads(
            (plugin_dir / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        parts.append(f"### `{name}`\n\n{plugin_info.get('description', '')}\n")

        # Agents
        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            agent_files = sorted(agents_dir.glob("*.md"))
            if agent_files:
                parts.append(
                    "**Subagents** (invoked automatically or via"
                    " `Agent(subagent_type=...)`):\n"
                )
                rows = []
                for af in agent_files:
                    fm = _parse_frontmatter(af)
                    # readme_description is a short curated summary stored in
                    # agent frontmatter; fall back to auto-deriving from description
                    rdesc = fm.get("readme_description") or _short_desc(fm.get("description", ""))
                    rows.append([f"`{fm.get('name', af.stem)}`", rdesc])
                parts.append(_md_table(["Subagent", "Purpose"], rows))
                parts.append("")

        # Skills
        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            skill_files = sorted(skills_dir.glob("*/SKILL.md"))
            if skill_files:
                parts.append("**Skills:**\n")
                rows = []
                for sf in skill_files:
                    fm = _parse_frontmatter(sf)
                    rows.append([f"`{fm.get('name', sf.parent.name)}`", _short_desc(fm.get("description", ""))])
                parts.append(_md_table(["Skill", "Description"], rows))
                parts.append("")

        # MCP servers
        mcp_path = plugin_dir / ".mcp.json"
        if mcp_path.exists():
            mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
            servers = mcp.get("mcpServers", {})
            if servers:
                parts.append(
                    f"**MCP servers** (configured in `plugins/{name}/.mcp.json`):\n"
                )
                rows = []
                for sname, cfg in servers.items():
                    cmd = " ".join([cfg.get("command", "")] + cfg.get("args", []))
                    rows.append([f"`{sname}`", f"`{cmd}`", cfg.get("description", "")])
                parts.append(_md_table(["Server", "Launch command", "Purpose"], rows))
                parts.append("")

                if "rucio" in servers and servers["rucio"].get("env"):
                    parts.extend([
                        "**Required environment variables for Rucio MCP:**\n",
                        "```bash",
                        "export RUCIO_ACCOUNT=yourusername        # required — no default",
                        'export RUCIO_AUTH_TYPE=x509_proxy        # default; or "oidc" / "userpass"',
                        "voms-proxy-init --voms atlas             # obtain a valid proxy first",
                        "```\n",
                    ])

        parts.append("---\n")

    # Drop trailing separator
    while parts and parts[-1].strip() in ("---", ""):
        parts.pop()

    return parts


def _layout_section(marketplace: dict) -> list[str]:
    parts: list[str] = ["## Repository Layout\n"]
    lines = ["```text", "plugins/"]

    for entry in marketplace["plugins"]:
        name = entry["name"]
        plugin_dir = ROOT / "plugins" / name
        lines.append(f"  {name}/")
        lines.append("    .claude-plugin/plugin.json")
        if (plugin_dir / ".mcp.json").exists():
            lines.append("    .mcp.json")
        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            n = len(list(agents_dir.glob("*.md")))
            lines.append(f"    agents/  # {n} subagent{'s' if n != 1 else ''}")
        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            n = len(list(skills_dir.glob("*/SKILL.md")))
            lines.append(f"    skills/  # {n} skill{'s' if n != 1 else ''}")
        if (plugin_dir / "VENDORED-LICENSES.md").exists():
            lines.append("    VENDORED-LICENSES.md")

    lines.extend([".claude-plugin/marketplace.json", "```"])
    parts.append("\n".join(lines))
    return parts


def _generate(marketplace: dict) -> str:
    parts = _plugins_section(marketplace) + [""] + _layout_section(marketplace)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# README update
# ---------------------------------------------------------------------------


def sync() -> None:
    """Replace README content between markers."""
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    new_body = _generate(marketplace)

    text = README.read_text(encoding="utf-8")
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    if start == -1 or end == -1:
        print(f"ERROR: markers {START_MARKER!r} / {END_MARKER!r} not found in {README}", file=sys.stderr)
        sys.exit(1)

    updated = text[: start + len(START_MARKER)] + "\n\n" + new_body + "\n\n" + text[end:]
    if updated == text:
        print("README.md already up to date.")
        return
    README.write_text(updated, encoding="utf-8")
    print(f"Updated {README.relative_to(ROOT)}")


def main() -> None:
    sync()


if __name__ == "__main__":
    main()
