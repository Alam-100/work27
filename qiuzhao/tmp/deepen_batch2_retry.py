#!/usr/bin/env python3
"""Retry deepen with site-specific detail navigation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qiuzhao" / "tmp" / "deepen_batch2_retry.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def body(page) -> str:
    try:
        return page.locator("body").inner_text(timeout=8000)
    except Exception:  # noqa: BLE001
        return ""


def is_jd(text: str) -> bool:
    if len(text) < 180:
        return False
    return bool(re.search(r"岗位职责|任职要求|工作职责|岗位要求|任职资格", text))


def extract_jd(text: str) -> str:
    m = re.search(r"(岗位职责|任职要求|工作职责|岗位要求|任职资格).{0,3500}", text, re.S)
    return (m.group(0) if m else text)[:3500]


def slice_job_block(text: str, title_hint: str) -> str | None:
    """From a Moka multi-JD list page, slice the block around matching title."""
    lines = text.splitlines()
    idx = -1
    for i, line in enumerate(lines):
        if re.search(title_hint, line, re.I) and len(line.strip()) < 80:
            idx = i
            break
    if idx < 0:
        return None
    chunk = "\n".join(lines[idx : idx + 80])
    if is_jd(chunk):
        return extract_jd(chunk)
    # expand window
    chunk = "\n".join(lines[idx : idx + 160])
    return extract_jd(chunk) if is_jd(chunk) else None


def click_text(page, pattern: str) -> bool:
    # Try get_by_text
    try:
        loc = page.get_by_text(re.compile(pattern, re.I))
        n = min(loc.count(), 20)
        for i in range(n):
            el = loc.nth(i)
            try:
                t = (el.inner_text(timeout=500) or "").strip()
            except Exception:  # noqa: BLE001
                continue
            if len(t) > 100:
                continue
            try:
                el.scroll_into_view_if_needed(timeout=2000)
            except Exception:  # noqa: BLE001
                pass
            try:
                with page.expect_navigation(timeout=10000, wait_until="domcontentloaded"):
                    el.click(timeout=3000, force=True)
            except Exception:  # noqa: BLE001
                try:
                    el.click(timeout=3000, force=True)
                    page.wait_for_timeout(3000)
                except Exception:  # noqa: BLE001
                    continue
            page.wait_for_timeout(1500)
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


def click_zhiye_job(page, title: str) -> bool:
    """Zhiye: find anchor whose text contains title, prefer href with /job."""
    handles = page.evaluate(
        """(title) => {
          const out = [];
          for (const a of document.querySelectorAll('a')) {
            const t = (a.innerText || '').trim().split('\\n')[0];
            if (!t || t.length > 80) continue;
            if (!t.includes(title) && !new RegExp(title, 'i').test(t)) continue;
            out.push({text: t, href: a.href || '', id: a.id || ''});
          }
          return out.slice(0, 10);
        }""",
        title,
    )
    print(f"    zhiye candidates: {handles}", flush=True)
    for h in handles or []:
        href = h.get("href") or ""
        if href and href != page.url:
            try:
                page.goto(href, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)
                return True
            except Exception as exc:  # noqa: BLE001
                print(f"    goto href fail: {exc}", flush=True)
    # fallback text click
    return click_text(page, re.escape(title))


def deepen_sifang(page) -> dict:
    url = "https://sf-auto.zhiye.com/campus/jobs"
    out = {
        "公司": "四方股份",
        "岗位": "智能体开发工程师",
        "截止": "2026-09-19",
        "地点": "北京",
        "批次": "提前批",
        "投递链接": url,
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000)
    # search
    try:
        page.fill("input[placeholder*='搜索']", "智能体")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)
    except Exception:  # noqa: BLE001
        pass
    clicked = click_zhiye_job(page, "智能体开发工程师")
    if not clicked:
        clicked = click_zhiye_job(page, "智能体")
    text = body(page)
    out["投递链接"] = page.url
    print(f"    url={page.url} len={len(text)} jd={is_jd(text)}", flush=True)
    if is_jd(text):
        out["jd_text"] = extract_jd(text)
        out["status"] = "ok"
    else:
        out["jd_text"] = text[:800]
        out["reason"] = "zhiye detail missing JD sections"
    return out


def deepen_joinquant(page) -> dict:
    url = (
        "https://app.mokahr.com/campus-recruitment/joinquant/92347"
        "#/jobs?keyword=%E5%A4%A7%E6%A8%A1%E5%9E%8B&page=1&anchorName=jobsList"
    )
    out = {
        "公司": "聚宽投资",
        "岗位": "大模型应用开发",
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
    text = body(page)
    # Prefer slicing the matching job block from SPA list
    block = slice_job_block(text, r"大模型应用")
    if block and re.search(r"大模型|Agent|智能体|LLM", block, re.I):
        out["jd_text"] = block
        out["投递链接"] = page.url
        out["status"] = "ok"
        # try click into detail for cleaner URL
        click_text(page, r"大模型应用")
        t2 = body(page)
        if is_jd(t2) and re.search(r"大模型应用", t2):
            out["jd_text"] = extract_jd(t2)
            out["投递链接"] = page.url
        return out

    clicked = click_text(page, r"大模型应用")
    text = body(page)
    out["投递链接"] = page.url
    if is_jd(text) and re.search(r"大模型|Agent|智能体", text, re.I):
        # Ensure it's not a wrong sibling job: require title near start or keyword in duties
        block = slice_job_block(text, r"大模型应用") or extract_jd(text)
        if re.search(r"大模型|Agent|智能体|LLM|Prompt|RAG", block, re.I):
            out["jd_text"] = block
            out["status"] = "ok"
            return out
    out["jd_text"] = (block or text)[:800]
    out["reason"] = "no Agent/大模型 JD block" + (" after click" if clicked else "")
    return out


def deepen_diandian(page) -> dict:
    url = "https://ddhd.cn/4"
    out = {
        "公司": "点点互动",
        "岗位": "AI Agent工程师",
        "截止": "2026-09-11",
        "地点": "北京、上海、深圳、广州",
        "批次": "提前批",
        "投递链接": url,
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000)
    # Beisen often has job list under 应届生校招
    for label in ["应届生校招", "Elite Program", "职位", "社会招聘"]:
        try:
            page.get_by_text(label, exact=False).first.click(timeout=2000)
            page.wait_for_timeout(2000)
        except Exception:  # noqa: BLE001
            pass
    clicked = click_text(page, r"AI\s*Agent|Agent工程师")
    # Also try scrolling and collecting links
    if not clicked:
        hrefs = page.evaluate(
            """() => [...document.querySelectorAll('a')].map(a => ({t:(a.innerText||'').trim().slice(0,60), h:a.href})).filter(x => /Agent|智能体/i.test(x.t)).slice(0,10)"""
        )
        print(f"    diandian links: {hrefs}", flush=True)
        for h in hrefs or []:
            if h.get("h"):
                try:
                    page.goto(h["h"], wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2500)
                    clicked = True
                    break
                except Exception:  # noqa: BLE001
                    continue
    text = body(page)
    out["投递链接"] = page.url
    if is_jd(text):
        out["jd_text"] = extract_jd(text)
        out["status"] = "ok"
        out["岗位"] = "AI Agent工程师"
    else:
        out["jd_text"] = text[:800]
        out["reason"] = "landing/FAQ only, no JD"
    return out


def deepen_ths(page) -> dict:
    url = "https://campus.10jqka.com.cn/"
    out = {
        "公司": "同花顺",
        "岗位": "agent算法工程师",
        "截止": "2026-09-19",
        "地点": "杭州",
        "批次": "提前批",
        "投递链接": url,
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000)
    for label in ["职位列表", "校园招聘", "热招职位", "岗位"]:
        try:
            page.get_by_text(label, exact=False).first.click(timeout=2000)
            page.wait_for_timeout(2000)
        except Exception:  # noqa: BLE001
            pass
    clicked = click_text(page, r"agent|Agent|智能体")
    text = body(page)
    out["投递链接"] = page.url
    print(f"    ths url={page.url} len={len(text)}", flush=True)
    if is_jd(text):
        out["jd_text"] = extract_jd(text)
        out["status"] = "ok"
    else:
        out["jd_text"] = text[:800]
        out["reason"] = "no JD" + (" after click" if clicked else "")
    return out


def deepen_tencent_detail(page) -> dict:
    """Open Tencent campus, search 智能体, click first matching post into detail."""
    url = "https://join.qq.com/post.html?query=p_14"
    out = {
        "公司": "腾讯-青云计划",
        "岗位": "",
        "截止": "2026-09-14",
        "地点": "深圳、北京、上海、广州",
        "批次": "提前批",
        "投递链接": url,
        "jd_text": "",
        "status": "no_jd",
        "reason": "",
    }
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000)
    try:
        page.fill("input[type='text']", "智能体")
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
    except Exception:  # noqa: BLE001
        pass
    # Click a card that looks like a job id row
    clicked = click_text(page, r"智能体|Agent|大语言模型")
    text = body(page)
    out["投递链接"] = page.url
    print(f"    tencent url={page.url} len={len(text)} jd={is_jd(text)}", flush=True)
    if is_jd(text):
        out["jd_text"] = extract_jd(text)
        out["status"] = "ok"
        for line in text.splitlines():
            line = line.strip()
            if re.search(r"智能体|Agent|大模型", line, re.I) and 4 < len(line) < 70:
                out["岗位"] = line
                break
    else:
        out["jd_text"] = text[:800]
        out["reason"] = "list only / login" if not clicked else "detail without JD markers"
    return out


def main() -> int:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(locale="zh-CN").new_page()
        for name, fn in [
            ("四方股份", deepen_sifang),
            ("聚宽投资", deepen_joinquant),
            ("点点互动", deepen_diandian),
            ("同花顺", deepen_ths),
            ("腾讯-青云计划", deepen_tencent_detail),
        ]:
            print(f"retry: {name}", flush=True)
            r = fn(page)
            print(f"  -> {r['status']} {r.get('reason','')}", flush=True)
            results.append(r)
        browser.close()

    ok = [r for r in results if r["status"] == "ok"]
    payload = {
        "fetched_at": utc_now(),
        "ok_count": len(ok),
        "results": results,
        "ok": ok,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ok={len(ok)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
