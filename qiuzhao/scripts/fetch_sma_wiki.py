#!/usr/bin/env python3
"""Fetch sma-wiki 27届校园招聘汇总表 into structured JSON.

Site: https://campus.sma-wiki.cn/campus/campus_recruit.html?channel=zpdt
Data lives in page global RAW_DATA (embedded in inline script).

Default filters: industry=互联网/科技, batch=27届秋招.
Reject WeChat-only apply URLs by default; unwrap nowcoder jump redirects.

Usage:
  python qiuzhao/scripts/fetch_sma_wiki.py --out sma_wiki.json
  python qiuzhao/scripts/fetch_sma_wiki.py --out agent.json \\
    --filter-keywords \"Agent,智能体,大模型应用\" --limit 50
  python qiuzhao/scripts/fetch_sma_wiki.py --diff-vault --out sma_wiki_gap.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from playwright_env import ensure_playwright_browsers_path  # noqa: E402

DEFAULT_URL = "https://campus.sma-wiki.cn/campus/campus_recruit.html?channel=zpdt"
DEFAULT_INDUSTRY = "互联网"
DEFAULT_BATCH = "27届秋招"
DEFAULT_KEYWORDS: list[str] = []  # empty = keep all after industry/batch filter
WEIXIN_RE = re.compile(r"mp\.weixin\.qq\.com|weixin://|wxaurl", re.I)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-sma-wiki/1.0"
)

# Strip common suffixes/tags when matching vault folder names
COMPANY_NOISE_RE = re.compile(
    r"(2027校园招聘|校园招聘|校招|集团|股份有限公司|有限公司|科技|网络|"
    r"\s*[|丨｜].*$|\s*[（(].*?[）)].*$)"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_weixin(url: str) -> bool:
    return bool(url and WEIXIN_RE.search(url))


def unwrap_nowcoder_jump(url: str) -> str:
    """Extract real target from nowcoder jump affiliate links."""
    if not url:
        return ""
    try:
        p = urlparse(url)
        if "nowcoder.com" in (p.netloc or "") and "/jump" in (p.path or ""):
            qs = parse_qs(p.query)
            target = (qs.get("url") or [""])[0]
            if target:
                return unquote(target)
    except Exception:  # noqa: BLE001
        pass
    return url


def normalize_company_key(name: str) -> str:
    s = (name or "").strip()
    s = re.sub(r"\s+", "", s)
    # Drop trailing marketing tag after space-like separators already stripped
    for sep in ("—", "-", "·"):
        if sep in s:
            s = s.split(sep, 1)[0]
    s = COMPANY_NOISE_RE.sub("", s)
    return s.lower()


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
    apply_url = unwrap_nowcoder_jump(str(raw.get("appLink") or "").strip())
    source_url = unwrap_nowcoder_jump(str(raw.get("sourceLink") or "").strip())
    return {
        "公司": company,
        "职位摘要": str(raw.get("positions") or "").strip(),
        "地点": str(raw.get("location") or "").strip(),
        "截止": str(raw.get("deadline") or "").strip(),
        "批次": str(raw.get("batch") or "").strip(),
        "行业": str(raw.get("industry") or "").strip(),
        "性质": str(raw.get("nature") or "").strip(),
        "投递链接": apply_url,
        "公告链接": source_url,
        "简介": str(raw.get("evaluation") or "").strip(),
        "更新时间": str(raw.get("fullDate") or raw.get("updateDate") or "").strip(),
        "精选": "1" if raw.get("isKey") or raw.get("isFeaturedCard") else "",
    }


def filter_raw_rows(
    raw_rows: list[dict[str, Any]],
    *,
    industry: str,
    batch: str,
    reject_weixin: bool,
    keywords: list[str],
    limit: int,
) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []
    seen: set[str] = set()
    ind = (industry or "").strip()
    bat = (batch or "").strip()
    for raw in raw_rows:
        item = normalize_row(raw)
        if not item:
            continue
        if ind and ind not in item["行业"]:
            continue
        if bat and bat not in item["批次"]:
            continue
        if reject_weixin and is_weixin(item["投递链接"]):
            continue
        if not match_keywords(item, keywords):
            continue
        key = f"{item['公司']}|{item['投递链接']}"
        if key in seen:
            continue
        seen.add(key)
        rows_out.append(item)
        if limit and len(rows_out) >= limit:
            break
    return rows_out


def load_raw_data(page) -> list[dict[str, Any]]:
    data = page.evaluate(
        """() => {
          if (typeof RAW_DATA === 'undefined' || !Array.isArray(RAW_DATA)) return null;
          return RAW_DATA;
        }"""
    )
    return data if isinstance(data, list) else []


def wait_for_raw_data(page, timeout_ms: int = 90000) -> bool:
    page.wait_for_function(
        "() => typeof RAW_DATA !== 'undefined' && Array.isArray(RAW_DATA) && RAW_DATA.length > 0",
        timeout=timeout_ms,
    )
    return True


def fetch_sma_wiki(
    url: str = DEFAULT_URL,
    *,
    timeout_ms: int = 90000,
    industry: str = DEFAULT_INDUSTRY,
    batch: str = DEFAULT_BATCH,
    reject_weixin: bool = True,
    filter_keywords: list[str] | None = None,
    limit: int = 0,
) -> dict[str, Any]:
    keywords = list(filter_keywords) if filter_keywords is not None else list(DEFAULT_KEYWORDS)
    status = "ok"
    error: str | None = None
    rows_out: list[dict[str, str]] = []
    total_raw = 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return {
            "url": url,
            "fetched_at": utc_now_iso(),
            "status": "error",
            "mode": "playwright_raw_data",
            "row_count": 0,
            "total_raw": 0,
            "industry": industry,
            "batch": batch,
            "filter_keywords": keywords,
            "rows": [],
            "error": f"playwright not installed: {exc}",
        }

    try:
        ensure_playwright_browsers_path()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT, locale="zh-CN")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                wait_for_raw_data(page, timeout_ms=timeout_ms)
            except Exception:  # noqa: BLE001
                page.wait_for_timeout(5000)
            raw_rows = load_raw_data(page)
            if not raw_rows:
                page.wait_for_timeout(8000)
                raw_rows = load_raw_data(page)
            browser.close()

        total_raw = len(raw_rows)
        rows_out = filter_raw_rows(
            raw_rows,
            industry=industry,
            batch=batch,
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
        "mode": "playwright_raw_data",
        "row_count": len(rows_out),
        "total_raw": total_raw,
        "industry": industry,
        "batch": batch,
        "reject_weixin": reject_weixin,
        "filter_keywords": keywords,
        "rows": rows_out,
        "error": error,
    }


def list_vault_companies(vault_intel: Path) -> set[str]:
    if not vault_intel.is_dir():
        return set()
    return {d.name for d in vault_intel.iterdir() if d.is_dir()}


def company_in_vault(name: str, vault: set[str]) -> str | None:
    """Return matched vault folder name if present."""
    if name in vault:
        return name
    # Direct substring / prefix matches
    key = normalize_company_key(name)
    for v in vault:
        vk = normalize_company_key(v)
        if not vk:
            continue
        if key == vk or key.startswith(vk) or vk.startswith(key):
            return v
        if len(vk) >= 2 and (vk in key or key in vk):
            return v
    # Manual aliases for common aggregator naming
    aliases = {
        "满帮集团": "满帮",
        "拼多多": "拼多多集团",
        "pdd": "拼多多集团",
        "阿里": "阿里巴巴",
        "alibaba": "阿里巴巴",
        "字节": "字节跳动",
        "bytedance": "字节跳动",
        "网易": "网易智企",
        "boss": "BOSS直聘",
        "贝壳": "贝壳找房",
    }
    for a, target in aliases.items():
        if a in name.lower() or a in name:
            if target in vault:
                return target
    return None


def diff_against_vault(
    rows: list[dict[str, str]], vault_companies: set[str]
) -> dict[str, Any]:
    missing: list[dict[str, str]] = []
    present: list[dict[str, str]] = []
    for r in rows:
        hit = company_in_vault(r["公司"], vault_companies)
        item = dict(r)
        if hit:
            item["vault匹配"] = hit
            present.append(item)
        else:
            missing.append(item)
    # Deduplicate missing by normalized company
    seen: set[str] = set()
    missing_uniq: list[dict[str, str]] = []
    for m in missing:
        k = normalize_company_key(m["公司"]) or m["公司"]
        if k in seen:
            continue
        seen.add(k)
        missing_uniq.append(m)
    return {
        "vault_count": len(vault_companies),
        "source_row_count": len(rows),
        "present_count": len(present),
        "missing_count": len(missing_uniq),
        "missing": missing_uniq,
        "present_sample": present[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch sma-wiki campus recruit summary")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--industry", default=DEFAULT_INDUSTRY)
    parser.add_argument("--batch", default=DEFAULT_BATCH)
    parser.add_argument("--allow-weixin", action="store_true")
    parser.add_argument(
        "--filter-keywords",
        default="",
        help="Comma-separated keywords on 公司/职位摘要; empty=all",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout-ms", type=int, default=90000)
    parser.add_argument(
        "--diff-vault",
        action="store_true",
        help="Also write missing-vs-vault analysis into the same JSON under key gap",
    )
    parser.add_argument(
        "--vault-intel",
        type=Path,
        default=Path(r"E:\obsidian\My_docs\秋招\02_情报库"),
    )
    args = parser.parse_args()

    keywords = [x.strip() for x in args.filter_keywords.split(",") if x.strip()]
    result = fetch_sma_wiki(
        args.url,
        timeout_ms=args.timeout_ms,
        industry=args.industry,
        batch=args.batch,
        reject_weixin=not args.allow_weixin,
        filter_keywords=keywords,
        limit=args.limit,
    )
    if args.diff_vault and result.get("status") == "ok":
        vault = list_vault_companies(args.vault_intel)
        result["gap"] = diff_against_vault(result.get("rows") or [], vault)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"status={result.get('status')} raw={result.get('total_raw')} "
        f"rows={result.get('row_count')} out={args.out}"
    )
    if args.diff_vault and "gap" in result:
        g = result["gap"]
        print(
            f"gap missing={g.get('missing_count')} present={g.get('present_count')} "
            f"vault={g.get('vault_count')}"
        )
    return 0 if result.get("status") in ("ok", "empty") else 1


if __name__ == "__main__":
    sys.exit(main())
