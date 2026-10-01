#!/usr/bin/env python3
"""Extract 四方股份 / 点点互动 campus JD via side-panel click + Beisen campus list."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "qiuzhao" / "tmp" / "deepen_batch2_extra.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_jd(text: str) -> bool:
    return len(text) >= 180 and bool(
        re.search(r"岗位职责|任职要求|工作职责|岗位要求|任职资格", text)
    )


def extract_jd(text: str) -> str:
    m = re.search(r"(岗位职责|任职要求|工作职责|岗位要求|任职资格).{0,3500}", text, re.S)
    return (m.group(0) if m else text)[:3500]


def deepen_sifang(page) -> dict:
    out = {
        "公司": "四方股份",
        "岗位": "智能体开发工程师",
        "截止": "2026-09-19",
        "地点": "北京",
        "批次": "提前批",
        "投递链接": "https://sf-auto.zhiye.com/campus/jobs",
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    apis: list[dict] = []

    def on_response(resp):
        if "JobAd" in resp.url or "Jobad" in resp.url:
            try:
                apis.append({"url": resp.url, "data": resp.json()})
            except Exception:  # noqa: BLE001
                pass

    page.on("response", on_response)
    page.goto("https://sf-auto.zhiye.com/campus/jobs", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)

    # Prefer API data if duties already embedded
    for a in apis:
        data = a.get("data", {}).get("Data")
        if not isinstance(data, list):
            continue
        for item in data:
            title = str(item.get("JobTitle") or item.get("Title") or item.get("Name") or "")
            if "智能体" not in title:
                continue
            # common Beisen/zhiye fields
            duty = str(
                item.get("Duty")
                or item.get("JobDuty")
                or item.get("Responsibility")
                or item.get("JobDescription")
                or ""
            )
            req = str(
                item.get("Require")
                or item.get("Requirement")
                or item.get("Qualification")
                or item.get("JobRequire")
                or ""
            )
            blob = json.dumps(item, ensure_ascii=False)
            # strip HTML
            duty_c = re.sub(r"<[^>]+>", "\n", duty)
            req_c = re.sub(r"<[^>]+>", "\n", req)
            text = f"岗位职责\n{duty_c}\n任职要求\n{req_c}".strip()
            if not is_jd(text):
                # try full item text fields
                for k, v in item.items():
                    if isinstance(v, str) and ("职责" in v or "要求" in v or "Agent" in v):
                        text = re.sub(r"<[^>]+>", "\n", v)
                        break
            if is_jd(text) or (len(duty_c) > 50 and len(req_c) > 30):
                jid = item.get("Id") or item.get("JobAdId") or ""
                out["岗位"] = title.split("(")[0].strip() or out["岗位"]
                out["jd_text"] = text if is_jd(text) else f"岗位职责\n{duty_c}\n\n任职要求\n{req_c}"
                out["投递链接"] = (
                    f"https://sf-auto.zhiye.com/campus/jobs/{jid}" if jid else page.url
                )
                out["status"] = "ok"
                out["api_keys"] = list(item.keys())[:40]
                return out
            # keep raw for debug
            out["reason"] = f"api hit title but fields weak keys={list(item.keys())[:25]}"
            Path(__file__).resolve().parent.joinpath("sifang_job_raw.json").write_text(
                json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    # Click side panel
    loc = page.locator("div[class*='STListItem']").filter(has_text="智能体开发工程师")
    if loc.count() == 0:
        loc = page.get_by_text("智能体开发工程师", exact=False)
    loc.first.click(timeout=5000)
    page.wait_for_timeout(2500)
    text = page.locator("body").inner_text()
    # Isolate from title to next job title-ish
    m = re.search(
        r"智能体开发工程师\(J13834\).{0,50}(?P<body>.{200,2500}?)(?=主回路设计工程师|硬件开发工程师|信息化设计|$)",
        text,
        re.S,
    )
    chunk = m.group(0) if m else text
    # Also grab from known duty nodes near selection
    detail_text = page.evaluate(
        """() => {
          const sel = document.querySelector(\"div[class*='STListItem'][class*='active'], div[class*='selected'], div[class*='STDetail'], div[class*='JobDetail']\");
          if (sel) return sel.innerText || '';
          // fallback: largest text block containing Agent
          let best = '';
          for (const el of document.querySelectorAll('div')) {
            const t = el.innerText || '';
            if (t.includes('Agent') && t.includes('智能体') && t.length > best.length && t.length < 5000) best = t;
          }
          return best;
        }"""
    )
    final = detail_text if is_jd(detail_text) else chunk
    out["投递链接"] = page.url
    if is_jd(final) or ("Agent" in final and len(final) > 150):
        out["jd_text"] = extract_jd(final) if is_jd(final) else final[:3500]
        out["status"] = "ok"
    else:
        out["jd_text"] = (final or text)[:1000]
        out["reason"] = out.get("reason") or "side panel click no JD"
    return out


def deepen_joinquant_campus(page) -> dict:
    """Prefer 大模型应用工程师（校招） over intern if present."""
    url = (
        "https://app.mokahr.com/campus-recruitment/joinquant/92347"
        "#/jobs?keyword=%E5%A4%A7%E6%A8%A1%E5%9E%8B&page=1&anchorName=jobsList"
    )
    out = {
        "公司": "聚宽投资",
        "岗位": "大模型应用工程师（校招）",
        "截止": "2026-09-27",
        "地点": "北京、上海、深圳、广州",
        "批次": "27秋招",
        "投递链接": url,
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000)
    try:
        page.get_by_text("大模型应用工程师（校招）", exact=False).first.click(timeout=4000)
        page.wait_for_timeout(2500)
    except Exception:  # noqa: BLE001
        try:
            page.get_by_text("大模型应用工程师", exact=False).first.click(timeout=4000)
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            pass
    text = page.locator("body").inner_text()
    out["投递链接"] = page.url
    if is_jd(text) and re.search(r"Agent|大模型|RAG|智能体", text, re.I):
        out["jd_text"] = extract_jd(text)
        # detect title
        if "实习生" in text and "校招" not in page.url:
            for line in text.splitlines():
                if "大模型应用" in line and len(line) < 40:
                    out["岗位"] = line.strip()
                    break
        out["status"] = "ok"
    else:
        out["reason"] = "campus engineer card not opened"
        out["jd_text"] = text[:600]
    return out


def deepen_diandian_campus(page) -> dict:
    out = {
        "公司": "点点互动",
        "岗位": "AI Agent工程师",
        "截止": "2026-09-11",
        "地点": "北京、上海、深圳、广州",
        "批次": "提前批",
        "投递链接": "https://ddhd.cn/campus/jobs",
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    for url in [
        "https://ddhd.cn/campus/jobs",
        "https://ddhd.cn/campus",
        "https://ddhd.cn/4",
    ]:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(3500)
        except Exception:  # noqa: BLE001
            continue
        out["投递链接"] = page.url
        # search
        try:
            page.fill("input[placeholder*='搜索']", "Agent")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            pass
        try:
            page.get_by_text(re.compile(r"AI\s*Agent|Agent工程师", re.I)).first.click(timeout=4000)
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            pass
        text = page.locator("body").inner_text()
        if is_jd(text):
            out["jd_text"] = extract_jd(text)
            out["投递链接"] = page.url
            out["status"] = "ok"
            return out
        # try click list item
        try:
            page.locator("div[class*='STListItem'], div[class*='job']").filter(
                has_text=re.compile(r"Agent", re.I)
            ).first.click(timeout=3000)
            page.wait_for_timeout(2500)
            text = page.locator("body").inner_text()
            if is_jd(text) or ("Agent" in text and "职责" in text):
                out["jd_text"] = extract_jd(text) if is_jd(text) else text[:3500]
                out["投递链接"] = page.url
                out["status"] = "ok"
                return out
        except Exception:  # noqa: BLE001
            pass
    out["reason"] = "campus Agent job not found or no JD"
    out["jd_text"] = text[:800] if "text" in dir() else ""
    return out


def deepen_tencent_one(page) -> dict:
    """Click first 青云 智能体 topic into detail."""
    out = {
        "公司": "腾讯-青云计划",
        "岗位": "",
        "截止": "2026-09-14",
        "地点": "深圳",
        "批次": "提前批",
        "投递链接": "https://join.qq.com/post.html?query=p_14",
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    page.goto(
        "https://join.qq.com/post.html?query=p_14&keyword=%E6%99%BA%E8%83%BD%E4%BD%93",
        wait_until="domcontentloaded",
        timeout=45000,
    )
    page.wait_for_timeout(4000)
    title = "电脑操作智能体"
    try:
        page.get_by_text(title, exact=False).first.click(timeout=4000)
        page.wait_for_timeout(3500)
    except Exception:  # noqa: BLE001
        try:
            page.get_by_text("智能体", exact=False).nth(2).click(timeout=4000)
            page.wait_for_timeout(3500)
        except Exception:  # noqa: BLE001
            out["reason"] = "cannot click topic"
            return out
    text = page.locator("body").inner_text()
    out["投递链接"] = page.url
    out["岗位"] = title
    # Tencent detail often uses 课题介绍 / 岗位要求
    if re.search(r"课题介绍|岗位职责|任职要求|岗位要求|研究方向|工作内容", text) and len(text) > 300:
        m = re.search(
            r"(课题介绍|岗位职责|任职要求|岗位要求|研究方向|工作内容).{0,3500}",
            text,
            re.S,
        )
        out["jd_text"] = (m.group(0) if m else text)[:3500]
        out["status"] = "ok"
    else:
        out["jd_text"] = text[:800]
        out["reason"] = f"detail page no markers url={page.url}"
    return out


def main() -> int:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(locale="zh-CN").new_page()
        for name, fn in [
            ("四方股份", deepen_sifang),
            ("聚宽校招岗", deepen_joinquant_campus),
            ("点点互动校招", deepen_diandian_campus),
            ("腾讯青云一条", deepen_tencent_one),
        ]:
            print(f"extra: {name}", flush=True)
            r = fn(page)
            print(f"  -> {r['status']} {r.get('岗位','')} {r.get('reason','')}", flush=True)
            results.append(r)
        browser.close()
    ok = [r for r in results if r["status"] == "ok"]
    payload = {"fetched_at": utc_now(), "ok_count": len(ok), "results": results, "ok": ok}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ok={len(ok)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
