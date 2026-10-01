import json
import os
import sqlite3
from pathlib import Path

out = Path(__file__).with_name("_membership_shape.txt")
db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
data = json.loads(cur.fetchone()[0])
lines = [f"type={type(data).__name__}"]
if isinstance(data, dict):
    lines.append(f"keys={list(data.keys())[:20]}")
    for k, v in list(data.items())[:5]:
        lines.append(f"sample key {k}: type={type(v).__name__}")
        if isinstance(v, list) and v:
            lines.append(f"  first item keys={list(v[0].keys()) if isinstance(v[0], dict) else v[0]}")
elif isinstance(data, list) and data:
    lines.append(f"len={len(data)}")
    if isinstance(data[0], dict):
        lines.append(f"first keys={list(data[0].keys())}")
conn.close()
out.write_text("\n".join(lines), encoding="utf-8")
