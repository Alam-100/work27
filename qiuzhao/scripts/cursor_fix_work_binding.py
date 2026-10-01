#!/usr/bin/env python3
"""Fix work workspace chat binding: clean orphan/plans identities, unify membership."""

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

TARGET_WS = "a23eec696091501088cbffe13c90d4f8"
ORPHAN_WS = "7aeeac556a461eec32a7969003d273b7"
PLANS_WS_IDS = {
    "e32b46c2337b38d41c225a038898d736",
    "b03ad64bd75c784718dc3526f5f86576",
}
BAD_MARKERS = (
    "1786347249089",
    ".cursor/plans/work.code-workspace",
    ".cursor\\plans\\work.code-workspace",
    ORPHAN_WS,
)
TARGET_PROJECT_ID = "f846d8c4-96bb-46bc-b2d5-4e8c265935ef"
MERGE_PROJECT_IDS = {
    "74d405a4-80e1-4ddc-ac41-72cd79ac6182",  # Explore qiuzhao vault layout
}
QIUZHAO_KEYWORDS = ("秋招",)
TARGET_URI = {
    "$mid": 1,
    "fsPath": "d:\\AgentProjects\\work",
    "_sep": 1,
    "external": "file:///d%3A/AgentProjects/work",
    "path": "/d:/AgentProjects/work",
    "scheme": "file",
}
TARGET_WORKSPACE = {"id": TARGET_WS, "uri": TARGET_URI}

BACKUP_DBS = [
    GLOBAL_DB,
    APPDATA / "workspaceStorage" / TARGET_WS / "state.vscdb",
    APPDATA / "workspaceStorage" / ORPHAN_WS / "state.vscdb",
    APPDATA / "workspaceStorage" / "e32b46c2337b38d41c225a038898d736" / "state.vscdb",
    APPDATA / "workspaceStorage" / "b03ad64bd75c784718dc3526f5f86576" / "state.vscdb",
]


def backup_db(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = path.with_suffix(path.suffix + f".backup-{stamp}")
    shutil.copy2(path, dest)
    return dest


def load_json(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def workspace_blob(ws: dict | None) -> str:
    if not ws:
        return ""
    return json.dumps(ws, ensure_ascii=False)


def is_bad_workspace(ws: dict | None) -> bool:
    if not isinstance(ws, dict):
        return False
    blob = workspace_blob(ws).lower()
    if ws.get("id") in PLANS_WS_IDS or ws.get("id") == ORPHAN_WS:
        return True
    return any(m.lower() in blob for m in BAD_MARKERS)


def normalize_workspace(ws: dict | None) -> dict:
    return copy.deepcopy(TARGET_WORKSPACE)


def iter_composer_names(conn: sqlite3.Connection) -> dict[str, str]:
    names: dict[str, str] = {}
    cur = conn.cursor()
    cur.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerHeaders'")
    row = cur.fetchone()
    if row and row[0]:
        data = load_json(row[0])
        if isinstance(data, list):
            for h in data:
                if isinstance(h, dict):
                    cid = str(h.get("composerId") or h.get("id") or "")
                    if cid:
                        names[cid] = str(h.get("name") or h.get("subtitle") or "")
    cur.execute("SELECT key, value FROM cursorDiskKV")
    for key, value in cur.fetchall():
        if not key or not value or not key.startswith("composerData:"):
            continue
        data = load_json(value)
        if isinstance(data, dict):
            cid = str(data.get("composerId") or data.get("id") or key.split(":", 1)[-1])
            names[cid] = str(data.get("name") or names.get(cid) or "")
    return names


def update_projects(projects: list) -> tuple[list, int, set[str]]:
    changed = 0
    removed_project_ids: set[str] = set()
    out: list = []
    target_seen = False

    for item in projects:
        if not isinstance(item, dict):
            out.append(item)
            continue

        pid = item.get("id")
        ws = item.get("workspace") or {}
        ws_id = ws.get("id")

        # Drop glass projects bound to plans/orphan workspace identities
        if ws_id in PLANS_WS_IDS or ws_id == ORPHAN_WS or is_bad_workspace(ws):
            if pid and pid not in {TARGET_PROJECT_ID}:
                removed_project_ids.add(str(pid))
            changed += 1
            continue

        new_item = copy.deepcopy(item)
        if ws_id == TARGET_WS or (
            isinstance(ws.get("uri"), dict)
            and "agentprojects/work" in str(ws["uri"].get("external", "")).lower()
        ):
            new_item["workspace"] = normalize_workspace(ws)
            if pid == TARGET_PROJECT_ID:
                new_item["name"] = "秋招"
                target_seen = True
            changed += 1
        out.append(new_item)

    if not target_seen:
        out.append(
            {
                "id": TARGET_PROJECT_ID,
                "name": "秋招",
                "workspace": copy.deepcopy(TARGET_WORKSPACE),
                "createdAt": int(datetime.now().timestamp() * 1000),
                "lastUpdatedAt": int(datetime.now().timestamp() * 1000),
                "isArchived": False,
            }
        )
        changed += 1

    return out, changed, removed_project_ids


def update_membership(
    membership: dict,
    composer_names: dict[str, str],
    removed_project_ids: set[str],
) -> tuple[dict, int]:
    changed = 0
    out = copy.deepcopy(membership)
    merge_ids = MERGE_PROJECT_IDS | removed_project_ids

    for composer_id, project_id in membership.items():
        name = composer_names.get(composer_id, "")
        should_move = project_id in merge_ids or any(k in name for k in QIUZHAO_KEYWORDS)
        if should_move and out.get(composer_id) != TARGET_PROJECT_ID:
            out[composer_id] = TARGET_PROJECT_ID
            changed += 1

    return out, changed


def update_workspace_metadata(metadata: dict) -> tuple[dict, int]:
    entries = metadata.get("entries") or []
    kept = []
    removed = 0
    work_exists = False

    for entry in entries:
        if not isinstance(entry, dict):
            kept.append(entry)
            continue
        ws_id = entry.get("workspaceId")
        blob = json.dumps(entry, ensure_ascii=False)
        if ws_id in PLANS_WS_IDS or ws_id == ORPHAN_WS or any(m in blob for m in BAD_MARKERS):
            removed += 1
            continue
        if ws_id == TARGET_WS:
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

    return {"entries": kept}, removed


def update_composer_headers(conn: sqlite3.Connection, composer_names: dict[str, str]) -> int:
    changed = 0
    cur = conn.cursor()
    cur.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerHeaders'")
    row = cur.fetchone()
    if not row or not row[0]:
        return 0
    data = load_json(row[0])
    if not isinstance(data, list):
        return 0

    for item in data:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("composerId") or item.get("id") or "")
        name = composer_names.get(cid, str(item.get("name") or ""))
        ws = item.get("workspaceIdentifier") or item.get("workspace")
        if any(k in name for k in QIUZHAO_KEYWORDS) or is_bad_workspace(ws if isinstance(ws, dict) else None):
            item["workspaceIdentifier"] = copy.deepcopy(TARGET_WORKSPACE)
            if "workspace" in item:
                item["workspace"] = copy.deepcopy(TARGET_WORKSPACE)
            changed += 1

    if changed:
        cur.execute(
            "UPDATE ItemTable SET value = ? WHERE key = 'composer.composerHeaders'",
            (json.dumps(data, ensure_ascii=False),),
        )
    return changed


def update_composer_disk_kv(conn: sqlite3.Connection, composer_names: dict[str, str]) -> int:
    changed = 0
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM cursorDiskKV")
    for key, value in cur.fetchall():
        if not key or not value or not key.startswith("composerData:"):
            continue
        data = load_json(value)
        if not isinstance(data, dict):
            continue
        cid = str(data.get("composerId") or data.get("id") or key.split(":", 1)[-1])
        name = composer_names.get(cid, str(data.get("name") or ""))
        ws = data.get("workspaceIdentifier") or data.get("workspace")
        if not (any(k in name for k in QIUZHAO_KEYWORDS) or is_bad_workspace(ws if isinstance(ws, dict) else None)):
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


def merge_work_sidebar(composer_ids: set[str], composer_names: dict[str, str]) -> int:
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
    for cid in composer_ids:
        if cid in existing:
            continue
        composers.append(
            {
                "type": "head",
                "composerId": cid,
                "name": composer_names.get(cid) or f"chat-{cid[:8]}",
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
    return added


def backup_all() -> list[str]:
    lines = []
    for path in BACKUP_DBS:
        dest = backup_db(path)
        if dest:
            lines.append(f"backed up {path} -> {dest}")
        else:
            lines.append(f"skip missing {path}")
    return lines


def fix(dry_run: bool = False) -> int:
    conn = sqlite3.connect(GLOBAL_DB)
    composer_names = iter_composer_names(conn)
    cur = conn.cursor()

    cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
    projects = load_json(cur.fetchone()[0]) or []
    new_projects, projects_changed, removed_pids = update_projects(projects)

    cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
    membership = load_json(cur.fetchone()[0]) or {}
    new_membership, membership_changed = update_membership(
        membership, composer_names, removed_pids
    )

    cur.execute("SELECT value FROM ItemTable WHERE key='workspaceMetadata.entries'")
    new_metadata, metadata_removed = update_workspace_metadata(load_json(cur.fetchone()[0]) or {})

    qiuzhao_composers = {
        cid for cid, name in composer_names.items() if any(k in name for k in QIUZHAO_KEYWORDS)
    }
    moved_composers = {
        cid for cid, pid in new_membership.items() if pid == TARGET_PROJECT_ID and cid in qiuzhao_composers
    }

    report = {
        "projects_changed": projects_changed,
        "removed_project_ids": sorted(removed_pids),
        "membership_changed": membership_changed,
        "metadata_entries_removed": metadata_removed,
        "qiuzhao_composers": sorted(qiuzhao_composers),
        "target_project": TARGET_PROJECT_ID,
    }

    if dry_run:
        conn.close()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    backups = backup_all()
    for line in backups:
        print(line)

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
    headers_changed = update_composer_headers(conn, composer_names)
    disk_changed = update_composer_disk_kv(conn, composer_names)
    conn.commit()
    conn.close()

    sidebar_added = merge_work_sidebar(moved_composers, composer_names)
    report["headers_changed"] = headers_changed
    report["disk_changed"] = disk_changed
    report["sidebar_added"] = sidebar_added

    out = Path(__file__).with_name("_fix_work_binding_report.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report: {out}")
    print("Done. Restart Cursor and Open Folder -> D:\\AgentProjects\\work")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--backup-only", action="store_true")
    args = parser.parse_args()

    if args.backup_only:
        for line in backup_all():
            print(line)
        return 0
    if args.fix:
        return fix(dry_run=args.dry_run)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
