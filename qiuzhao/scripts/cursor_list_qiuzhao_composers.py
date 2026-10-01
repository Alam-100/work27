import json
import os
import sqlite3
from pathlib import Path

db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
for key, value in cur.fetchall():
    if not value:
        continue
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        continue
    name = str(data.get("name") or data.get("subtitle") or "")
    if "秋招" in name:
        cid = key.split(":", 1)[1]
        ws = data.get("workspaceIdentifier") or data.get("workspace")
        print(name, cid, ws.get("id") if isinstance(ws, dict) else ws)
conn.close()
