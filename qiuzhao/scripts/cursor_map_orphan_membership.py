import json
import os
import sqlite3
from pathlib import Path

OUT = Path(__file__).with_name("_membership_orphan_map.txt")
db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
projects = {p["id"]: p for p in json.loads(cur.fetchone()[0]) if isinstance(p, dict)}

orphan_project_ids = set()
for pid, p in projects.items():
    ws = p.get("workspace") or {}
    if ws.get("id") == "7aeeac556a461eec32a7969003d273b7":
        orphan_project_ids.add(pid)

cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
membership = json.loads(cur.fetchone()[0])

lines = [f"orphan_project_ids={sorted(orphan_project_ids)}"]
for composer_id, project_id in membership.items():
    if project_id in orphan_project_ids:
        proj = projects.get(project_id, {})
        lines.append(
            f"composer={composer_id} -> project={project_id} name={proj.get('name')}"
        )

# also map composer names from headers
cur.execute("SELECT value FROM ItemTable WHERE key='composer.composerHeaders'")
row = cur.fetchone()
headers = json.loads(row[0]) if row and row[0] else []
name_by_id = {}
for h in headers:
    if isinstance(h, dict):
        cid = h.get("composerId") or h.get("id")
        if cid:
            name_by_id[cid] = h.get("name")

lines.append("\nWith composer header names:")
for line in lines[1:]:
    if line.startswith("composer="):
        cid = line.split("composer=")[1].split(" ")[0]
        lines.append(f"  header_name={name_by_id.get(cid)}")

conn.close()
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT} lines={len(lines)}")
