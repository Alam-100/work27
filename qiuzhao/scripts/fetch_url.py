#!/usr/bin/env python3
"""Fetch a URL and extract main text for qiuzhao pipelines.

Output JSON contract:
  url, final_url, title, fetched_at, text, markdown,
  status (ok|blocked|empty|error), http_status, content_length, error

Usage:
  python qiuzhao/scripts/fetch_url.py --url "https://..." [--out path.json] [--min-chars 200]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

try:
    import trafilatura
except ImportError:
    trafilatura = None  # type: ignore

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-fetch/1.0"
)

BLOCK_HINTS = (
    "captcha",
    "access denied",
    "just a moment",
    "cf-browser-verification",
    "请完成安全验证",
    "验证码",
    "登录后查看",
    "请先登录",
    "sign in to continue",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def result(
    *,
    url: str,
    final_url: str = "",
    title: str = "",
    text: str = "",
    markdown: str = "",
    status: str,
    http_status: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    body = text or markdown
    return {
        "url": url,
        "final_url": final_url or url,
        "title": title or "",
        "fetched_at": utc_now_iso(),
        "text": text or "",
        "markdown": markdown or text or "",
        "status": status,
        "http_status": http_status,
        "content_length": len(body),
        "error": error,
    }


def looks_blocked(html: str, http_status: int | None) -> bool:
    if http_status in (401, 403, 429, 503):
        return True
    low = (html or "").lower()
    return any(h in low for h in BLOCK_HINTS)


def extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S)
    if not m:
        return ""
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    return title[:300]


def extract_with_trafilatura(html: str, url: str) -> tuple[str, str, str]:
    """Return (text, markdown, title)."""
    if trafilatura is None:
        return "", "", ""
    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        favor_recall=False,
    ) or ""
    md = (
        trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            output_format="markdown",
            favor_recall=False,
        )
        or text
    )
    meta = trafilatura.extract_metadata(html)
    title = (meta.title if meta and meta.title else "") or ""
    return text.strip(), (md or "").strip(), title


def strip_tags_fallback(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html or "")
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def fetch_url(url: str, timeout: float = 30.0, min_chars: int = 200) -> dict[str, Any]:
    if httpx is None:
        return result(
            url=url,
            status="error",
            error="httpx not installed; pip install -r qiuzhao/scripts/requirements.txt",
        )

    try:
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
    except Exception as exc:  # noqa: BLE001
        return result(url=url, status="error", error=str(exc))

    final_url = str(resp.url)
    http_status = resp.status_code
    html = resp.text or ""
    title_guess = extract_title(html)

    if looks_blocked(html, http_status):
        return result(
            url=url,
            final_url=final_url,
            title=title_guess,
            status="blocked",
            http_status=http_status,
            error="page looks blocked, login-walled, or rate-limited; use Playwright or paste",
        )

    if http_status >= 400:
        return result(
            url=url,
            final_url=final_url,
            title=title_guess,
            status="error",
            http_status=http_status,
            error=f"HTTP {http_status}",
        )

    text, markdown, title_ext = extract_with_trafilatura(html, final_url)
    title = title_ext or title_guess

    if not text and not markdown:
        fallback = strip_tags_fallback(html)
        if len(fallback) >= min_chars:
            text = fallback
            markdown = fallback
        else:
            return result(
                url=url,
                final_url=final_url,
                title=title,
                status="empty",
                http_status=http_status,
                error="extracted body too short or empty; try Playwright MCP",
            )

    body = text or markdown
    if len(body) < min_chars:
        return result(
            url=url,
            final_url=final_url,
            title=title,
            text=text,
            markdown=markdown,
            status="empty",
            http_status=http_status,
            error=f"body shorter than min_chars={min_chars}; try Playwright MCP",
        )

    return result(
        url=url,
        final_url=final_url,
        title=title,
        text=text,
        markdown=markdown,
        status="ok",
        http_status=http_status,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch URL main content for qiuzhao")
    parser.add_argument("--url", required=True, help="Page URL to fetch")
    parser.add_argument("--out", help="Write JSON to this path (else stdout)")
    parser.add_argument("--min-chars", type=int, default=200, help="Minimum body length")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)

    payload = fetch_url(args.url, timeout=args.timeout, min_chars=args.min_chars)
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
