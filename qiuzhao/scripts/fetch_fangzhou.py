#!/usr/bin/env python3
"""Fetch 求职方舟 campus summary table into structured JSON.

The site is a SPA; rows live in localStorage key `campus` after the page loads.
Default filters: urlType=官网, reject WeChat apply URLs, optional keyword filter.

Usage:
  python qiuzhao/scripts/fetch_fangzhou.py --out fangzhou.json
  python qiuzhao/scripts/fetch_fangzhou.py --out agent.json \\
    --filter-keywords "Agent,智能体,Agent开发,大模型应用" --limit 30
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from playwright_env import ensure_playwright_browsers_path  # noqa: E402

DEFAULT_URL = "https://www.qiuzhifangzhou.com/campus?table=hot"
DEFAULT_KEYWORDS = [
    "Agent",
    "AI Agent",
    "Agent开发",
    "智能体",
    "大模型应用",
    "Agentic",
    "人工智能",
    "AI应用",
    "智能科研",
    "智能投研",
    "大模型",
    "RAG",
]
WEIXIN_RE = re.compile(r"mp\.weixin\.qq\.com|weixin://|wxaurl", re.I)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-fangzhou/1.0"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_weixin(url: str) -> bool:
    return bool(url and WEIXIN_RE.search(url))


def match_keywords(row: dict[str, str], keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = f"{row.get('公司', '')} {row.get('职位摘要', '')}".lower()
    for kw in keywords:
        k = kw.strip().lower()
        if k and k in blob:
            return True
    return False


def normalize_row(raw: dict[str, Any]) -> dict[str, str] | None:
    company = str(raw.get("company") or "").strip()
    if not company:
        return None
    apply_url = str(raw.get("applyUrl") or "").strip()
    notice_url = str(raw.get("noticeUrl") or raw.get("sourceUrl") or "").strip()
    url_type = str(raw.get("urlType") or "").strip()
    return {
        "id": str(raw.get("id") or ""),
        "公司": company,
        "职位摘要": str(raw.get("positions") or "").strip(),
        "地点": str(raw.get("locations") or "").strip(),
        "截止": str(raw.get("deadline") or "").strip(),
        "批次": str(raw.get("batch") or "").strip(),
        "行业": str(raw.get("industry") or "").strip(),
        "urlType": url_type,
        "投递链接": apply_url,
        "公告链接": notice_url,
        "更新时间": str(raw.get("createTime") or "").strip(),
    }


def load_rows_from_local_storage(page) -> list[dict[str, Any]]:
    raw = page.evaluate("() => localStorage.getItem('campus')")
    if not raw:
        return []
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return []
    rows: list[dict[str, Any]] = []
    cache = obj.get("dateCache") or {}
    for day in cache.values():
        data = (day or {}).get("data") or []
        if isinstance(data, list):
            rows.extend(data)
    return rows


def wait_for_campus_cache(page, timeout_ms: int = 60000) -> bool:
    page.wait_for_function(
        """() => {
          const raw = localStorage.getItem('campus');
          if (!raw) return false;
          try {
            const obj = JSON.parse(raw);
            const cache = obj.dateCache || {};
            return Object.keys(cache).length > 0;
          } catch (e) { return false; }
        }""",
        timeout=timeout_ms,
    )
    return True


def filter_raw_rows(
    raw_rows: list[dict[str, Any]],
    *,
    official_only: bool,
    reject_weixin: bool,
    keywords: list[str],
    limit: int,
) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in raw_rows:
        item = normalize_row(raw)
        if not item:
            continue
        if official_only and item["urlType"] != "官网":
            continue
        if reject_weixin and is_weixin(item["投递链接"]):
            continue
        if not match_keywords(item, keywords):
            continue
        key = f"{item['公司']}|{item['投递链接']}|{item['id']}"
        if key in seen:
            continue
        seen.add(key)
        rows_out.append(item)
        if limit and len(rows_out) >= limit:
            break
    return rows_out


def load_raw_from_dump(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and "dateCache" in obj:
        rows: list[dict[str, Any]] = []
        for day in (obj.get("dateCache") or {}).values():
            data = (day or {}).get("data") or []
            if isinstance(data, list):
                rows.extend(data)
        return rows
    if isinstance(obj, dict) and isinstance(obj.get("rows"), list):
        # already normalized export — wrap back to raw-like
        return [
            {
                "id": r.get("id"),
                "company": r.get("公司"),
                "positions": r.get("职位摘要"),
                "locations": r.get("地点"),
                "deadline": r.get("截止"),
                "batch": r.get("批次"),
                "industry": r.get("行业"),
                "urlType": r.get("urlType"),
                "applyUrl": r.get("投递链接"),
                "noticeUrl": r.get("公告链接"),
                "createTime": r.get("更新时间"),
            }
            for r in obj["rows"]
            if isinstance(r, dict)
        ]
    return []


def fetch_fangzhou(
    url: str = DEFAULT_URL,
    *,
    timeout_ms: int = 60000,
    official_only: bool = True,
    reject_weixin: bool = True,
    filter_keywords: list[str] | None = None,
    limit: int = 0,
    from_localstorage: Path | None = None,
) -> dict[str, Any]:
    keywords = filter_keywords if filter_keywords is not None else list(DEFAULT_KEYWORDS)
    status = "ok"
    error: str | None = None
    mode = "playwright_localstorage"
    rows_out: list[dict[str, str]] = []
    total_raw = 0

    try:
        if from_localstorage is not None:
            mode = "localstorage_dump"
            raw_rows = load_raw_from_dump(from_localstorage)
        else:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as exc:
                return {
                    "url": url,
                    "fetched_at": utc_now_iso(),
                    "status": "error",
                    "mode": mode,
                    "row_count": 0,
                    "filter_keywords": keywords,
                    "rows": [],
                    "error": (
                        f"playwright not installed: {exc}. "
                        "Use Python 3.10+ with pip install playwright, "
                        "or pass --from-localstorage dumped campus JSON."
                    ),
                }

            ensure_playwright_browsers_path()
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=USER_AGENT, locale="zh-CN")
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                try:
                    wait_for_campus_cache(page, timeout_ms=timeout_ms)
                except Exception:  # noqa: BLE001
                    page.wait_for_timeout(5000)
                raw_rows = load_rows_from_local_storage(page)
                if not raw_rows:
                    page.wait_for_timeout(8000)
                    raw_rows = load_rows_from_local_storage(page)
                browser.close()

        total_raw = len(raw_rows)
        rows_out = filter_raw_rows(
            raw_rows,
            official_only=official_only,
            reject_weixin=reject_weixin,
            keywords=keywords,
            limit=limit,
        )

        if not rows_out:
            status = "empty"
            error = f"no rows after filter (raw={total_raw})"
    except Exception as exc:  # noqa: BLE001
        status = "error"
        error = str(exc)

    return {
        "url": url,
        "fetched_at": utc_now_iso(),
        "status": status,
        "mode": mode,
        "raw_count": total_raw,
        "row_count": len(rows_out),
        "official_only": official_only,
        "reject_weixin": reject_weixin,
        "filter_keywords": keywords,
        "rows": rows_out,
        "error": error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch 求职方舟 campus list as JSON")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out", help="Write JSON path")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    parser.add_argument(
        "--all-sources",
        action="store_true",
        help="Do not restrict to urlType=官网",
    )
    parser.add_argument(
        "--keep-weixin",
        action="store_true",
        help="Do not drop WeChat apply URLs",
    )
    parser.add_argument(
        "--filter-keywords",
        default=",".join(DEFAULT_KEYWORDS),
        help="Comma-separated keywords; empty string = no keyword filter",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max rows to keep after filter (0 = all)",
    )
    parser.add_argument(
        "--from-localstorage",
        help="Parse dumped localStorage campus JSON instead of launching browser",
    )
    args = parser.parse_args(argv)

    if args.filter_keywords.strip() == "":
        keywords: list[str] = []
    else:
        keywords = [k.strip() for k in args.filter_keywords.split(",") if k.strip()]

    dump = Path(args.from_localstorage) if args.from_localstorage else None
    payload = fetch_fangzhou(
        args.url,
        timeout_ms=args.timeout_ms,
        official_only=not args.all_sources,
        reject_weixin=not args.keep_weixin,
        filter_keywords=keywords,
        limit=args.limit,
        from_localstorage=dump,
    )
    raw = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw + "\n", encoding="utf-8")
    else:
        sys.stdout.write(raw + "\n")

    return 0 if payload.get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
