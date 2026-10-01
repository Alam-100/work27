"""Profile API."""

from __future__ import annotations

from fastapi import APIRouter

import vault_io as vio

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
def get_profile():
    card = vio.get_profile()
    if not card:
        return {"stem": None, "meta": {}, "body": "", "summary": {}}
    # lightweight summary for UI chips
    summary = {
        "届别": "2027",
        "方向": "Agent / LLM 应用开发",
    }
    body = card.body or ""
    for line in body.splitlines():
        if "届别" in line and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2 and parts[0] == "届别":
                summary["届别"] = parts[1].replace("**", "")
        if line.strip().startswith("- **主攻**"):
            summary["方向"] = line.split("：", 1)[-1].strip() if "：" in line else line
    return {
        "stem": card.stem,
        "rel": card.rel,
        "meta": vio._jsonable_meta(card.meta),
        "body": body,
        "summary": summary,
    }
