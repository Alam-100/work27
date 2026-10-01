#!/usr/bin/env python3
"""Export qiuzhao progress + intel deadlines + campus events to ICS.

Reads:
  - 秋招/05_投递进度/*.md  (type: qiuzhao-progress) → 测评/笔试/一面~HR面
  - 秋招/02_情报库/*.md    (type: qiuzhao-intel-job) → 投递截止
  - 秋招/10_校园活动/*.md  (type: qiuzhao-campus-event) → 宣讲/双选
Also accepts legacy 02_投递 / qiuzhao-application if present.

Default vault: E:/obsidian/My_docs (override with QIUZHAO_VAULT).
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

VAULT = Path(os.environ.get("QIUZHAO_VAULT", r"E:\obsidian\My_docs"))
PROGRESS_DIR = VAULT / "秋招" / "05_投递进度"
INTEL_DIR = VAULT / "秋招" / "02_情报库"
CAMPUS_DIR = VAULT / "秋招" / "10_校园活动"
LEGACY_DIR = VAULT / "秋招" / "02_投递"
OUT = VAULT / "秋招" / "01_看板" / "秋招日程.ics"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

INTERVIEW_FIELDS = (
    ("测评时间", "测评", "assessment"),
    ("笔试时间", "笔试", "written"),
    ("一面", "一面", "r1"),
    ("二面", "二面", "r2"),
    ("三面", "三面", "r3"),
    ("HR面", "HR面", "hr"),
)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    raw = m.group(1)
    if yaml:
        data = yaml.safe_load(raw) or {}
        return data if isinstance(data, dict) else {}
    data: dict = {}
    for line in raw.splitlines():
        if ":" not in line or line.strip().startswith("-"):
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if val in ("", "[]", "null", "~"):
            continue
        data[key] = val
    return data


def parse_dt(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s[:19] if "T" in s and len(s) > 19 else s, fmt)
        except ValueError:
            continue
    return None


def ics_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def event(uid: str, summary: str, dt: datetime, description: str, duration_hours: int = 2) -> str:
    end = dt + timedelta(hours=duration_hours)
    if dt.hour == 0 and dt.minute == 0 and "截止" in summary:
        day = dt.strftime("%Y%m%d")
        next_day = (dt + timedelta(days=1)).strftime("%Y%m%d")
        return "\r\n".join(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;VALUE=DATE:{day}",
                f"DTEND;VALUE=DATE:{next_day}",
                f"SUMMARY:{ics_escape(summary)}",
                f"DESCRIPTION:{ics_escape(description)}",
                "END:VEVENT",
            ]
        )
    return "\r\n".join(
        [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{ics_dt(dt)}",
            f"DTEND:{ics_dt(end)}",
            f"SUMMARY:{ics_escape(summary)}",
            f"DESCRIPTION:{ics_escape(description)}",
            "BEGIN:VALARM",
            "TRIGGER:-PT24H",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{ics_escape(summary)}",
            "END:VALARM",
            "BEGIN:VALARM",
            "TRIGGER:-PT2H",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{ics_escape(summary)}",
            "END:VALARM",
            "END:VEVENT",
        ]
    )


def meta_get(meta: dict, *keys):
    for k in keys:
        if k in meta and meta[k] not in (None, ""):
            return meta[k]
    return None


def collect_from_progress(events: list[str]) -> None:
    if not PROGRESS_DIR.is_dir():
        return
    for path in sorted(PROGRESS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        if meta.get("type") != "qiuzhao-progress":
            continue
        company = str(meta_get(meta, "公司", "company") or path.stem)
        position = str(meta_get(meta, "岗位", "position") or "")
        url = str(meta_get(meta, "投递链接", "apply_url") or "")
        base_desc = f"{company} {position}\n{url}\nnote:{path.name}"

        for field, label, suffix in INTERVIEW_FIELDS:
            dt = parse_dt(meta_get(meta, field))
            if not dt:
                continue
            events.append(
                event(
                    f"{uuid.uuid5(uuid.NAMESPACE_URL, path.name + '-' + suffix)}@qiuzhao",
                    f"[{label}] {company}-{position}",
                    dt,
                    base_desc,
                )
            )


def collect_from_intel(events: list[str]) -> None:
    for app_dir in (INTEL_DIR, LEGACY_DIR):
        if not app_dir.is_dir():
            continue
        for path in sorted(app_dir.rglob("*.md")):
            if path.name.startswith("_"):
                continue
            text = path.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            t = meta.get("type")
            if t not in ("qiuzhao-intel-job", "qiuzhao-application"):
                continue
            company = str(meta_get(meta, "公司", "company") or path.stem)
            position = str(meta_get(meta, "岗位", "position") or "")
            url = str(meta_get(meta, "投递链接", "apply_url") or "")
            base_desc = f"{company} {position}\n{url}\nnote:{path.name}"

            deadline = parse_dt(meta_get(meta, "投递截止", "deadline"))
            if deadline:
                events.append(
                    event(
                        f"{uuid.uuid5(uuid.NAMESPACE_URL, path.name + '-deadline')}@qiuzhao",
                        f"[截止] {company}-{position}",
                        deadline.replace(hour=0, minute=0, second=0),
                        base_desc,
                        duration_hours=24,
                    )
                )

            if t != "qiuzhao-application":
                continue
            written = parse_dt(meta_get(meta, "笔试时间", "written_test_at"))
            if written:
                events.append(
                    event(
                        f"{uuid.uuid5(uuid.NAMESPACE_URL, path.name + '-written')}@qiuzhao",
                        f"[笔试] {company}-{position}",
                        written,
                        base_desc,
                    )
                )
            interview = parse_dt(meta_get(meta, "下场面试", "interview_next_at"))
            if interview:
                events.append(
                    event(
                        f"{uuid.uuid5(uuid.NAMESPACE_URL, path.name + '-interview')}@qiuzhao",
                        f"[面试] {company}-{position}",
                        interview,
                        base_desc,
                    )
                )


def collect_from_campus(events: list[str]) -> None:
    if not CAMPUS_DIR.is_dir():
        return
    for path in sorted(CAMPUS_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        if meta.get("type") != "qiuzhao-campus-event":
            continue
        dt = parse_dt(meta_get(meta, "开始"))
        if not dt:
            continue
        company = str(meta_get(meta, "公司", "标题") or path.stem)
        label = str(meta_get(meta, "活动类型") or "校园活动")
        place = str(meta_get(meta, "地点") or "")
        url = str(meta_get(meta, "来源链接") or "")
        desc = f"{company}\n{place}\n{url}\nnote:{path.name}"
        end = parse_dt(meta_get(meta, "结束"))
        hours = 2
        if end and end > dt:
            hours = max(1, int(round((end - dt).total_seconds() / 3600)))
        events.append(
            event(
                f"{uuid.uuid5(uuid.NAMESPACE_URL, path.name + '-campus')}@qiuzhao",
                f"[{label}] {company}",
                dt,
                desc,
                duration_hours=hours,
            )
        )


def collect_events() -> list[str]:
    events: list[str] = []
    collect_from_progress(events)
    collect_from_intel(events)
    collect_from_campus(events)
    if not events and not PROGRESS_DIR.is_dir() and not INTEL_DIR.is_dir() and not CAMPUS_DIR.is_dir():
        raise SystemExit(
            f"No progress/intel/campus dirs found under {VAULT / '秋招'}"
        )
    return events


def main() -> None:
    events = collect_events()
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"Wrote {len(events)} events -> {OUT}")


if __name__ == "__main__":
    main()
