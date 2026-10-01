import json
import os
import sqlite3
from pathlib import Path

db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
data = json.loads(cur.fetchone()[0])
print(type(data), len(data) if isinstance(data, (list, dict)) else "")
if isinstance(data, dict):
    for k, v in data.items():
        text = json.dumps(v, ensure_ascii=False)
        if any(x in text for x in ["1786347249089", "7aeeac556a461eec32a7969003d273b7", "秋招"]):
            print("KEY", k)
            print(text[:3000])
            print()
elif isinstance(data, list):
    for item in data:
        text = json.dumps(item, ensure_ascii=False)
        if any(x in text for x in ["1786347249089", "7aeeac556a461eec32a7969003d273b7", "秋招"]):
            print(text[:3000])
            print()
conn.close()
