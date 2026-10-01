#!/usr/bin/env python3
"""Batch-2 deepen: force list→detail click on zhiye/Moka/etc., keep only substantive JD."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qiuzhao" / "tmp" / "deepen_batch2.json"

TARGETS = [
    {
        "公司": "四方股份",
        "岗位": "智能体开发工程师",
        "url": "https://sf-auto.zhiye.com/campus/jobs",
        "search": "智能体",
        "title_re": r"智能体开发工程师",
        "截止": "2026-09-19",
        "地点": "北京",
        "批次": "提前批",
    },
    {
        "公司": "天锐星通",
        "岗位": "AI agent工程师",
        "url": "https://t-ray.zhiye.com/campus/jobs",
        "search": "agent",
        "title_re": r"AI\s*agent|agent工程师",
        "截止": "2026-09-12",
        "地点": "上海、南京、成都",
        "批次": "提前批",
    },
    {
        "公司": "点点互动",
        "岗位": "AI Agent工程师",
        "url": "https://ddhd.cn/4",
        "search": "Agent",
        "title_re": r"AI\s*Agent",
        "截止": "2026-09-11",
        "地点": "北京、上海、深圳、广州",
        "批次": "提前批",
    },
    {
        "公司": "聚宽投资",
        "岗位": "大模型应用开发",
        "url": "https://app.mokahr.com/campus-recruitment/joinquant/92347#/jobs",
        "search": "大模型",
        "title_re": r"大模型应用|Agent",
        "截止": "2026-09-27",
        "地点": "北京、上海、深圳、广州",
        "批次": "27秋招",
    },
    {
        "公司": "同花顺",
        "岗位": "agent算法工程师",
        "url": "http://campus.10jqka.com.cn/mobile/job/list",
        "search": "agent",
        "title_re": r"agent算法|Agent",
        "截止": "2026-09-19",
        "地点": "杭州",
        "批次": "提前批",
    },
    {
        "公司": "深信服",
        "岗位": "",
        "url": "https://app.mokahr.com/campus-recruitment/sangfor/27944?locale=zh-CN#/jobs",
        "search": "智能体",
        "title_re": r"Agent|智能体",
        "截止": "2026-09-21",
        "地点": "深圳",
        "批次": "提前批",
    },
    {
        "公司": "百度",
        "岗位": "",
        "url": "https://talent.baidu.com/jobs/list",
        "search": "智能体",
        "title_re": r"智能体|Agent",
        "截止": "2026-09-28",
        "地点": "北京、上海、深圳",
        "批次": "27秋招",
    },
    {
        "公司": "腾讯CDG",
        "岗位": "",
        "url": "https://join.qq.com/post.html?query=p_2",
        "search": "Agent",
        "title_re": r"Agent|智能体|大模型",
        "截止": "2026-09-28",
        "地点": "深圳、北京、上海",
        "批次": "27秋招",
    },
    {
        "公司": "腾讯WXG",
        "岗位": "",
        "url": "https://join.qq.com/m/qingyun.html",
        "search": "智能体",
        "title_re": r"智能体|Agent|大模型",
        "截止": "2026-09-28",
        "地点": "广州、深圳、北京、上海",
        "批次": "27秋招",
    },
    {
        "公司": "腾讯-青云计划",
        "岗位": "",
        "url": "https://join.qq.com/post.html?query=p_14",
        "search": "智能体",
        "title_re": r"智能体|Agent|大语言模型",
        "截止": "2026-09-14",
        "地点": "深圳、北京、上海、广州",
        "批次": "提前批",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_jd(text: str) -> bool:
    if len(text) < 200:
        return False
    return bool(re.search(r"岗位职责|任职要求|工作职责|岗位要求|任职资格|Responsibilities|Requirements", text))


def body(page) -> str:
    try:
        return page.locator("body").inner_text(timeout=8000)
    except Exception:  # noqa: BLE001
        return ""


def search(page, kw: str) -> None:
    for sel in [
        "input[placeholder*='搜索']",
        "input[placeholder*='职位']",
        "input[placeholder*='岗位']",
        "input[type='search']",
        "input[type='text']",
    ]:
        loc = page.locator(sel)
        if loc.count() == 0:
            continue
        try:
            loc.first.fill(kw, timeout=1500)
            loc.first.press("Enter")
            page.wait_for_timeout(2500)
            return
        except Exception:  # noqa: BLE001
            continue


def click_title(page, pattern: str) -> bool:
    """Prefer short job-title like nodes; click into detail."""
    rx = re.compile(pattern, re.I)
    # Prefer anchors / job cards
    selectors = [
        "a",
        "[class*='job'] a",
        "[class*='position'] a",
        "[class*='Job']",
        "[class*='job-title']",
        "[class*='position-title']",
        "li",
        "div[role='button']",
        "button",
    ]
    seen: set[str] = set()
    for sel in selectors:
        loc = page.locator(sel)
        n = min(loc.count(), 100)
        for i in range(n):
            el = loc.nth(i)
            try:
                t = (el.inner_text(timeout=400) or "").strip()
            except Exception:  # noqa: BLE001
                continue
            # Use first line only for matching
            first = t.splitlines()[0].strip() if t else ""
            if not first or len(first) > 80:
                continue
            if first in seen:
                continue
            if not rx.search(first):
                continue
            if re.search(r"登录|注册|筛选|分享|清除|搜索|首页|全部职位", first):
                continue
            seen.add(first)
            try:
                with page.expect_navigation(timeout=8000, wait_until="domcontentloaded"):
                    el.click(timeout=2500)
            except Exception:  # noqa: BLE001
                try:
                    el.click(timeout=2500)
                    page.wait_for_timeout(2500)
                except Exception:  # noqa: BLE001
                    continue
            page.wait_for_timeout(2000)
            return True
    return False


def extract_jd(text: str) -> str:
    m = re.search(r"(岗位职责|任职要求|工作职责|岗位要求|任职资格).{0,4000}", text, re.S)
    return (m.group(0) if m else text)[:4000]


def guess_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if re.search(r"Agent|智能体|大模型应用", line, re.I) and 4 < len(line) < 60:
            if not re.search(r"登录|筛选|分享|职位摘要", line):
                return line
    return fallback or "Agent相关（待核对岗名）"


def deepen(page, t: dict) -> dict:
    out = {
        **{k: t.get(k, "") for k in ("公司", "岗位", "截止", "地点", "批次")},
        "投递链接": t["url"],
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    try:
        page.goto(t["url"], wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3500)
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"goto: {exc}"
        return out

    text = body(page)
    if re.search(r"(登录后|请登录|验证码|扫码关注|微信扫码)", text) and len(text) < 500:
        out["status"] = "login_wall"
        out["reason"] = "login/captcha wall"
        return out

    if is_jd(text):
        out["jd_text"] = extract_jd(text)
        out["投递链接"] = page.url
        out["status"] = "ok"
        if not out["岗位"]:
            out["岗位"] = guess_title(text, "")
        return out

    kw = t.get("search") or "Agent"
    search(page, kw)
    title_re = t.get("title_re") or r"Agent|智能体|大模型"
    clicked = click_title(page, title_re)
    if not clicked:
        # second keyword pass
        alt = "Agent" if kw != "Agent" else "智能体"
        search(page, alt)
        clicked = click_title(page, title_re)

    text = body(page)
    out["投递链接"] = page.url
    if is_jd(text):
        out["jd_text"] = extract_jd(text)
        out["status"] = "ok"
        if not out["岗位"]:
            out["岗位"] = guess_title(text, "")
    else:
        out["jd_text"] = text[:600]
        out["reason"] = "no 岗位职责/任职要求 after detail click" if clicked else "no matching job title clicked"
    return out


def main() -> int:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        page = context.new_page()
        for t in TARGETS:
            print(f"deepen: {t['公司']}", flush=True)
            r = deepen(page, t)
            print(f"  -> {r['status']} {r.get('岗位','')} {r.get('reason','')}", flush=True)
            results.append(r)
        browser.close()

    ok = [r for r in results if r["status"] == "ok"]
    payload = {
        "fetched_at": utc_now(),
        "ok_count": len(ok),
        "count": len(results),
        "results": results,
        "ok": ok,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ok={len(ok)}/{len(results)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
