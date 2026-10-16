#!/usr/bin/env python3
"""Search Nowcoder interview posts and fetch full text (moments + discuss).

Does not write the vault. Output JSON for qiuzhao-mianshi-search ingest.

Usage:
  py -3.12 qiuzhao/scripts/fetch_nowcoder_mianshi.py --out qiuzhao/tmp/nowcoder_mianshi.json
  py -3.12 qiuzhao/scripts/fetch_nowcoder_mianshi.py --query "税友 Agent 面经" --pages 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

SEARCH_API = "https://gw-c.nowcoder.com/api/sparta/pc/search"
MOMENT_API = "https://gw-c.nowcoder.com/api/sparta/detail/moment-data/detail/{uuid}"
DISCUSS_API = "https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail/{cid}"
BJ = timezone(timedelta(hours=8))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-nowcoder-mianshi/1.0"
)

# Drop unless the intel card itself is that role.
MISMATCH = re.compile(
    r"硬件|嵌入式|售前|销售|产品经理|运营|前端实习|纯前端|"
    r"FPGA|模拟ic|射频|示波器|PCB|测试开发(?!.*Agent)|测开(?!.*Agent)",
    re.I,
)
JOB_OK = re.compile(
    r"Agent|智能体|大模型应用|LLM|RAG|AI应用|AI 应用|AI开发|AI 开发|"
    r"算法工程师|后端|研发|全栈|知识库",
    re.I,
)
TAG_STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

DEFAULT_QUERIES: list[dict[str, str]] = [
    {"company": "锐捷网络", "query": "星网锐捷 Agent 面经"},
    {"company": "锐捷网络", "query": "锐捷网络 AI 面经"},
    {"company": "广联达", "query": "广联达 Agent 面经"},
    {"company": "广联达", "query": "广联达 大模型 面经"},
    {"company": "税友", "query": "税友 Agent 面经"},
    {"company": "税友", "query": "税友 AI 面经 秋招"},
    {"company": "贝壳", "query": "贝壳 Agent 算法 面经"},
    {"company": "FunPlus", "query": "FunPlus Agent 面经"},
    {"company": "FunPlus", "query": "趣加 Agent 面经"},
    {"company": "百川智能", "query": "百川智能 Agent 面经"},
    {"company": "百川智能", "query": "百川源点 Agent 面经"},
    {"company": "思必驰", "query": "思必驰 Agent 面经"},
    {"company": "华橙网络", "query": "华橙网络 Agent 面经"},
    {"company": "北方华创", "query": "北方华创 Agent 面经"},
    {"company": "携程", "query": "携程 Agent 面经"},
    {"company": "同花顺", "query": "同花顺 Agent 面经"},
    {"company": "云帐房", "query": "云帐房 Agent 面经"},
    {"company": "顺丰科技", "query": "顺丰科技 AI 面经 Agent"},
    {"company": "合合信息", "query": "合合信息 Agent 面经"},
    {"company": "神州信息", "query": "神州信息 Agent 面经"},
    {"company": "新浪微博", "query": "微博 AI应用 面经"},
    {"company": "恒生电子", "query": "恒生电子 AI应用 面经"},
    {"company": "中兴通讯", "query": "中兴通讯 智能体 面经"},
    {"company": "京东", "query": "京东 Agent 面经 秋招"},
    {"company": "联想", "query": "联想 Agent 面经"},
    {"company": "去哪儿", "query": "去哪儿 Agent 面经"},
    {"company": "OPPO", "query": "OPPO Agent 面经"},
    {"company": "哔哩哔哩", "query": "B站 多模态 Agent 面经"},
    {"company": "大疆", "query": "大疆 Agent 面经"},
    {"company": "网易雷火", "query": "网易雷火 智能NPC 面经"},
    {"company": "蚂蚁集团", "query": "蚂蚁 智能体 面经 秋招"},
    {"company": "TCL", "query": "TCL AI应用 面经"},
    {"company": "得物", "query": "得物 大模型 面经"},
    {"company": "浩鲸", "query": "浩鲸 大模型 面经"},
    {"company": "达梦数据", "query": "达梦 Agent 面经"},
    {"company": "快递100", "query": "快递100 Agent 面经"},
    {"company": "树根科技", "query": "树根科技 智能体 面经"},
    {"company": "拓维信息", "query": "拓维信息 Agent 面经"},
    {"company": "思谋科技", "query": "思谋科技 Agent 面经"},
    {"company": "歌尔", "query": "歌尔 Agent 面经"},
    {"company": "光轮智能", "query": "光轮智能 Agent 面经"},
    {"company": "诺因智能", "query": "诺因智能 面经"},
    {"company": "神州数码", "query": "神州数码 Agent 面经"},
    {"company": "中移互联网", "query": "中移互联网 智能体 面经"},
    {"company": "中移在线", "query": "中移在线 智能体 面经"},
    {"company": "中国移动云公司", "query": "移动云 Agent 面经"},
    {"company": "九方智投", "query": "九方智投 Agent 面经"},
    {"company": "招银网络科技", "query": "招银网络 Agent 面经"},
    {"company": "科大讯飞", "query": "讯飞 Agent 面经 秋招"},
    {"company": "深信服", "query": "深信服 Agent 面经"},
    {"company": "腾讯", "query": "腾讯 Agent 开发 面经 秋招"},
    {"company": "拼多多集团", "query": "拼多多 Agent 面经"},
    {"company": "拼多多集团", "query": "拼多多 算法 面经 秋招"},
    {"company": "拼多多集团", "query": "拼多多 算法 一面"},
    {"company": "拼多多集团", "query": "拼多多 算法 二面"},
    {"company": "拼多多集团", "query": "拼多多 算法 三面"},
    {"company": "拼多多集团", "query": "pdd 算法 面经"},
    {"company": "拼多多集团", "query": "拼多多 大模型 算法 面经"},
    {"company": "拼多多集团", "query": "拼多多 LLM 面经"},
    {"company": "拼多多集团", "query": "拼多多 NLP 面经"},
    {"company": "拼多多集团", "query": "拼多多 智能体 面经"},
    {"company": "拼多多集团", "query": "pdd agent 面经"},
    {"company": "顺丰科技", "query": "顺丰科技 AI开发 面经"},
    {"company": "东方有线", "query": "东方有线 AI 面经 秋招"},
    {"company": "税友", "query": "税友 算法 面经 RAG"},
    {"company": "贝壳", "query": "贝壳 Agent 一面"},
    {"company": "FunPlus", "query": "FunPlus 多模态 面经"},
    {"company": "京东", "query": "京东 Agent 一面 秋招"},
    {"company": "中兴通讯", "query": "中兴 AI算法 智能体 面经"},
    {"company": "广联达", "query": "广联达 AI 一面"},
    {"company": "携程", "query": "携程 LLM 算法 面经"},
    {"company": "锐捷网络", "query": "锐捷 AI开发 一面"},
    {"company": "小米", "query": "小米 Agent 工程师 面经"},
    {"company": "东方有线", "query": "东方有线 AI 面经"},
    {"company": "鹰角网络", "query": "鹰角 Agent 面经"},
    {"company": "中车", "query": "中车 AI开发 面经"},
    {"company": "海信", "query": "海信 NLP 面经 秋招"},
    {"company": "百度", "query": "百度 智能体 面经 秋招"},
    {"company": "broad", "query": "Agent 面经 秋招"},
    {"company": "broad", "query": "智能体开发 一面 面经"},
    {"company": "broad", "query": "AI Agent 二面 面经"},
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def http_proxy() -> str | None:
    for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        v = os.environ.get(k, "").strip()
        if v.startswith("http://") or v.startswith("https://"):
            return v
    return None


def make_client() -> httpx.Client:
    # httpx socks extra is often missing; prefer HTTP proxy.
    os.environ.pop("ALL_PROXY", None)
    os.environ.pop("all_proxy", None)
    kwargs: dict[str, Any] = {
        "follow_redirects": True,
        "timeout": 25.0,
        "headers": {
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://www.nowcoder.com",
            "Referer": "https://www.nowcoder.com/search",
            "Content-Type": "application/json",
        },
    }
    proxy = http_proxy()
    if proxy:
        kwargs["proxy"] = proxy
    return httpx.Client(**kwargs)


def ms_to_bj(ms: Any) -> str:
    try:
        n = int(ms)
    except (TypeError, ValueError):
        return ""
    if n > 10_000_000_000:
        n //= 1000
    if n < 1_000_000_000:
        return ""
    return datetime.fromtimestamp(n, BJ).strftime("%Y-%m-%d %H:%M")


def strip_html(text: str) -> str:
    text = TAG_STRIP.sub(" ", text or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return WS.sub(" ", text).strip()


def rec_fields(rec: dict[str, Any], query_company: str) -> dict[str, Any]:
    if not isinstance(rec, dict):
        return {
            "query_company": query_company,
            "title": "",
            "uuid": "",
            "content_id": "",
            "content_type": None,
            "created_ms": "",
            "created_bj": "",
            "snippet": "",
            "url": "",
            "mismatch": True,
            "job_ok": False,
        }
    d = rec.get("data") or {}
    if not isinstance(d, dict):
        d = {}
    md = d.get("momentData") or {}
    ie = d.get("interviewExp") or {}
    title = rec.get("title") or md.get("title") or ie.get("title") or d.get("title") or ""
    uuid = md.get("uuid") or d.get("uuid") or ""
    content = md.get("content") or ie.get("content") or d.get("content") or ""
    created = md.get("createdAt") or md.get("createTime") or ie.get("createTime") or d.get("createTime")
    ctype = d.get("contentType")
    cid = str(d.get("contentId") or rec.get("entityDataId") or "")
    blob = f"{title} {strip_html(content)}"
    return {
        "query_company": query_company,
        "title": title,
        "uuid": uuid,
        "content_id": cid,
        "content_type": ctype,
        "created_ms": created,
        "created_bj": ms_to_bj(created),
        "snippet": strip_html(content)[:400],
        "url": (
            f"https://www.nowcoder.com/feed/main/detail/{uuid}"
            if uuid
            else (f"https://www.nowcoder.com/discuss/{cid}" if cid else "")
        ),
        "mismatch": bool(MISMATCH.search(blob)),
        "job_ok": bool(JOB_OK.search(blob)),
    }


def search_page(client: httpx.Client, query: str, page: int) -> list[dict[str, Any]]:
    r = client.post(SEARCH_API, json={"query": query, "type": "all", "page": page})
    r.raise_for_status()
    payload = r.json()
    if not payload.get("success"):
        raise RuntimeError(payload.get("msg") or "search failed")
    return list((payload.get("data") or {}).get("records") or [])


def fetch_detail(client: httpx.Client, item: dict[str, Any]) -> dict[str, Any]:
    uuid = item.get("uuid") or ""
    cid = item.get("content_id") or ""
    ctype = item.get("content_type")
    url = ""
    if uuid and ctype in (74, None, 0):
        url = MOMENT_API.format(uuid=uuid)
    elif cid and str(cid).isdigit() and len(str(cid)) >= 15:
        url = DISCUSS_API.format(cid=cid)
    elif uuid:
        url = MOMENT_API.format(uuid=uuid)
    elif cid:
        url = DISCUSS_API.format(cid=cid)
    if not url:
        return {**item, "detail_status": "no-id"}
    r = client.get(url, headers={**client.headers, "Referer": item.get("url") or "https://www.nowcoder.com/"})
    if r.status_code != 200:
        return {**item, "detail_status": f"http-{r.status_code}"}
    try:
        payload = r.json()
    except Exception:
        return {**item, "detail_status": "not-json", "detail_len": len(r.text)}
    data = payload.get("data") or {}
    content = data.get("content") or data.get("mdContent") or ""
    title = data.get("title") or item.get("title") or ""
    created = data.get("createdAt") or data.get("createTime") or item.get("created_ms")
    return {
        **item,
        "title": title or item.get("title"),
        "created_ms": created,
        "created_bj": ms_to_bj(created) or item.get("created_bj"),
        "content": strip_html(content),
        "content_raw_len": len(content or ""),
        "detail_status": "ok" if content else "empty",
        "show_content": bool((data.get("showMessage") or {}).get("showContent", True)),
    }


def in_window(created_bj: str, start: str, end: str) -> bool:
    if not created_bj:
        return False
    day = created_bj[:10]
    return start <= day <= end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="", help="single query; default = built-in company list")
    ap.add_argument("--company", default="", help="label for --query")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--sleep", type=float, default=0.35)
    ap.add_argument("--start", default="2026-08-20")
    ap.add_argument("--end", default="2026-10-16")
    ap.add_argument(
        "--queries-file",
        default="",
        help="JSON list of {company, query}; overrides default list when set",
    )
    ap.add_argument("--fetch-older", action="store_true", help="also fetch 2026 posts outside window")
    ap.add_argument("--max-fetch", type=int, default=80)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.query:
        queries = [{"company": args.company or "adhoc", "query": args.query}]
    elif args.queries_file:
        queries = json.loads(Path(args.queries_file).read_text(encoding="utf-8"))
    else:
        queries = DEFAULT_QUERIES
    client = make_client()
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    search_log: list[dict[str, Any]] = []

    for q in queries:
        company, query = q["company"], q["query"]
        page_n = 0
        kept = 0
        try:
            for page in range(1, args.pages + 1):
                recs = search_page(client, query, page)
                page_n += len(recs)
                for rec in recs:
                    item = rec_fields(rec, company)
                    key = item.get("uuid") or item.get("content_id") or item.get("title")
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    hits.append(item)
                    kept += 1
                time.sleep(args.sleep)
        except Exception as exc:  # noqa: BLE001
            search_log.append({"company": company, "query": query, "error": str(exc)})
            continue
        search_log.append({"company": company, "query": query, "raw": page_n, "unique_added": kept})
        time.sleep(args.sleep)

    windowed = [h for h in hits if in_window(h.get("created_bj") or "", args.start, args.end)]
    older_2026 = [
        h
        for h in hits
        if (h.get("created_bj") or "").startswith("2026")
        and h not in windowed
    ]
    to_fetch = [h for h in windowed if not h.get("mismatch")]
    if args.fetch_older:
        to_fetch.extend(h for h in older_2026 if not h.get("mismatch") and h.get("job_ok"))
    to_fetch = to_fetch[: args.max_fetch]

    details: list[dict[str, Any]] = []
    for item in to_fetch:
        try:
            details.append(fetch_detail(client, item))
        except Exception as exc:  # noqa: BLE001
            details.append({**item, "detail_status": f"error:{exc}"})
        time.sleep(args.sleep)

    payload = {
        "fetched_at": utc_now_iso(),
        "window": {"start": args.start, "end": args.end},
        "search_log": search_log,
        "hit_count": len(hits),
        "window_count": len(windowed),
        "older_2026_count": len(older_2026),
        "fetched_count": len(details),
        "hits": hits,
        "details": details,
    }
    out = args.out or (Path(__file__).resolve().parents[1] / "tmp" / "nowcoder_mianshi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    print(
        f"hits={len(hits)} window={len(windowed)} older2026={len(older_2026)} fetched={len(details)}"
    )
    ok = sum(1 for d in details if d.get("detail_status") == "ok")
    print(f"detail_ok={ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
