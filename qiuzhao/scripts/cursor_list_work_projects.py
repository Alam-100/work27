import json
import os
import sqlite3
from pathlib import Path

db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjects.v1'")
for p in json.loads(cur.fetchone()[0]):
    ws = (p or {}).get("workspace") or {}
    if ws.get("id") == "a23eec696091501088cbffe13c90d4f8":
        print(p.get("id"), p.get("name"))
conn.close()
