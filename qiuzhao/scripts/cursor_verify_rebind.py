#!/usr/bin/env python3
"""Verify work workspace binding after cursor_fix_work_binding.py."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

OUT = Path(__file__).with_name("_rebind_verify.txt")
APPDATA = Path(os.environ["APPDATA"]) / "Cursor" / "User"
GLOBAL_DB = APPDATA / "globalStorage" / "state.vscdb"
TARGET_WS = "a23eec696091501088cbffe13c90d4f8"
TARGET_PROJECT = "f846d8c4-96bb-46bc-b2d5-4e8c265935ef"
BAD = ("1786347249089", ".cursor/plans/work.code-workspace", "7aeeac556a461eec32a7969003d273b7")
QIUZHAO_IDS = [
    "f590d2c9-8fee-4e0d-93ee-6c03974a53e9",
    "f4433eaf-cad0-4526-9db7-bc9e34b58649",
    "91b0ae70-f811-477e-a925-7a8ffb24d10a",
    "be98ab58-dee7-4f76-aa09-5da7f85ac341",
]


def main() -> None:
    lines: list[str] = []
    plans_ws = Path(r"C:\Users\xd\.cursor\plans\work.code-workspace")
    repo_ws = Path(r"D:\AgentProjects\work\work.code-workspace")
    orphan_json = Path(os.environ["APPDATA"]) / "Cursor/Workspaces/1786347249089/workspace.json"

    lines.append(f"plans_work_code_workspace_exists={plans_ws.exists()}")
    lines.append(f"repo_work_code_workspace_exists={repo_ws.exists()}")
    lines.append(f"orphan_workspace_json_exists={orphan_json.exists()}")

    conn = sqlite3.connect(GLOBAL_DB)
    cur = conn.cursor()

    cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
    membership = json.loads(cur.fetchone()[0])
    for cid in QIUZHAO_IDS:
        lines.append(f"membership[{cid[:8]}]={membership.get(cid)}")

    cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
    projects = json.loads(cur.fetchone()[0])
    work_projects = []
    bad_refs = []
    for p in projects:
        blob = json.dumps(p, ensure_ascii=False)
        if any(b in blob for b in BAD):
            bad_refs.append(p.get("name"))
        ws = p.get("workspace") or {}
        if ws.get("id") == TARGET_WS:
            work_projects.append(f"{p.get('name')} ({p.get('id')[:8]})")
    lines.append(f"work_glass_projects={work_projects}")
    lines.append(f"bad_glass_project_refs={bad_refs}")

    cur.execute("SELECT value FROM ItemTable WHERE key='workspaceMetadata.entries'")
    meta = json.loads(cur.fetchone()[0])
    meta_bad = []
    meta_work = False
    for e in meta.get("entries", []):
        blob = json.dumps(e, ensure_ascii=False)
        if any(b in blob for b in BAD):
            meta_bad.append(e.get("workspaceId"))
        if e.get("workspaceId") == TARGET_WS:
            meta_work = True
    lines.append(f"metadata_has_work={meta_work}")
    lines.append(f"metadata_bad_refs={meta_bad}")

    cur.execute("SELECT value FROM ItemTable WHERE key='composer.composerHeaders'")
    headers = json.loads(cur.fetchone()[0] or "[]")
    for h in headers:
        if not isinstance(h, dict):
            continue
        cid = h.get("composerId") or h.get("id")
        if cid not in QIUZHAO_IDS:
            continue
        ws = h.get("workspaceIdentifier") or h.get("workspace") or {}
        ws_id = ws.get("id") if isinstance(ws, dict) else ws
        lines.append(f"header[{str(cid)[:8]}] name={h.get('name')} ws_id={ws_id}")

    conn.close()
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
