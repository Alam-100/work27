"""Calendar API."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

import vault_io as vio

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return vio.parse_dt(value)


@router.get("/events")
def calendar_events(
    start: str = Query(""),
    end: str = Query(""),
):
    start_dt = _parse_iso(start)
    end_dt = _parse_iso(end)
    if not start_dt and not end_dt:
        now = datetime.now()
        start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # ~2 months window
        end_dt = now + timedelta(days=60)
    events = vio.collect_all_calendar_events(start=start_dt, end=end_dt)
    return {"events": events, "total": len(events)}


@router.get("/conflicts")
def calendar_conflicts():
    pairs = vio.find_conflicts()
    items = []
    for a, b in pairs:
        items.append(
            {
                "a": {
                    "when": a.when.isoformat(timespec="minutes"),
                    "when_fmt": vio.fmt_dt(a.when),
                    "label": a.label,
                    "company": a.company,
                    "position": a.position,
                    "stem": a.stem,
                },
                "b": {
                    "when": b.when.isoformat(timespec="minutes"),
                    "when_fmt": vio.fmt_dt(b.when),
                    "label": b.label,
                    "company": b.company,
                    "position": b.position,
                    "stem": b.stem,
                },
            }
        )
    return {"conflicts": items, "total": len(items)}


@router.get("/stats")
def calendar_stats():
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        month_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        month_end = now.replace(month=now.month + 1, day=1) - timedelta(seconds=1)
    week_end = now + timedelta(days=7)
    all_events = [e for e in vio.collect_progress_events() if e.label != "投递截止"]
    month_count = sum(1 for e in all_events if month_start <= e.when <= month_end)
    week_count = sum(1 for e in all_events if now.replace(hour=0, minute=0, second=0) <= e.when <= week_end)
    upcoming = sum(1 for e in all_events if e.when >= now)
    completed = sum(1 for e in all_events if e.when < now and month_start <= e.when <= month_end)
    conflicts = len(vio.find_conflicts())
    return {
        "month": month_count,
        "week": week_count,
        "upcoming": upcoming,
        "completed_this_month": completed,
        "conflicts": conflicts,
    }


@router.post("/export-ics")
def export_ics():
    import export_ics as ics_mod

    try:
        events = ics_mod.collect_events()
        body = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-qiuzhao-assistant-export_ics-",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH",
                "X-WR-CALNAME:秋招日程",
                *events,
                "END:VCALENDAR",
                "",
            ]
        )
        ics_mod.OUT.parent.mkdir(parents=True, exist_ok=True)
        ics_mod.OUT.write_text(body, encoding="utf-8")
        return {"ok": True, "count": len(events), "path": str(ics_mod.OUT)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"导出失败：{exc}") from exc
