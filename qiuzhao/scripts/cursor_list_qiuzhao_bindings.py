import json
import os
import sqlite3
from pathlib import Path

TARGET_NAMES = ("秋招",)
db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
projects = {p["id"]: p for p in json.loads(cur.fetchone()[0])}

cur.execute("SELECT value FROM ItemTable WHERE key='composer.composerHeaders'")
headers = json.loads(cur.fetchone()[0] or "[]")
name_by_id = {}
ws_by_id = {}
for h in headers:
    if isinstance(h, dict):
        cid = h.get("composerId") or h.get("id")
        if cid:
            name_by_id[cid] = h.get("name")
            ws_by_id[cid] = h.get("workspaceIdentifier") or h.get("workspace")

cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
membership = json.loads(cur.fetchone()[0])

for cid, pid in membership.items():
    name = str(name_by_id.get(cid) or "")
    if any(k in name for k in TARGET_NAMES):
        proj = projects.get(pid, {})
        print(f"{name} | composer={cid} | project={pid} | project_name={proj.get('name')} | ws={ws_by_id.get(cid, {}).get('id') if isinstance(ws_by_id.get(cid), dict) else ws_by_id.get(cid)}")

conn.close()
