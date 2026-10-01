#!/usr/bin/env python3
"""Rebind orphaned Cursor agent chats to the work workspace."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


APPDATA = Path(os.environ["APPDATA"]) / "Cursor" / "User"
GLOBAL_DB = APPDATA / "globalStorage" / "state.vscdb"
ORPHAN_WS = "7aeeac556a461eec32a7969003d273b7"
TARGET_WS = "a23eec696091501088cbffe13c90d4f8"
TARGET_FOLDER = "file:///d%3A/AgentProjects/work"
ORPHAN_WORKSPACE_URI = (
    "file:///c%3A/Users/xd/AppData/Roaming/Cursor/Workspaces/1786347249089/workspace.json"
)
KEYWORDS = ("秋招",)


def backup_db(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = path.with_suffix(path.suffix + f".backup-{stamp}")
    shutil.copy2(path, dest)
    return dest


def load_json(raw: str | None) -> dict | list | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def iter_composer_headers(conn: sqlite3.Connection) -> list[dict]:
    headers: list[dict] = []
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM ItemTable WHERE key = 'composer.composerHeaders'")
    row = cur.fetchone()
    if row and row[1]:
        data = load_json(row[1])
        if isinstance(data, list):
            headers.extend(x for x in data if isinstance(x, dict))

    cur.execute("SELECT key, value FROM cursorDiskKV")
    for key, value in cur.fetchall():
        if not key or not value:
            continue
        if "composerHeader" in key or key.startswith("composerData:"):
            data = load_json(value)
            if isinstance(data, dict) and data.get("composerId"):
                headers.append(data)
    return headers


def matches_chat(header: dict) -> bool:
    name = str(header.get("name") or header.get("subtitle") or "")
    return any(k in name for k in KEYWORDS)


def workspace_matches(header: dict) -> bool:
    ws = header.get("workspaceIdentifier") or header.get("workspace") or {}
    if isinstance(ws, str):
        return ORPHAN_WORKSPACE_URI in ws or ORPHAN_WS in ws
    if isinstance(ws, dict):
        uri = str(ws.get("uri") or ws.get("id") or "")
        return (
            ORPHAN_WORKSPACE_URI in uri
            or ORPHAN_WS in uri
            or "1786347249089" in uri
        )
    return False


def make_target_workspace() -> dict:
    return {
        "id": TARGET_WS,
        "uri": TARGET_FOLDER,
        "configPath": TARGET_FOLDER,
    }


def list_chats(orphan_only: bool = False) -> None:
    conn = sqlite3.connect(GLOBAL_DB)
    headers = iter_composer_headers(conn)
    conn.close()

    print(f"Found {len(headers)} composer headers total\n")
    for h in headers:
        name = h.get("name") or h.get("subtitle") or "(unnamed)"
        cid = h.get("composerId") or h.get("id") or "?"
        ws = h.get("workspaceIdentifier") or h.get("workspace")
        is_orphan = workspace_matches(h)
        if orphan_only and not is_orphan:
            continue
        flag = ""
        if matches_chat(h):
            flag += " [MATCH keyword]"
        if is_orphan:
            flag += " [ORPHAN ws]"
        print(f"- {name}")
        print(f"  id: {cid}")
        print(f"  workspace: {ws}{flag}\n")

    ws_db = APPDATA / "workspaceStorage" / ORPHAN_WS / "state.vscdb"
    if ws_db.exists():
        conn = sqlite3.connect(ws_db)
        cur = conn.cursor()
        cur.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
        row = cur.fetchone()
        conn.close()
        data = load_json(row[0] if row else None)
        composers = (data or {}).get("allComposers") if isinstance(data, dict) else []
        print(f"Orphan workspace index entries: {len(composers or [])}")
        for item in composers or []:
            if isinstance(item, dict):
                print(
                    f"  - {item.get('name')} ({item.get('composerId') or item.get('id')})"
                )


def update_item_table_headers(conn: sqlite3.Connection, ids: set[str]) -> int:
    cur = conn.cursor()
    cur.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerHeaders'")
    row = cur.fetchone()
    if not row or not row[0]:
        return 0
    data = load_json(row[0])
    if not isinstance(data, list):
        return 0
    changed = 0
    target = make_target_workspace()
    for item in data:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("composerId") or item.get("id") or "")
        if cid not in ids and not (matches_chat(item) and workspace_matches(item)):
            continue
        item["workspaceIdentifier"] = target
        if "workspace" in item:
            item["workspace"] = target
        changed += 1
    if changed:
        cur.execute(
            "UPDATE ItemTable SET value = ? WHERE key = 'composer.composerHeaders'",
            (json.dumps(data, ensure_ascii=False),),
        )
    return changed


def update_workspace_db(ws_id: str, composer_ids: set[str], remove: bool) -> int:
    ws_db = APPDATA / "workspaceStorage" / ws_id / "state.vscdb"
    if not ws_db.exists():
        return 0
    conn = sqlite3.connect(ws_db)
    cur = conn.cursor()
    cur.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cur.fetchone()
    if not row or not row[0]:
        conn.close()
        return 0
    data = load_json(row[0])
    if not isinstance(data, dict):
        conn.close()
        return 0
    composers = data.get("allComposers") or []
    if not isinstance(composers, list):
        conn.close()
        return 0

    changed = 0
    if remove:
        new_list = []
        for item in composers:
            if not isinstance(item, dict):
                new_list.append(item)
                continue
            cid = str(item.get("composerId") or item.get("id") or "")
            if cid in composer_ids:
                changed += 1
                continue
            new_list.append(item)
        composers = new_list
    else:
        existing = {
            str(x.get("composerId") or x.get("id") or "")
            for x in composers
            if isinstance(x, dict)
        }
        for cid in composer_ids:
            if cid in existing:
                continue
            composers.append(
                {
                    "type": "head",
                    "composerId": cid,
                    "name": f"migrated-{cid[:8]}",
                    "createdAt": datetime.now().isoformat(),
                }
            )
            changed += 1

    data["allComposers"] = composers
    cur.execute(
        "UPDATE ItemTable SET value = ? WHERE key = 'composer.composerData'",
        (json.dumps(data, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()
    return changed


def rebind(dry_run: bool = False) -> int:
    conn = sqlite3.connect(GLOBAL_DB)
    headers = iter_composer_headers(conn)
    target_ids: set[str] = set()
    for h in headers:
        if matches_chat(h) and (workspace_matches(h) or True):
            cid = str(h.get("composerId") or h.get("id") or "")
            if cid:
                target_ids.add(cid)

    if not target_ids:
        print("No matching composer IDs found.")
        conn.close()
        return 1

    print("Will rebind composer IDs:")
    for cid in sorted(target_ids):
        print(f"  - {cid}")

    if dry_run:
        conn.close()
        return 0

    backup_db(GLOBAL_DB)
    backup_db(APPDATA / "workspaceStorage" / ORPHAN_WS / "state.vscdb")
    backup_db(APPDATA / "workspaceStorage" / TARGET_WS / "state.vscdb")

    changed_global = update_item_table_headers(conn, target_ids)
    conn.commit()
    conn.close()

    removed = update_workspace_db(ORPHAN_WS, target_ids, remove=True)
    added = update_workspace_db(TARGET_WS, target_ids, remove=False)

    print(f"Global headers updated: {changed_global}")
    print(f"Removed from orphan workspace index: {removed}")
    print(f"Added to work workspace index: {added}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--orphan-only", action="store_true")
    parser.add_argument("--rebind", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list:
        list_chats(orphan_only=args.orphan_only)
        return 0
    if args.rebind:
        return rebind(dry_run=args.dry_run)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
