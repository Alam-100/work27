"""Campus career talks / job fairs API."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import vault_io as vio

router = APIRouter(prefix="/events", tags=["events"])

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
_FETCH = _SCRIPTS / "fetch_xidian_events.py"


_FIT_RANK = {"intel": 0, "direction": 1, "normal": 2}


def _event_dict(card: vio.NoteCard, *, keywords: list[str] | None = None) -> dict:
    meta = card.meta
    bucket = vio.campus_event_bucket(meta)
    linked = bool(meta.get("关联情报"))
    fit = vio.campus_event_fit_level(meta, keywords=keywords)
    source = str(meta.get("来源") or "")
    sources = [p.strip() for p in re.split(r"[·+/|,，、]", source) if p.strip()] if source else []
    return {
        **vio.note_card_to_dict(card),
        "bucket": bucket,
        "intel_linked": linked,
        "fit_level": fit,
        "session_key": vio.campus_session_key({**meta, "stem": card.stem}),
        "identity_key": vio.campus_identity_key({**meta, "stem": card.stem}),
        "company": meta.get("公司") or "",
        "title": meta.get("标题") or meta.get("公司") or card.stem,
        "event_type": meta.get("活动类型") or "",
        "form": meta.get("形式") or "",
        "place": meta.get("地点") or "",
        "start": meta.get("开始") or "",
        "end": meta.get("结束") or "",
        "status": meta.get("状态") or "",
        "source": source,
        "sources": sources or ([source] if source else []),
        "source_url": meta.get("来源链接") or "",
        "verified_at": meta.get("核实于") or "",
        "intel_link": meta.get("关联情报") or "",
    }


@router.get("")
def list_events(
    q: str = Query(""),
    event_type: str = Query("", alias="type"),
    form: str = Query(""),
    bucket: str = Query(""),
    intel_only: bool = Query(False),
    status: str = Query(""),
):
    vio.campus_events_dir().mkdir(parents=True, exist_ok=True)
    vio.ensure_campus_events_inbox()
    keywords = vio.profile_direction_keywords()
    cards = vio.list_campus_events()
    items = [_event_dict(c, keywords=keywords) for c in cards]
    qn = q.strip().lower()
    if qn:
        items = [
            it
            for it in items
            if qn in str(it.get("title") or "").lower()
            or qn in str(it.get("company") or "").lower()
            or qn in str(it.get("place") or "").lower()
        ]
    if event_type:
        items = [it for it in items if it.get("event_type") == event_type]
    if form:
        items = [it for it in items if it.get("form") == form]
    if status:
        items = [it for it in items if it.get("status") == status]
    if intel_only:
        items = [it for it in items if it.get("intel_linked")]
    if bucket:
        items = [it for it in items if it.get("bucket") == bucket]

    # Safety-net: collapse same company+start+place across sources in API response
    collapsed: dict[str, dict] = {}
    order: list[str] = []
    for it in items:
        key = str(it.get("identity_key") or it.get("stem") or id(it))
        if key not in collapsed:
            collapsed[key] = dict(it)
            order.append(key)
            continue
        cur = collapsed[key]
        cur["source"] = vio.merge_campus_sources(cur.get("source"), it.get("source"))
        srcs = list(cur.get("sources") or [])
        for s in it.get("sources") or []:
            if s and s not in srcs:
                srcs.append(s)
        cur["sources"] = srcs
        if not cur.get("source_url") and it.get("source_url"):
            cur["source_url"] = it["source_url"]
        if it.get("intel_linked"):
            cur["intel_linked"] = True
            cur["intel_link"] = it.get("intel_link") or cur.get("intel_link")
        fit_a = _FIT_RANK.get(str(cur.get("fit_level") or "normal"), 9)
        fit_b = _FIT_RANK.get(str(it.get("fit_level") or "normal"), 9)
        if fit_b < fit_a:
            cur["fit_level"] = it.get("fit_level")
        # prefer employment-site title/place quality via longer source_url presence
        if it.get("source_url") and not cur.get("source_url"):
            cur["title"] = it.get("title") or cur.get("title")
            cur["place"] = it.get("place") or cur.get("place")
    items = [collapsed[k] for k in order]

    def sort_key(it: dict) -> tuple:
        start = str(it.get("start") or "")
        fit = _FIT_RANK.get(str(it.get("fit_level") or "normal"), 9)
        company = str(it.get("company") or "")
        return (start == "", start, fit, company)

    items.sort(key=sort_key)

    buckets = {"today": 0, "tomorrow": 0, "week": 0, "later": 0, "past": 0}
    for it in items:
        b = it.get("bucket") or "later"
        if b in buckets:
            buckets[b] += 1

    verified = [str(it.get("verified_at") or "") for it in items if it.get("verified_at")]
    last_verified = max(verified) if verified else ""
    fit_intel = sum(1 for it in items if it.get("fit_level") == "intel")
    fit_direction = sum(1 for it in items if it.get("fit_level") == "direction")

    return {
        "items": items,
        "total": len(items),
        "stats": {
            "total": len(items),
            "today": buckets["today"],
            "tomorrow": buckets["tomorrow"],
            "week": buckets["week"],
            "later": buckets["later"],
            "past": buckets["past"],
            "intel_linked": sum(1 for it in items if it.get("intel_linked")),
            "fit_intel": fit_intel,
            "fit_direction": fit_direction,
            "last_verified": last_verified,
        },
        "enums": {
            "types": vio.CAMPUS_EVENT_TYPES,
            "forms": vio.CAMPUS_EVENT_FORMS,
            "statuses": vio.CAMPUS_EVENT_STATUSES,
            "sources": vio.CAMPUS_EVENT_SOURCES,
            "buckets": ["today", "tomorrow", "week", "later", "past"],
        },
    }


@router.get("/{stem}")
def get_event(stem: str):
    card = vio.get_campus_event(stem)
    if not card:
        raise HTTPException(404, "找不到校园活动")
    return _event_dict(card, keywords=vio.profile_direction_keywords())


@router.post("/refresh")
def refresh_events():
    if not _FETCH.is_file():
        raise HTTPException(500, f"找不到抓取脚本: {_FETCH}")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(_FETCH),
                "--write-vault",
                "--update-source-links",
                "--out",
                str(_SCRIPTS.parent / "tmp" / "xidian_events.json"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            cwd=str(_SCRIPTS.parent.parent),
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "就业网刷新超时（>180s）") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"刷新失败：{exc}") from exc

    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    if proc.returncode != 0:
        raise HTTPException(
            500,
            f"抓取失败（code={proc.returncode}）：{stderr or stdout or 'unknown'}",
        )
    summary = stderr or stdout
    cards = vio.list_campus_events()
    return {
        "ok": True,
        "count": len(cards),
        "summary": summary[-2000:],
        "verified_at": vio.today_str(),
    }


class InboxBody(BaseModel):
    url: str = Field(..., min_length=4)
    note: str = ""


@router.post("/inbox")
def inbox_event(body: InboxBody):
    url = body.url.strip()
    if not url:
        raise HTTPException(400, "URL 不能为空")
    payload = url if not body.note.strip() else f"{url} | {body.note.strip()}"
    vio.append_campus_inbox_url(payload)
    try:
        job = vio.append_agent_job("宣讲会补录", payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "ok": True,
        "message": "已写入宣讲会收件箱并入队「宣讲会补录」。请在 Cursor 说：处理控制台任务",
        "job": {
            "id": job.id,
            "intent": job.intent,
            "payload": job.payload,
            "status": job.status,
        },
    }
