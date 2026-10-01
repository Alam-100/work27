#!/usr/bin/env python3
"""Rebind orphaned Cursor Agents Window workspace to D:/AgentProjects/work."""

from __future__ import annotations

import argparse
import copy
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
ORPHAN_PROJECT_ID = "74d405a4-80e1-4ddc-ac41-72cd79ac6182"
TARGET_PROJECT_ID = "f846d8c4-96bb-46bc-b2d5-4e8c265935ef"
TARGET_URI = {
    "$mid": 1,
    "fsPath": "d:\\AgentProjects\\work",
    "_sep": 1,
    "external": "file:///d%3A/AgentProjects/work",
    "path": "/d:/AgentProjects/work",
    "scheme": "file",
}
TARGET_WORKSPACE = {"id": TARGET_WS, "uri": TARGET_URI}


def backup_db(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = path.with_suffix(path.suffix + f".backup-{stamp}")
    shutil.copy2(path, dest)
    return dest


def load_json(raw: str | None):
    if not raw:
        return None
    return json.loads(raw)


def rebind_workspace_obj(obj: dict) -> dict:
    out = copy.deepcopy(obj)
    out["id"] = TARGET_WS
    out.pop("configPath", None)
    out["uri"] = copy.deepcopy(TARGET_URI)
    return out


def update_projects(projects: list) -> tuple[list, int]:
    changed = 0
    out = []
    for item in projects:
        if not isinstance(item, dict):
            out.append(item)
            continue
        if item.get("id") == ORPHAN_PROJECT_ID:
            new_item = copy.deepcopy(item)
            new_item["workspace"] = rebind_workspace_obj(new_item.get("workspace") or {})
            out.append(new_item)
            changed += 1
        else:
            out.append(item)
    return out, changed


def update_membership(membership: dict) -> tuple[dict, int]:
    changed = 0
    out = copy.deepcopy(membership)
    for composer_id, project_id in membership.items():
        if project_id == ORPHAN_PROJECT_ID:
            out[composer_id] = TARGET_PROJECT_ID
            changed += 1
    return out, changed


def update_workspace_metadata(metadata: dict) -> dict:
    entries = metadata.get("entries") or []
    kept = []
    work_exists = False
    for entry in entries:
        if not isinstance(entry, dict):
            kept.append(entry)
            continue
        if entry.get("workspaceId") == ORPHAN_WS:
            continue
        if entry.get("workspaceId") == TARGET_WS:
            work_exists = True
        kept.append(entry)
    if not work_exists:
        kept.append(
            {
                "workspaceId": TARGET_WS,
                "displayPath": "D:\\AgentProjects\\work",
                "worktreeInfo": {"isWorktree": False},
                "folderUri": TARGET_URI["external"],
                "paths": [
                    {
                        "uri": copy.deepcopy(TARGET_URI),
                        "displayPath": "D:\\AgentProjects\\work",
                    }
                ],
                "trackedGitRepos": [{"repoPath": "d:\\AgentProjects\\work"}],
            }
        )
    return {"entries": kept}


def update_composer_disk_kv(conn: sqlite3.Connection, composer_ids: set[str]) -> int:
    changed = 0
    cur = conn.cursor()
    for composer_id in composer_ids:
        key = f"composerData:{composer_id}"
        cur.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue
        data = load_json(row[0])
        if not isinstance(data, dict):
            continue
        data["workspaceIdentifier"] = copy.deepcopy(TARGET_WORKSPACE)
        if "workspace" in data:
            data["workspace"] = copy.deepcopy(TARGET_WORKSPACE)
        cur.execute(
            "UPDATE cursorDiskKV SET value = ? WHERE key = ?",
            (json.dumps(data, ensure_ascii=False), key),
        )
        changed += 1
    return changed


def merge_workspace_sidebar(composer_ids: set[str]) -> int:
    target_db = APPDATA / "workspaceStorage" / TARGET_WS / "state.vscdb"
    if not target_db.exists():
        return 0
    conn = sqlite3.connect(target_db)
    cur = conn.cursor()
    cur.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerData'")
    row = cur.fetchone()
    data = load_json(row[0] if row else None)
    if not isinstance(data, dict):
        conn.close()
        return 0
    composers = data.get("allComposers") or []
    existing = {
        str(x.get("composerId") or x.get("id") or "")
        for x in composers
        if isinstance(x, dict)
    }
    added = 0
    global_conn = sqlite3.connect(GLOBAL_DB)
    gcur = global_conn.cursor()
    for composer_id in composer_ids:
        if composer_id in existing:
            continue
        gcur.execute(
            "SELECT value FROM cursorDiskKV WHERE key = ?",
            (f"composerData:{composer_id}",),
        )
        grow = gcur.fetchone()
        header = load_json(grow[0] if grow else None) or {}
        composers.append(
            {
                "type": "head",
                "composerId": composer_id,
                "name": header.get("name") or f"chat-{composer_id[:8]}",
                "createdAt": header.get("createdAt"),
            }
        )
        added += 1
    data["allComposers"] = composers
    cur.execute(
        "UPDATE ItemTable SET value = ? WHERE key = 'composer.composerData'",
        (json.dumps(data, ensure_ascii=False),),
    )
    conn.commit()
    conn.close()
    global_conn.close()
    return added


def rebind(dry_run: bool = False) -> int:
    conn = sqlite3.connect(GLOBAL_DB)
    cur = conn.cursor()

    cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
    projects = load_json(cur.fetchone()[0]) or []
    new_projects, projects_changed = update_projects(projects)

    cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
    membership = load_json(cur.fetchone()[0]) or {}
    new_membership, membership_changed = update_membership(membership)
    moved_composers = {
        cid for cid, pid in membership.items() if pid == ORPHAN_PROJECT_ID
    }

    cur.execute("SELECT value FROM ItemTable WHERE key='workspaceMetadata.entries'")
    new_metadata = update_workspace_metadata(load_json(cur.fetchone()[0]) or {})

    report = {
        "projects_changed": projects_changed,
        "membership_changed": membership_changed,
        "composer_ids_moved": sorted(moved_composers),
    }

    if dry_run:
        conn.close()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    backup_db(GLOBAL_DB)
    if (APPDATA / "workspaceStorage" / TARGET_WS / "state.vscdb").exists():
        backup_db(APPDATA / "workspaceStorage" / TARGET_WS / "state.vscdb")

    cur.execute(
        "UPDATE ItemTable SET value = ? WHERE key='glass.localAgentProjects.v1'",
        (json.dumps(new_projects, ensure_ascii=False),),
    )
    cur.execute(
        "UPDATE ItemTable SET value = ? WHERE key='glass.localAgentProjectMembership.v1'",
        (json.dumps(new_membership, ensure_ascii=False),),
    )
    cur.execute(
        "UPDATE ItemTable SET value = ? WHERE key='workspaceMetadata.entries'",
        (json.dumps(new_metadata, ensure_ascii=False),),
    )
    disk_changed = update_composer_disk_kv(conn, moved_composers)
    conn.commit()
    conn.close()

    sidebar_added = merge_workspace_sidebar(moved_composers)
    report["composer_disk_changed"] = disk_changed
    report["work_sidebar_added"] = sidebar_added
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("Rebind complete. Fully restart Cursor, then open only D:\\AgentProjects\\work.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rebind", action="store_true")
    args = parser.parse_args()
    if not args.rebind:
        parser.print_help()
        return 1
    return rebind(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
