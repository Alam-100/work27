import json
import os
import sqlite3
from pathlib import Path

APPDATA = Path(os.environ["APPDATA"]) / "Cursor/User"
global_db = APPDATA / "globalStorage/state.vscdb"
needles = ["1786347249089", "7aeeac556a461eec32a7969003d273b7", "秋招：面试模拟", "秋招信息收集"]

conn = sqlite3.connect(global_db)
cur = conn.cursor()

for table in ["ItemTable", "cursorDiskKV"]:
    cur.execute(f"SELECT key, value FROM {table}")
    for key, value in cur.fetchall():
        if not value:
            continue
        text = value if isinstance(value, str) else value.decode("utf-8", errors="ignore")
        if any(n in text for n in needles):
            print("=" * 80)
            print(f"TABLE={table} KEY={key[:120]}")
            if len(text) < 4000:
                print(text[:4000])
            else:
                print(text[:800], "...")

# Also inspect work workspace index
work_db = APPDATA / "workspaceStorage/a23eec696091501088cbffe13c90d4f8/state.vscdb"
conn2 = sqlite3.connect(work_db)
cur2 = conn2.cursor()
cur2.execute("SELECT value FROM ItemTable WHERE key='composer.composerData'")
row = cur2.fetchone()
if row:
    data = json.loads(row[0])
    for c in data.get("allComposers", []):
        name = c.get("name") or ""
        if "秋招" in name or "Restoring" in name:
            print("WORK INDEX:", name, c.get("composerId"))

conn.close()
conn2.close()
