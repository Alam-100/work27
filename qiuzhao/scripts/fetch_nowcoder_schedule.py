#!/usr/bin/env python3
"""Fetch 牛客校招日程 via np-api list-card (paginated).

batch mapping:
  1203 -> 校招提前批 / 27提前批
  1206 -> 校招正式批 / 27秋招
  1210 -> 校招正式批 / 27届秋招

Usage:
  py -3.12 qiuzhao/scripts/fetch_nowcoder_schedule.py --batch 1203,1206,1210
  py -3.12 qiuzhao/scripts/fetch_nowcoder_schedule.py --batch 1206 --no-filter
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse, parse_qs

import httpx

BATCH_META: dict[str, dict[str, str]] = {
    "1203": {"批次标签": "27提前批", "招聘计划": "校招提前批"},
    "1206": {"批次标签": "27秋招", "招聘计划": "校招正式批"},
    "1210": {"批次标签": "27秋招", "招聘计划": "校招正式批"},
}

LIST_API = "https://www.nowcoder.com/np-api/u/school-schedule/list-card"
HOT_API = "https://www.nowcoder.com/school/schedule/hot-search-card"
SCHEDULE_URL = (
    "https://www.nowcoder.com/jobs/school/schedule"
    "?jobFirstId=11226&jobType=11200&tab=1&batch={batch}"
)

# Software-dev filter on schedule page
DEFAULT_CAREER_JOB_ID = "11200"

DEFAULT_KEYWORDS = [
    "Agent",
    "AI Agent",
    "Agent开发",
    "智能体",
    "大模型",
    "大模型应用",
    "RAG",
    "LLM",
    "人工智能",
    "AI",
]

WHITELIST = {
    "百度",
    "快手",
    "科大讯飞",
    "网易",
    "字节",
    "腾讯",
    "阿里",
    "拼多多",
    "阶跃",
    "智谱",
    "大疆",
    "商汤",
    "月之暗面",
    "MiniMax",
    "美团",
    "京东",
    "华为",
    "OPPO",
    "vivo",
    "小米",
    "滴滴",
    "蚂蚁",
    "哔哩",
    "B站",
    "360",
    "同花顺",
    "深信服",
    "Unity",
    "莉莉丝",
    "鹰角",
    "米哈游",
    "理想",
    "Momenta",
    "昆仑",
    "智元",
    "宇树",
    "普渡",
    "元戎",
    "NVIDIA",
    "英伟达",
    "虹软",
    "讯飞",
    "乐元素",
    "七牛",
    "TP-LINK",
    "海康",
    "大华",
    "云从",
    "依图",
    "旷视",
    "出门问问",
    "面壁",
    "百川",
    "零一万物",
    "DeepSeek",
    "深度求索",
    "腾讯音乐",
    "网易游戏",
    "雷火",
    # 央国企 / 银行（第四档）
    "工商银行",
    "工行",
    "建设银行",
    "建行",
    "农业银行",
    "农行",
    "中国银行",
    "中行",
    "交通银行",
    "交行",
    "邮储",
    "邮政储蓄",
    "国家开发银行",
    "国开",
    "进出口银行",
    "农业发展银行",
    "农发",
    "招商银行",
    "招行",
    "中信银行",
    "中信",
    "浦发",
    "兴业银行",
    "民生银行",
    "光大银行",
    "华夏银行",
    "平安银行",
    "广发银行",
    "北京银行",
    "上海银行",
    "江苏银行",
    "宁波银行",
    "南京银行",
    "中国移动",
    "移动",
    "中国电信",
    "电信",
    "中国联通",
    "联通",
    "中国铁塔",
    "铁塔",
    "国家电网",
    "国网",
    "南方电网",
    "南网",
    "中石油",
    "中国石油",
    "中石化",
    "中国石化",
    "中海油",
    "中国海油",
    "中国电科",
    "电科",
    "中国电子",
    "航天科工",
    "航天科技",
    "航空工业",
    "中核",
    "中国核",
    "中车",
    "中国中车",
    "中铁",
    "中建",
    "中国人寿",
    "人寿",
    "中国人保",
    "人保",
    "太保",
    "太平洋保险",
    "新华保险",
    # 外企（第五档）
    "亚马逊",
    "Amazon",
    "微软",
    "Microsoft",
    "谷歌",
    "Google",
    "Alphabet",
    "苹果",
    "Apple",
    "Meta",
    "Facebook",
    "英伟达",
    "NVIDIA",
    "英特尔",
    "Intel",
    "IBM",
    "甲骨文",
    "Oracle",
    "SAP",
    "西门子",
    "Siemens",
    "特斯拉",
    "Tesla",
    "高通",
    "Qualcomm",
    "Adobe",
    "Salesforce",
    "VMware",
    "博通",
    "Broadcom",
}

WEIXIN_RE = re.compile(r"mp\.weixin\.qq\.com|weixin://|wxaurl", re.I)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 qiuzhao-nowcoder/1.0"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_weixin(url: str) -> bool:
    return bool(url and WEIXIN_RE.search(url))


def unwrap_jump(url: str) -> str:
    if not url:
        return ""
    if "nowcoder.com/jump" in url:
        qs = parse_qs(urlparse(url).query)
        inner = qs.get("url", [""])[0]
        return unquote(inner) if inner else url
    return url


def in_whitelist(company: str) -> bool:
    c = company.strip().lower()
    for w in WHITELIST:
        if w.lower() in c:
            return True
    return False


def ms_to_date(ms: Any) -> str:
    try:
        if ms is None:
            return ""
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).date().isoformat()
    except Exception:
        return ""


def normalize_item(raw: dict[str, Any], batch: str) -> dict[str, str]:
    meta = BATCH_META.get(batch, {})
    name = str(raw.get("name") or "").strip()
    apply = unwrap_jump(str(raw.get("customWangshenLink") or "").strip())
    source = str(raw.get("sourceInformation") or "").strip()
    cities = raw.get("cityList") or []
    if isinstance(cities, list):
        city_s = "、".join(str(c) for c in cities)
    else:
        city_s = str(cities)
    careers = raw.get("careerNameList") or []
    career_s = "、".join(str(c) for c in careers) if isinstance(careers, list) else str(careers)
    return {
        "公司": name,
        "简介": str(raw.get("companyEvaluation") or "").strip(),
        "城市": city_s,
        "职能": career_s,
        "批次文案": str(raw.get("batchName") or meta.get("批次标签") or ""),
        "投递链接": apply,
        "公告链接": source,
        "网申开始": ms_to_date(raw.get("wangshenBeginDate")),
        "网申结束": ms_to_date(raw.get("wangshenEndDate")),
        "companyId": str(raw.get("companyId") or ""),
        "end": str(raw.get("end") or "0"),
        "batch_id": batch,
        "批次标签": meta.get("批次标签", ""),
        "招聘计划": meta.get("招聘计划", ""),
        "来源链接": SCHEDULE_URL.format(batch=batch),
    }


def should_keep(row: dict[str, str], keywords: list[str], strict: bool) -> bool:
    if is_weixin(row.get("投递链接") or ""):
        return False
    company = row.get("公司", "")
    blob = f"{company} {row.get('简介','')} {row.get('职能','')}"
    if in_whitelist(company):
        return True
    low = blob.lower()
    for kw in keywords:
        k = kw.strip().lower()
        if k and k in low:
            return True
    if strict:
        return False
    return "人工智能" in row.get("职能", "")


def fetch_hot(client: httpx.Client) -> dict[str, str]:
    r = client.get(HOT_API, timeout=30)
    r.raise_for_status()
    data = r.json()
    out: dict[str, str] = {}
    for item in data.get("data") or []:
        name = str(item.get("companyName") or "").strip()
        url = unwrap_jump(str(item.get("rawUrl") or "").strip())
        if name and url and not is_weixin(url):
            out[name] = url
    return out


def fetch_batch_pages(
    client: httpx.Client,
    batch: str,
    career_job_id: str,
    page_size: int = 20,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    page = 1
    total_page = 1
    while page <= total_page:
        resp = client.post(
            LIST_API,
            data={
                "careerJobId": career_job_id,
                "query": "",
                "propertyId": "",
                "batchId": batch,
                "page": str(page),
                "pageSize": str(page_size),
                "tab": "1",
            },
            timeout=45,
        )
        resp.raise_for_status()
        payload = resp.json()
        block = (payload.get("data") or {}) if isinstance(payload, dict) else {}
        total_page = int(block.get("totalPage") or 1)
        for item in block.get("datas") or []:
            if isinstance(item, dict) and item.get("name"):
                rows.append(normalize_item(item, batch))
        page += 1
        if page > 50:
            break
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default="1203,1206,1210")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--filter-keywords", default=",".join(DEFAULT_KEYWORDS))
    ap.add_argument("--no-filter", action="store_true")
    ap.add_argument("--career-job-id", default=DEFAULT_CAREER_JOB_ID)
    ap.add_argument("--update-source-links", action="store_true")
    args = ap.parse_args()

    batches = [b.strip() for b in args.batch.split(",") if b.strip()]
    keywords = [k.strip() for k in args.filter_keywords.split(",") if k.strip()]
    strict = not args.no_filter

    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://www.nowcoder.com/jobs/school/schedule",
        "Origin": "https://www.nowcoder.com",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }

    all_rows: list[dict[str, str]] = []
    by_batch: dict[str, list[dict[str, str]]] = {}
    hot: dict[str, str] = {}

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        try:
            hot = fetch_hot(client)
        except Exception as e:
            print(f"hot-search failed: {e}", file=sys.stderr)
        for b in batches:
            print(f"=== batch {b} {BATCH_META.get(b, {})}", flush=True)
            rows = fetch_batch_pages(client, b, args.career_job_id)
            # enrich apply url from hot when missing / weixin
            for r in rows:
                if (not r.get("投递链接") or is_weixin(r["投递链接"])) and r["公司"] in hot:
                    r["投递链接"] = hot[r["公司"]]
                # fuzzy hot match
                if not r.get("投递链接") or is_weixin(r.get("投递链接") or ""):
                    for hn, hu in hot.items():
                        if r["公司"] in hn or hn in r["公司"]:
                            r["投递链接"] = hu
                            break
            print(f"  raw {len(rows)}", flush=True)
            by_batch[b] = rows
            all_rows.extend(rows)

        # add hot-only companies not in list (still useful leads)
        for name, url in hot.items():
            if any(r["公司"] == name for r in all_rows):
                continue
            if is_weixin(url):
                continue
            all_rows.append(
                {
                    "公司": name,
                    "简介": "牛客热门推荐",
                    "城市": "",
                    "职能": "",
                    "批次文案": "热门",
                    "投递链接": url,
                    "公告链接": "",
                    "网申开始": "",
                    "网申结束": "",
                    "companyId": "",
                    "end": "0",
                    "batch_id": "hot",
                    "批次标签": "混合",
                    "招聘计划": "校招正式批",
                    "来源链接": HOT_API,
                }
            )

    kept: list[dict[str, str]] = []
    for r in all_rows:
        if should_keep(r, keywords, strict=strict):
            kept.append(r)

    dedup: list[dict[str, str]] = []
    seen: set[str] = set()
    for r in kept:
        k = f"{r.get('公司')}|{r.get('batch_id')}"
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)

    payload = {
        "fetched_at": utc_now_iso(),
        "batches": batches,
        "raw_count": len(all_rows),
        "filtered_count": len(dedup),
        "hot_count": len(hot),
        "rows": dedup,
        "raw_by_batch_counts": {b: len(v) for b, v in by_batch.items()},
        "hot": hot,
    }

    out = args.out
    if out is None:
        out = Path(__file__).resolve().parents[1] / "tmp" / "nowcoder_filtered.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    tmp = Path(__file__).resolve().parents[1] / "tmp"
    for b, rows in by_batch.items():
        pth = tmp / f"nowcoder_{b}.json"
        pth.write_text(
            json.dumps(
                {
                    "fetched_at": utc_now_iso(),
                    "batch": b,
                    "meta": BATCH_META.get(b, {}),
                    "count": len(rows),
                    "rows": rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    if args.update_source_links:
        src = Path(__file__).resolve().parents[1] / "data" / "source_links.json"
        if src.exists():
            data = json.loads(src.read_text(encoding="utf-8"))
            today = date.today().isoformat()
            for link in data.get("links", []):
                u = link.get("url", "")
                for b in batches:
                    if f"batch={b}" in u:
                        link["status"] = "有效" if by_batch.get(b) else "失效"
                        link["last_checked"] = today
            data["updated"] = today
            src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {"out": str(out), "filtered": len(dedup), "raw": len(all_rows), "hot": len(hot)},
            ensure_ascii=False,
        )
    )
    for r in dedup[:40]:
        link = (r.get("投递链接") or "")[:90]
        print(f"- [{r.get('批次标签')}] {r.get('公司')} | {link}", flush=True)


if __name__ == "__main__":
    main()
