#!/usr/bin/env python3
"""Fetch 西电就业网宣讲会 / 双选会（组团招聘）into structured JSON.

Sources:
  - https://job.xidian.edu.cn/          (homepage SSR panels)
  - https://job.xidian.edu.cn/teachin/* (Playwright rendered lists)
  - https://job.xidian.edu.cn/jobfair   (Playwright rendered lists)

Usage:
  py -3.12 qiuzhao/scripts/fetch_xidian_events.py --out qiuzhao/tmp/xidian_events.json
  py -3.12 qiuzhao/scripts/fetch_xidian_events.py --write-vault --update-source-links
  py -3.12 qiuzhao/scripts/fetch_xidian_events.py --http-only --out out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import httpx

from playwright_env import ensure_playwright_browsers_path  # noqa: E402

HOME_URL = "https://job.xidian.edu.cn/"
TEACHIN_URLS = [
    "https://job.xidian.edu.cn/teachin/index/zone/%E5%8C%97%E6%A0%A1%E5%8C%BA",
    "https://job.xidian.edu.cn/teachin/index/zone/%E5%8D%97%E6%A0%A1%E5%8C%BA",
    "https://job.xidian.edu.cn/teachin/index/type/online",
    "https://job.xidian.edu.cn/teachin/index",
]
JOBFAIR_URLS = [
    "https://job.xidian.edu.cn/jobfair",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-xidian/1.0"
)

LINK_RE = re.compile(
    r"""(?is)<a[^>]+href=["']([^"']*/(?:teachin|jobfair)/view/id/(\d+)[^"']*)["'][^>]*>(.*?)</a>""",
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
TIME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})(?:\s*-\s*(\d{2}:\d{2}))?"
)
TITLE_RE = re.compile(r'(?is)<p[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)</p>')
STATUS_WORDS = ("已举办", "进行中", "未开始", "已取消")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strip_html(html: str) -> str:
    text = TAG_RE.sub(" ", html or "")
    return WS_RE.sub(" ", text).strip()


def abs_url(href: str) -> str:
    if href.startswith("http"):
        return href.split("?")[0].rstrip("/")
    return urljoin(HOME_URL, href).split("?")[0].rstrip("/")


def external_id(kind: str, eid: str) -> str:
    return f"{kind}/{eid}"


def infer_kind_from_url(url: str) -> str:
    if "/jobfair/" in url:
        return "jobfair"
    return "teachin"


def infer_activity_type(kind: str, title: str) -> str:
    if kind == "jobfair":
        if "组团" in title:
            return "组团招聘"
        if "双选" in title or "招聘会" in title:
            return "双选会"
        return "双选会"
    return "宣讲会"


def infer_form(place: str, text: str) -> str:
    blob = f"{place} {text}"
    if "线上" in blob or "空中" in blob or "网络宣讲" in blob:
        return "线上"
    if "南校" in blob or "长安校区" in blob or "长安" in place:
        return "南校线下"
    if "北校" in blob or "雁塔校区" in blob or "雁塔" in place:
        return "北校线下"
    return ""


def parse_place(text: str) -> str:
    m = re.search(r"地点[：:]\s*([^\s时]+(?:[^\s时]*))", text)
    if m:
        return m.group(1).strip(" ，,;；")
    for token in ("线上宣讲", "线上", "北校区", "南校区"):
        if token in text:
            # take a short place token
            m2 = re.search(rf"({token}[^\s]*)", text)
            if m2:
                return m2.group(1)
    return ""


def parse_times(text: str) -> tuple[str, str]:
    """Return (开始, 结束) as 'YYYY-MM-DD HH:MM' strings; unknown left empty."""
    m = TIME_RE.search(text)
    if not m:
        return "", ""
    day, start_hm, end_hm = m.group(1), m.group(2), m.group(3)
    start = f"{day} {start_hm}"
    end = f"{day} {end_hm}" if end_hm else ""
    return start, end


def parse_status(text: str) -> str:
    for s in STATUS_WORDS:
        if s in text:
            return s
    return ""


def company_from_title(title: str) -> str:
    t = (title or "").strip()
    # strip common suffixes like 专场 / 宣讲会
    t = re.sub(r"(宣讲会|空中宣讲|线上宣讲|专场|招聘会|双选会).*$", "", t).strip()
    return t or title.strip()


def parse_anchor_block(href: str, inner_html: str) -> dict[str, Any] | None:
    m = re.search(r"/(teachin|jobfair)/view/id/(\d+)", href)
    if not m:
        return None
    kind, eid = m.group(1), m.group(2)
    title_m = TITLE_RE.search(inner_html)
    title = strip_html(title_m.group(1)) if title_m else ""
    text = strip_html(inner_html)
    if not title:
        # first chunk before 职位/地点/时间
        title = re.split(r"职位|地点|时间|已举办|进行中|未开始", text)[0].strip()[:80]
    if not title:
        return None
    place = parse_place(text)
    start, end = parse_times(text)
    status = parse_status(text)
    url = abs_url(href)
    return {
        "外部ID": external_id(kind, eid),
        "活动类型": infer_activity_type(kind, title),
        "标题": title,
        "公司": company_from_title(title),
        "形式": infer_form(place, text),
        "地点": place,
        "开始": start,
        "结束": end,
        "状态": status,
        "来源": "就业网",
        "来源链接": url,
        "原始摘要": text[:240],
    }


def infer_status_from_times(start: str, end: str, explicit: str = "") -> str:
    if explicit in STATUS_WORDS:
        return explicit
    now = datetime.now()
    st = None
    en = None
    if start:
        try:
            st = datetime.strptime(start[:16], "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                st = datetime.strptime(start[:10], "%Y-%m-%d")
            except ValueError:
                st = None
    if end:
        try:
            en = datetime.strptime(end[:16], "%Y-%m-%d %H:%M")
        except ValueError:
            en = None
    if st and en:
        if now < st:
            return "未开始"
        if st <= now <= en:
            return "进行中"
        return "已举办"
    if st:
        if now.date() < st.date():
            return "未开始"
        if now.date() == st.date():
            return "进行中" if now >= st else "未开始"
        return "已举办"
    return explicit or ""


def parse_infolist_events(html: str) -> list[dict[str, Any]]:
    """Parse employment-site list rows: ul.infoList with title / place / time columns."""
    events: list[dict[str, Any]] = []
    for block in re.findall(r'(?is)<ul class="infoList[^"]*">.*?</ul>', html):
        href_m = re.search(
            r"""(?is)<a[^>]+href=["']([^"']*/(?:teachin|jobfair)/view/id/(\d+)[^"']*)["'][^>]*>(.*?)</a>""",
            block,
        )
        if not href_m:
            continue
        href, eid, a_inner = href_m.group(1), href_m.group(2), href_m.group(3)
        kind = infer_kind_from_url(href)
        title_attr = re.search(r'(?is)<a[^>]+title=["\']([^"\']+)["\']', block)
        title = (title_attr.group(1).strip() if title_attr else "") or strip_html(a_inner)
        if not title:
            continue
        lis = re.findall(r"(?is)<li\b([^>]*)>(.*?)</li>", block)
        place = ""
        time_text = ""
        texts: list[str] = []
        for attrs, inner in lis:
            t = strip_html(inner)
            texts.append(t)
            cls = ""
            cm = re.search(r'class=["\']([^"\']*)["\']', attrs)
            if cm:
                cls = cm.group(1)
            if "span5" in cls.split() and t:
                place = t
            if TIME_RE.search(t) and not time_text:
                time_text = t
        # Column layout: [title(+badge), place, time]
        if (not place or place == title or title.startswith(place) or place.startswith(title[:8])) and len(texts) >= 3:
            cand = texts[1]
            if cand and cand != title and not TIME_RE.search(cand):
                place = cand
        if not place:
            for t in texts[1:]:
                if t and t != title and not TIME_RE.search(t) and t not in ("空中", "线下"):
                    if len(t) <= 40 or "校区" in t or "线上" in t or "教室" in t or "报告厅" in t:
                        place = t
                        break
        start, end = parse_times(time_text)
        badge = ""
        bm = re.search(r'class="status-text"[^>]*>([^<]+)', block)
        if bm:
            badge = bm.group(1).strip()
        explicit = parse_status(block)
        status = infer_status_from_times(start, end, explicit)
        url = abs_url(href)
        form = infer_form(place, f"{title} {badge} {place}")
        events.append(
            {
                "外部ID": external_id(kind, eid),
                "活动类型": infer_activity_type(kind, title),
                "标题": title,
                "公司": company_from_title(title),
                "形式": form,
                "地点": place,
                "开始": start,
                "结束": end,
                "状态": status,
                "来源": "就业网",
                "来源链接": url,
                "原始摘要": strip_html(block)[:240],
            }
        )
    return events


def extract_events_from_html(html: str) -> list[dict[str, Any]]:
    # Prefer structured list rows; fall back to homepage card anchors.
    events = parse_infolist_events(html)
    if events:
        return events

    for m in re.finditer(
        r"""(?is)href=["']([^"']*/(?:teachin|jobfair)/view/id/\d+[^"']*)["']""",
        html,
    ):
        href = m.group(1)
        start = m.start()
        a_start = -1
        for i in range(m.start(), max(-1, m.start() - 200), -1):
            if html.startswith("<a", i) and (i + 2 >= len(html) or html[i + 2] in " \t\r\n/>"):
                a_start = i
                break
        if a_start < 0:
            a_start = start
        depth = 0
        i = a_start
        end = -1
        while i < len(html) and i < a_start + 5000:
            next_open = -1
            j = i
            while True:
                j = html.find("<a", j)
                if j < 0 or j >= a_start + 5000:
                    break
                if j + 2 < len(html) and html[j + 2] in " \t\r\n/>":
                    next_open = j
                    break
                j += 2
            next_close = html.find("</a>", i)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                depth += 1
                i = next_open + 2
                continue
            depth -= 1
            i = next_close + 4
            if depth <= 0:
                end = next_close
                break
        if end < 0:
            inner = html[m.end() : m.end() + 1800]
        else:
            gt = html.find(">", a_start, end)
            inner = html[gt + 1 : end] if gt >= 0 else html[a_start:end]
        item = parse_anchor_block(href, inner)
        if item:
            if not item.get("状态"):
                item["状态"] = infer_status_from_times(
                    str(item.get("开始") or ""),
                    str(item.get("结束") or ""),
                )
            events.append(item)
    return events


def dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for ev in events:
        key = ev.get("外部ID") or ""
        if not key:
            key = f"manual|{ev.get('公司')}|{ev.get('开始')}|{ev.get('地点')}"
        prev = by_id.get(key)
        if not prev:
            by_id[key] = ev
            continue
        # Prefer richer fields
        merged = dict(prev)
        for k, v in ev.items():
            if v and not merged.get(k):
                merged[k] = v
            elif k in ("标题", "原始摘要") and v and len(str(v)) > len(str(merged.get(k) or "")):
                merged[k] = v
        by_id[key] = merged
    out = list(by_id.values())

    def sort_key(e: dict[str, Any]) -> tuple:
        start = e.get("开始") or ""
        return (start == "", start, e.get("标题") or "")

    out.sort(key=sort_key)
    return out


def fetch_home_http(timeout: float = 30.0) -> tuple[list[dict[str, Any]], str | None]:
    try:
        r = httpx.get(
            HOME_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )
        r.raise_for_status()
        return extract_events_from_html(r.text), None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


def fetch_lists_playwright(timeout_ms: int = 60000) -> tuple[list[dict[str, Any]], str | None]:
    ensure_playwright_browsers_path()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return [], f"playwright missing: {exc}"

    events: list[dict[str, Any]] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            for url in [*TEACHIN_URLS, *JOBFAIR_URLS]:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    page.wait_for_timeout(1800)
                    # try click "下一页" a couple times if present
                    for _ in range(3):
                        html = page.content()
                        events.extend(extract_events_from_html(html))
                        nxt = page.locator("a:has-text('下一页'), a.next, .pagination a:has-text('>')")
                        if nxt.count() == 0:
                            break
                        try:
                            if not nxt.first.is_enabled():
                                break
                            nxt.first.click(timeout=3000)
                            page.wait_for_timeout(1200)
                        except Exception:  # noqa: BLE001
                            break
                except Exception:  # noqa: BLE001
                    continue
            browser.close()
        return events, None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


def filter_horizon(
    events: list[dict[str, Any]],
    *,
    future_days: int = 21,
    keep_past_days: int = 7,
) -> list[dict[str, Any]]:
    today = date.today()
    start_keep = today - timedelta(days=keep_past_days)
    end_keep = today + timedelta(days=future_days)
    kept: list[dict[str, Any]] = []
    for ev in events:
        start_s = ev.get("开始") or ""
        status = ev.get("状态") or ""
        if not start_s:
            # Undated rows are usually incomplete list scrapes — drop them.
            continue
        try:
            d = datetime.strptime(start_s[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if start_keep <= d <= end_keep:
            kept.append(ev)
        elif status in ("未开始", "进行中") and d >= today:
            kept.append(ev)
    return kept


def update_source_links(checked_at: str) -> None:
    src = _SCRIPTS_DIR.parent / "data" / "source_links.json"
    if not src.is_file():
        return
    data = json.loads(src.read_text(encoding="utf-8"))
    links = data.setdefault("links", [])
    wanted = {
        HOME_URL.rstrip("/"): {
            "url": HOME_URL.rstrip("/"),
            "type": "校园活动",
            "batch": "西电",
            "platform": "西电就业网",
            "status": "有效",
            "note": "首页 SSR 宣讲/双选面板；主抓取入口之一",
        },
        "https://job.xidian.edu.cn/teachin/index": {
            "url": "https://job.xidian.edu.cn/teachin/index",
            "type": "校园活动",
            "batch": "西电",
            "platform": "西电就业网",
            "status": "有效",
            "note": "宣讲会列表（北/南/线上）；Playwright 渲染",
        },
        "https://job.xidian.edu.cn/jobfair": {
            "url": "https://job.xidian.edu.cn/jobfair",
            "type": "校园活动",
            "batch": "西电",
            "platform": "西电就业网",
            "status": "有效",
            "note": "招聘会/双选/组团；Playwright 渲染",
        },
    }
    by_url = {str(x.get("url", "")).rstrip("/"): x for x in links}
    for url, template in wanted.items():
        row = by_url.get(url)
        if not row:
            row = dict(template)
            links.append(row)
            by_url[url] = row
        row["status"] = "有效"
        row["last_checked"] = checked_at
        row["最近检查"] = checked_at
        row["核实于"] = checked_at
        if not row.get("type"):
            row["type"] = "校园活动"
    data["updated"] = checked_at
    src.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_vault(events: list[dict[str, Any]]) -> dict[str, Any]:
    import vault_io as vio

    return vio.upsert_campus_events_from_fetch(events)


def fetch_all(*, http_only: bool = False, timeout_ms: int = 60000) -> dict[str, Any]:
    errors: list[str] = []
    home, err = fetch_home_http(timeout=max(10.0, timeout_ms / 1000))
    if err:
        errors.append(f"home: {err}")
    lists: list[dict[str, Any]] = []
    if not http_only:
        lists, err2 = fetch_lists_playwright(timeout_ms=timeout_ms)
        if err2:
            errors.append(f"playwright: {err2}")
    merged = dedupe_events([*home, *lists])
    horizon = filter_horizon(merged)
    status = "ok"
    if not merged:
        status = "empty" if not errors else "error"
    elif errors and not lists and not http_only:
        status = "partial"
    return {
        "fetched_at": utc_now_iso(),
        "status": status,
        "home_count": len(home),
        "list_count": len(lists),
        "raw_count": len(merged),
        "row_count": len(horizon),
        "errors": errors,
        "rows": horizon,
        "all_rows": merged,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch 西电就业网宣讲会/双选会")
    ap.add_argument("--out", help="Write JSON path")
    ap.add_argument("--http-only", action="store_true", help="Skip Playwright list pages")
    ap.add_argument("--timeout-ms", type=int, default=60000)
    ap.add_argument("--write-vault", action="store_true", help="Upsert into 秋招/10_校园活动")
    ap.add_argument("--update-source-links", action="store_true")
    ap.add_argument("--keep-all", action="store_true", help="Do not apply 21d horizon filter for --out")
    args = ap.parse_args(argv)

    payload = fetch_all(http_only=args.http_only, timeout_ms=args.timeout_ms)
    rows = payload["all_rows"] if args.keep_all else payload["rows"]
    out_payload = {**payload, "rows": rows}
    out_payload.pop("all_rows", None)

    if args.write_vault:
        try:
            result = write_vault(rows)
            out_payload["vault"] = result
        except Exception as exc:  # noqa: BLE001
            out_payload["vault"] = {"ok": False, "error": str(exc)}
            out_payload["status"] = "error"

    if args.update_source_links:
        update_source_links(date.today().isoformat())

    raw = json.dumps(out_payload, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw + "\n", encoding="utf-8")
    else:
        sys.stdout.write(raw + "\n")

    print(
        json.dumps(
            {
                "status": out_payload.get("status"),
                "home": out_payload.get("home_count"),
                "lists": out_payload.get("list_count"),
                "rows": out_payload.get("row_count") if not args.keep_all else len(rows),
                "vault": out_payload.get("vault"),
                "errors": out_payload.get("errors"),
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 0 if out_payload.get("status") in ("ok", "partial", "empty") else 1


if __name__ == "__main__":
    raise SystemExit(main())
