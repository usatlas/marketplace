#!/usr/bin/env python3
"""Sync one plugin's version into .claude-plugin/marketplace.json.

Invoked as a tbump `before_commit` hook from each plugin's own tbump.toml
(plugins/<plugin>/tbump.toml) so `pixi run tbump-<plugin> <version>` keeps
marketplace.json's `plugins[].version` entry in sync with the plugin's own
manifest, instead of requiring a separate by-hand edit.

Usage: sync_marketplace_version.py <plugin-name> <new-version>
Exit code 0 on success, 1 if the plugin name isn't found in marketplace.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"


def main() -> None:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <plugin-name> <new-version>", file=sys.stderr)
        sys.exit(1)
    plugin_name, new_version = sys.argv[1], sys.argv[2]

    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    for plugin in data["plugins"]:
        if plugin["name"] == plugin_name:
            plugin["version"] = new_version
            break
    else:
        print(
            f"{MARKETPLACE_JSON}: no plugin entry named '{plugin_name}'",
            file=sys.stderr,
        )
        sys.exit(1)

    # json.dumps(..., indent=2) + trailing newline reproduces this repo's
    # existing marketplace.json formatting exactly (verified against
    # `jq '.'`), so this only touches the one changed line.
    MARKETPLACE_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{MARKETPLACE_JSON}: {plugin_name} -> {new_version}")


if __name__ == "__main__":
    main()
