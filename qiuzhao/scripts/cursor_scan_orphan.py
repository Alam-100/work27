import json
import os
import sqlite3
from pathlib import Path

OUT = Path(__file__).with_name("_orphan_scan.txt")
db = Path(os.environ["APPDATA"]) / "Cursor/User/globalStorage/state.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()
lines = []

cur.execute("SELECT value FROM ItemTable WHERE key='glass.localAgentProjectMembership.v1'")
membership = json.loads(cur.fetchone()[0])
lines.append(f"membership type={type(membership).__name__}")

if isinstance(membership, dict):
    for k, v in membership.items():
        blob = json.dumps(v, ensure_ascii=False)
        if "1786347249089" in blob or k == "7aeeac556a461eec32a7969003d273b7":
            if isinstance(v, list):
                lines.append(f"KEY {k} list len={len(v)}")
                for item in v[:30]:
                    if isinstance(item, dict):
                        lines.append(
                            f"  agent={item.get('agentId') or item.get('id')} "
                            f"name={item.get('name')} composer={item.get('composerId')}"
                        )
            else:
                lines.append(f"KEY {k} {type(v).__name__} len={len(blob)}")

cur.execute("SELECT key, value FROM ItemTable")
for key, value in cur.fetchall():
    if not value or key.startswith("glass.") is False and "agent" not in key.lower():
        continue
    if "1786347249089" in value and "localAgent" in key:
        lines.append(f"ITEM {key} len={len(value)}")

conn.close()
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT}")
