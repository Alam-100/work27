import json
import os
import sqlite3
from pathlib import Path

APPDATA = Path(os.environ["APPDATA"]) / "Cursor/User"
global_db = APPDATA / "globalStorage/state.vscdb"
conn = sqlite3.connect(global_db)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
row = cur.fetchone()
projects = json.loads(row[0])
for p in projects:
    ws = p.get("workspace") or {}
    cfg = ws.get("configPath") or {}
    ext = cfg.get("external") or ws.get("uri", {}).get("external") or ""
    if "1786347249089" in ext or ws.get("id") == "7aeeac556a461eec32a7969003d273b7":
        print(json.dumps(p, ensure_ascii=False, indent=2))

cur.execute("SELECT value FROM ItemTable WHERE key='workspaceMetadata.entries'")
row = cur.fetchone()
meta = json.loads(row[0])
for e in meta.get("entries", []):
    if e.get("workspaceId") == "7aeeac556a461eec32a7969003d273b7" or "1786347249089" in json.dumps(e, ensure_ascii=False):
        print("META:", json.dumps(e, ensure_ascii=False, indent=2))

conn.close()
