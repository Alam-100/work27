import json
import os
import sqlite3
from pathlib import Path

db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT key, length(value) FROM ItemTable WHERE key LIKE 'glass.%'")
for key, ln in cur.fetchall():
    print(key, ln)

for key in [
    "glass.localAgentProjects.v1",
    "glass.localAgents.v1",
    "glass.localAgentSessions.v1",
    "glass.agents.v1",
]:
    cur.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
    row = cur.fetchone()
    if not row:
        continue
    print("\n===", key, "===")
    data = json.loads(row[0])
    if isinstance(data, list):
        for item in data:
            text = json.dumps(item, ensure_ascii=False)
            if "1786347249089" in text or "7aeeac556a461eec32a7969003d273b7" in text or "秋招" in text:
                print(text[:2000])
    elif isinstance(data, dict):
        text = json.dumps(data, ensure_ascii=False)
        if "1786347249089" in text or "秋招" in text:
            print(text[:4000])

conn.close()
