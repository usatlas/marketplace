#!/usr/bin/env python3
"""Sync a plugin's or the workspace's version into .claude-plugin/marketplace.json.

Invoked as a tbump `before_commit` hook so a version bump keeps
marketplace.json in sync with the manifest(s) it was bumped from, instead of
requiring a separate by-hand edit:

* Each plugin's own tbump.toml (plugins/<plugin>/tbump.toml) calls this with
  a plugin name, to update that plugin's `plugins[].version` entry.
* The top-level tbump.toml calls this with --metadata, to update the
  workspace-wide `metadata.version` entry.

Usage: sync_marketplace_version.py <plugin-name> <new-version>
       sync_marketplace_version.py --metadata <new-version>
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
        print(
            f"usage: {sys.argv[0]} <plugin-name> <new-version>\n"
            f"       {sys.argv[0]} --metadata <new-version>",
            file=sys.stderr,
        )
        sys.exit(1)
    target, new_version = sys.argv[1], sys.argv[2]

    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    if target == "--metadata":
        data["metadata"]["version"] = new_version
        label = "metadata.version"
    else:
        for plugin in data["plugins"]:
            if plugin["name"] == target:
                plugin["version"] = new_version
                break
        else:
            print(
                f"{MARKETPLACE_JSON}: no plugin entry named '{target}'",
                file=sys.stderr,
            )
            sys.exit(1)
        label = target

    # json.dumps(..., indent=2) + trailing newline reproduces this repo's
    # existing marketplace.json formatting exactly (verified against
    # `jq '.'`), so this only touches the one changed line.
    MARKETPLACE_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{MARKETPLACE_JSON}: {label} -> {new_version}")


if __name__ == "__main__":
    main()
