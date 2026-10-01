#!/usr/bin/env python3
"""Fetch OfferStar campus recruitment list pages into structured JSON.

Supports:
  - First page via httpx + HTML table parse
  - Multi-page via Playwright pagination (optional)
  - Keyword filter for portrait-aligned ingest

Usage:
  python qiuzhao/scripts/fetch_offerstar.py --url "https://www.offerstar.cn/recruitment?..." --out list.json
  python qiuzhao/scripts/fetch_offerstar.py --url "..." --out ai.json --filter-keywords "Agent,AI Agent,Agent开发"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from playwright_env import ensure_playwright_browsers_path  # noqa: E402

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-offerstar/1.0"
)

HEADERS = [
    "公司名称",
    "标题",
    "批次",
    "更新时间",
    "招聘岗位",
    "工作地点",
    "行业",
    "招聘类型",
    "截止时间",
    "操作",
]

FIELD_MAP = {
    "公司名称": "公司",
    "标题": "标题",
    "批次": "批次",
    "更新时间": "更新时间",
    "招聘岗位": "招聘岗位",
    "工作地点": "工作地点",
    "行业": "行业",
    "招聘类型": "招聘类型",
    "截止时间": "截止时间",
    "操作": "操作",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_cell(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()
    return text


def extract_href(td_html: str) -> str:
    m = re.search(r'href=["\']([^"\']+)["\']', td_html or "", re.I)
    if not m:
        return ""
    href = m.group(1).replace("&amp;", "&")
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return urljoin("https://www.offerstar.cn", href)
    return href


def split_table_rows(html: str) -> list[str]:
    # Prefer tbody rows; fall back to any tr after first header row
    bodies = re.findall(r"(?is)<tbody[^>]*>(.*?)</tbody>", html or "")
    chunks: list[str] = []
    if bodies:
        for body in bodies:
            chunks.extend(re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", body))
    else:
        all_trs = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html or "")
        chunks = all_trs[1:] if len(all_trs) > 1 else all_trs
    return chunks


def parse_row_cells(tr_inner: str) -> tuple[list[str], str]:
    tds = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr_inner)
    texts: list[str] = []
    apply_url = ""
    for td in tds:
        href = extract_href(td)
        if href and ("投递" in td or "http" in href) and not apply_url:
            apply_url = href
        plain = re.sub(r"(?is)<[^>]+>", " ", td)
        plain = re.sub(r"&nbsp;", " ", plain)
        plain = re.sub(r"&amp;", "&", plain)
        plain = re.sub(r"&lt;", "<", plain)
        plain = re.sub(r"&gt;", ">", plain)
        texts.append(clean_cell(plain))
    return texts, apply_url


def cells_to_row(cells: list[str], apply_url: str) -> dict[str, str] | None:
    if len(cells) < 5:
        return None
    # Skip header-like rows
    if cells[0] in ("公司名称", "公司"):
        return None
    company = cells[0]
    if not company or company in ("-", "—"):
        return None

    # Normalize length to 10 columns
    padded = (cells + [""] * 10)[:10]
    row = {
        "公司": padded[0],
        "标题": padded[1],
        "批次": padded[2],
        "更新时间": padded[3],
        "招聘岗位": padded[4],
        "工作地点": padded[5],
        "行业": padded[6],
        "招聘类型": padded[7],
        "截止时间": padded[8],
        "投递链接": apply_url,
    }
    if not row["投递链接"] and padded[9].startswith("http"):
        row["投递链接"] = padded[9]
    return row


def parse_html_table(html: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for tr in split_table_rows(html):
        cells, apply_url = parse_row_cells(tr)
        item = cells_to_row(cells, apply_url)
        if item:
            rows.append(item)
    return rows


def with_page(url: str, current: int, page_size: int = 20) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs["current"] = [str(current)]
    qs["pageSize"] = [str(page_size)]
    query = urlencode({k: v[-1] for k, v in qs.items()})
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment)
    )


def detect_total_pages(html: str, page_size: int = 20) -> int:
    """Parse '共 N 条' or RSC total field; default 1."""
    m = re.search(r"共\s*(\d+)\s*条", html or "")
    if m:
        total = int(m.group(1))
        return max(1, (total + page_size - 1) // page_size)
    # Next.js RSC often escapes quotes: \"total\":125,\"current\":1,\"pageSize\":20
    m2 = re.search(
        r'\\*"total\\*"\s*:\s*(\d+)\s*,\s*\\*"current\\*"\s*:\s*\d+\s*,\s*\\*"pageSize\\*"\s*:\s*(\d+)',
        html or "",
    )
    if m2:
        total = int(m2.group(1))
        size = int(m2.group(2)) or page_size
        return max(1, (total + size - 1) // size)
    m3 = re.search(r'"total"\s*:\s*(\d+)', html or "")
    if m3:
        total = int(m3.group(1))
        if total > page_size:
            return max(1, (total + page_size - 1) // page_size)
    return 1


def fetch_html(url: str, timeout: float = 30.0) -> tuple[str, int, str]:
    if httpx is None:
        raise RuntimeError("httpx not installed; pip install -r qiuzhao/scripts/requirements.txt")
    with httpx.Client(
        follow_redirects=True,
        timeout=timeout,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    ) as client:
        resp = client.get(url)
    return resp.text or "", resp.status_code, str(resp.url)


def fetch_all_http_pages(
    url: str, timeout: float = 30.0, page_size: int = 20, max_pages: int = 30
) -> tuple[list[dict[str, str]], int | None, str]:
    first_url = with_page(url, 1, page_size)
    html, http_status, final_url = fetch_html(first_url, timeout=timeout)
    rows = parse_html_table(html)
    pages = detect_total_pages(html, page_size=page_size)

    # If total detection failed but first page is full, keep walking until empty/dup
    walk_until_empty = pages <= 1 and len(rows) >= page_size
    if walk_until_empty:
        pages = max_pages

    seen = {row_key(r) for r in rows}
    for current in range(2, pages + 1):
        page_url = with_page(url, current, page_size)
        page_html, _, _ = fetch_html(page_url, timeout=timeout)
        page_rows = parse_html_table(page_html)
        if not page_rows:
            break
        new_count = 0
        for r in page_rows:
            k = row_key(r)
            if k in seen:
                continue
            seen.add(k)
            rows.append(r)
            new_count += 1
        if walk_until_empty and new_count == 0:
            break
        # Refresh page estimate if later pages expose total
        if not walk_until_empty:
            pass
        else:
            detected = detect_total_pages(page_html, page_size=page_size)
            if detected > 1:
                pages = min(max_pages, detected)
                walk_until_empty = False
    return dedupe(rows), http_status, final_url


def row_key(row: dict[str, str]) -> str:
    return f"{row.get('公司','').strip()}|{row.get('标题','').strip()}|{row.get('投递链接','').strip()}"


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for r in rows:
        k = row_key(r)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def match_keywords(row: dict[str, str], keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = " ".join(
        [
            row.get("公司", ""),
            row.get("标题", ""),
            row.get("招聘岗位", ""),
            row.get("行业", ""),
        ]
    ).lower()
    for kw in keywords:
        k = kw.strip().lower()
        if not k:
            continue
        if k in blob:
            return True
    return False


def fetch_with_playwright(url: str, timeout_ms: int = 60000) -> list[dict[str, str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("playwright not installed") from exc

    ensure_playwright_browsers_path()
    all_rows: list[dict[str, str]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(2500)

        for _ in range(20):
            html = page.content()
            page_rows = parse_html_table(html)
            if page_rows:
                all_rows.extend(page_rows)

            # Try next page button
            next_btn = page.locator(
                "button:has-text('下一页'), .ant-pagination-next:not(.ant-pagination-disabled), "
                "li.ant-pagination-next:not(.ant-pagination-disabled), a:has-text('下一页')"
            )
            clicked = False
            try:
                if next_btn.count() > 0 and next_btn.first.is_enabled():
                    cls = next_btn.first.get_attribute("class") or ""
                    if "disabled" not in cls:
                        next_btn.first.click()
                        page.wait_for_timeout(2000)
                        clicked = True
            except Exception:  # noqa: BLE001
                clicked = False

            if not clicked:
                # Try numbered pages: click page N+1 if visible
                try:
                    pages = page.locator(".ant-pagination-item, .pagination li a, a.page-link")
                    current = page.locator(
                        ".ant-pagination-item-active, .pagination .active, .page-item.active"
                    )
                    cur_text = current.first.inner_text().strip() if current.count() else ""
                    advanced = False
                    if cur_text.isdigit():
                        want = str(int(cur_text) + 1)
                        for i in range(pages.count()):
                            t = pages.nth(i).inner_text().strip()
                            if t == want:
                                pages.nth(i).click()
                                page.wait_for_timeout(2000)
                                advanced = True
                                break
                    if not advanced:
                        break
                except Exception:  # noqa: BLE001
                    break

        browser.close()
    return dedupe(all_rows)


def fetch_offerstar(
    url: str,
    *,
    timeout: float = 30.0,
    use_playwright: bool = True,
    filter_keywords: list[str] | None = None,
) -> dict[str, Any]:
    keywords = filter_keywords or []
    rows: list[dict[str, str]] = []
    status = "ok"
    error: str | None = None
    http_status: int | None = None
    final_url = url
    mode = "http"

    try:
        rows, http_status, final_url = fetch_all_http_pages(url, timeout=timeout)
        mode = "http_paged"
        if not rows:
            status = "empty"
            error = "no table rows in HTTP HTML"
        else:
            status = "ok"
    except Exception as exc:  # noqa: BLE001
        status = "error"
        error = str(exc)

    if use_playwright and (status != "ok" or len(rows) < 20):
        try:
            pw_rows = fetch_with_playwright(url)
            if len(pw_rows) > len(rows):
                rows = pw_rows
                mode = "playwright"
                status = "ok"
                error = None
            elif rows:
                mode = mode or "http_paged"
                status = "ok"
                error = None
            elif pw_rows:
                rows = pw_rows
                mode = "playwright"
                status = "ok"
                error = None
        except Exception as exc:  # noqa: BLE001
            if rows:
                status = "ok_partial"
                error = f"playwright unavailable or failed ({exc}); returning HTTP pages"
            else:
                status = "error"
                error = f"http+playwright failed: {exc}"

    rows = dedupe(rows)
    if keywords:
        rows = [r for r in rows if match_keywords(r, keywords)]

    if status == "ok" and not rows and not keywords:
        status = "empty"
        error = error or "parsed zero rows"

    return {
        "url": url,
        "final_url": final_url,
        "fetched_at": utc_now_iso(),
        "status": status,
        "mode": mode,
        "http_status": http_status,
        "row_count": len(rows),
        "filter_keywords": keywords,
        "rows": rows,
        "error": error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch OfferStar recruitment list as JSON")
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", help="Write JSON path")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--no-playwright",
        action="store_true",
        help="Only use HTTP first page",
    )
    parser.add_argument(
        "--filter-keywords",
        default="",
        help="Comma-separated keywords; keep rows matching any",
    )
    args = parser.parse_args(argv)

    keywords = [k.strip() for k in args.filter_keywords.split(",") if k.strip()]
    payload = fetch_offerstar(
        args.url,
        timeout=args.timeout,
        use_playwright=not args.no_playwright,
        filter_keywords=keywords,
    )
    raw = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw + "\n", encoding="utf-8")
    else:
        sys.stdout.write(raw + "\n")

    return 0 if payload.get("status") in ("ok", "ok_partial") else 2


if __name__ == "__main__":
    raise SystemExit(main())
