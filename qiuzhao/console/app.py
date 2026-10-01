"""Qiuzhao hybrid console — FastAPI JSON API + Jinja legacy + React SPA."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

CONSOLE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = CONSOLE_DIR.parent / "scripts"
WEB_DIST = CONSOLE_DIR.parent / "web" / "dist"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import vault_io as vio  # noqa: E402
from console.api import api_router  # noqa: E402

app = FastAPI(title="秋招控制台", docs_url="/api/docs", redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

templates = Jinja2Templates(directory=str(CONSOLE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(CONSOLE_DIR / "static")), name="static")
templates.env.filters["fmt_dt"] = vio.fmt_dt


def flash_redirect(url: str, msg: str) -> RedirectResponse:
    sep = "&" if "?" in url else "?"
    return RedirectResponse(f"{url}{sep}msg={quote(msg)}", status_code=303)


def render(request: Request, name: str, **ctx: Any):
    return templates.TemplateResponse(request, name, ctx)


def pending_count() -> int:
    return len(vio.list_agent_jobs(status="待处理"))


# ----- Legacy Jinja pages under /legacy -----


@app.get("/legacy", response_class=HTMLResponse)
@app.get("/legacy/", response_class=HTMLResponse)
async def legacy_today(request: Request, msg: str = ""):
    events = vio.events_in_window(days=3)
    study = vio.study_due_soon(days=3)
    pending = vio.list_agent_jobs(status="待处理")
    conflicts = vio.find_conflicts()
    return render(
        request,
        "today.html",
        page="today",
        msg=msg,
        events=events,
        study=study,
        pending_jobs=pending,
        conflicts=conflicts[:8],
        pending_count=len(pending),
        statuses=vio.PROGRESS_STATUSES,
    )


@app.get("/legacy/progress", response_class=HTMLResponse)
async def progress_list(request: Request, msg: str = ""):
    return render(
        request,
        "progress.html",
        page="progress",
        msg=msg,
        cards=vio.list_progress(),
        intel=vio.list_intel(),
        statuses=vio.PROGRESS_STATUSES,
        priorities=vio.PRIORITIES,
        results=vio.RESULTS,
        plans=vio.PLANS,
        pending_count=pending_count(),
    )


@app.post("/legacy/progress/from-intel")
async def progress_from_intel(intel_stem: str = Form(...)):
    card = vio.create_progress_from_intel(intel_stem)
    return flash_redirect(f"/legacy/progress/{card.stem}", f"已跟进：{card.stem}")


@app.get("/legacy/progress/{stem}", response_class=HTMLResponse)
async def progress_edit(request: Request, stem: str, msg: str = ""):
    card = vio.get_progress(stem)
    if not card:
        return flash_redirect("/legacy/progress", "找不到该进度卡")
    return render(
        request,
        "progress_edit.html",
        page="progress",
        msg=msg,
        card=card,
        statuses=vio.PROGRESS_STATUSES,
        priorities=vio.PRIORITIES,
        results=vio.RESULTS,
        plans=vio.PLANS,
        pending_count=pending_count(),
    )


@app.post("/legacy/progress/{stem}")
async def progress_save(
    stem: str,
    投递状态: str = Form(""),
    优先级: str = Form(""),
    结果: str = Form(""),
    招聘计划: str = Form(""),
    投递时间: str = Form(""),
    测评时间: str = Form(""),
    笔试时间: str = Form(""),
    一面: str = Form(""),
    二面: str = Form(""),
    三面: str = Form(""),
    HR面: str = Form(""),
    内推人: str = Form(""),
    内推码: str = Form(""),
    投递链接: str = Form(""),
    备注: str = Form(""),
    排序权重: str = Form("3"),
):
    if stem == "from-intel":
        return flash_redirect("/legacy/progress", "路由错误")
    vio.update_progress_fields(
        stem,
        {
            "投递状态": 投递状态,
            "优先级": 优先级,
            "结果": 结果,
            "招聘计划": 招聘计划,
            "投递时间": 投递时间,
            "测评时间": 测评时间,
            "笔试时间": 笔试时间,
            "一面": 一面,
            "二面": 二面,
            "三面": 三面,
            "HR面": HR面,
            "内推人": 内推人,
            "内推码": 内推码,
            "投递链接": 投递链接,
            "备注": 备注,
            "排序权重": 排序权重,
        },
    )
    return flash_redirect(f"/legacy/progress/{stem}", "已保存到 Obsidian")


@app.get("/legacy/intel", response_class=HTMLResponse)
async def intel_list(
    request: Request,
    msg: str = "",
    q: str = Query(""),
    plan: str = Query(""),
):
    cards = vio.list_intel()
    if q:
        ql = q.lower()
        cards = [
            c
            for c in cards
            if ql in str(c.meta.get("公司", "")).lower()
            or ql in str(c.meta.get("岗位", "")).lower()
            or ql in c.stem.lower()
        ]
    if plan:
        cards = [c for c in cards if str(c.meta.get("招聘计划", "")) == plan]
    return render(
        request,
        "intel.html",
        page="intel",
        msg=msg,
        cards=cards,
        q=q,
        plan=plan,
        plans=vio.PLANS,
        pending_count=pending_count(),
    )


@app.post("/legacy/intel/follow")
async def intel_follow(intel_stem: str = Form(...)):
    card = vio.create_progress_from_intel(intel_stem)
    return flash_redirect("/legacy/progress", f"已跟进并建进度：{card.stem}")


@app.post("/legacy/intel/verify")
async def intel_verify(intel_stem: str = Form(...)):
    intel = vio.get_intel(intel_stem)
    company = str((intel.meta.get("公司") if intel else None) or intel_stem)
    job = vio.append_agent_job("收集公司", f"核实:{company}|{intel_stem}")
    return flash_redirect("/legacy/intel", f"已入队核实 {job.id}，请在 Cursor 说：处理控制台任务")


@app.get("/legacy/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request, msg: str = ""):
    jobs = vio.list_agent_jobs()
    return render(
        request,
        "inbox.html",
        page="inbox",
        msg=msg,
        jobs=list(reversed(jobs[-40:])),
        pending_count=len([j for j in jobs if j.status == "待处理"]),
        intents=vio.AGENT_INTENTS,
    )


@app.post("/legacy/inbox/urls")
async def inbox_urls(urls: str = Form("")):
    lines = [ln.strip() for ln in urls.splitlines() if ln.strip()]
    urls_only = [ln for ln in lines if ln.startswith("http://") or ln.startswith("https://")]
    if not urls_only:
        return flash_redirect("/legacy/inbox", "未识别到 http(s) 链接")
    job = vio.append_agent_job("链接入库", " ".join(urls_only))
    return flash_redirect(
        "/legacy/inbox",
        f"已入队链接入库 {job.id}（{len(urls_only)} 条），Cursor 说：处理控制台任务",
    )


@app.post("/legacy/inbox/company")
async def inbox_company(company: str = Form("")):
    company = company.strip()
    if not company:
        return flash_redirect("/legacy/inbox", "请填写公司名")
    job = vio.append_agent_job("收集公司", company)
    return flash_redirect("/legacy/inbox", f"已入队收集 {company}（{job.id}）")


@app.post("/legacy/inbox/daily")
async def inbox_daily():
    job = vio.append_agent_job("每日情报更新", "")
    return flash_redirect("/legacy/inbox", f"已入队日更 {job.id}，Cursor 说：处理控制台任务")


@app.post("/legacy/inbox/images")
async def inbox_images(company: str = Form("")):
    company = company.strip() or "（见 _inbox_images）"
    job = vio.append_agent_job("面经图片", company)
    return flash_redirect("/legacy/inbox", f"已入队面经图片 {job.id}")


@app.get("/legacy/study", response_class=HTMLResponse)
async def study_page(request: Request, msg: str = ""):
    cards = vio.list_study()
    return render(
        request,
        "study.html",
        page="study",
        msg=msg,
        open_cards=[c for c in cards if c.meta.get("状态") != "完成"],
        done_cards=[c for c in cards if c.meta.get("状态") == "完成"],
        types=vio.STUDY_TYPES,
        statuses=vio.STUDY_STATUSES,
        pending_count=pending_count(),
    )


@app.post("/legacy/study/create")
async def study_create(
    标题: str = Form(...),
    类型: str = Form("手撕"),
    关联公司: str = Form(""),
    截止日期: str = Form(""),
    关联笔记: str = Form(""),
    备注: str = Form(""),
):
    if 类型 == "手撕" and not 关联笔记:
        关联笔记 = "[[秋招/06_知识库/手撕与算法/高频手撕清单]]"
    card = vio.create_study_task(
        标题,
        类型,
        company=关联公司,
        due=截止日期,
        link=关联笔记,
        note=备注,
    )
    return flash_redirect("/legacy/study", f"已安排：{card.meta.get('标题')}")


@app.post("/legacy/study/{stem}/status")
async def study_status(stem: str, 状态: str = Form(...)):
    vio.update_study_fields(stem, {"状态": 状态})
    return flash_redirect("/legacy/study", "状态已更新")


@app.get("/legacy/conflicts", response_class=HTMLResponse)
async def conflicts_page(request: Request, msg: str = ""):
    return render(
        request,
        "conflicts.html",
        page="conflicts",
        msg=msg,
        conflicts=vio.find_conflicts(),
        events=vio.events_in_window(days=14),
        pending_count=pending_count(),
    )


@app.post("/legacy/export-ics")
async def export_ics():
    import export_ics as ics_mod

    try:
        events = ics_mod.collect_events()
        body = "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-qiuzhao-assistant-export_ics-",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH",
                "X-WR-CALNAME:秋招日程",
                *events,
                "END:VCALENDAR",
                "",
            ]
        )
        ics_mod.OUT.parent.mkdir(parents=True, exist_ok=True)
        ics_mod.OUT.write_text(body, encoding="utf-8")
        return flash_redirect(
            "/legacy/conflicts",
            f"已导出 {len(events)} 个事件 → {ics_mod.OUT.name}",
        )
    except Exception as exc:  # noqa: BLE001
        return flash_redirect("/legacy/conflicts", f"导出失败：{exc}")


@app.get("/legacy/settings", response_class=HTMLResponse)
async def settings_page(request: Request, msg: str = ""):
    report = vio.health_check()
    return render(
        request,
        "settings.html",
        page="settings",
        msg=msg,
        report=report,
        env_vault=os.environ.get("QIUZHAO_VAULT", ""),
        pending_count=report.pending_jobs,
    )


# Update legacy template nav links to /legacy/*
# (done via base.html patch)


# ----- SPA static hosting -----

if WEB_DIST.is_dir():
    assets_dir = WEB_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="spa-assets")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Serve SPA index for client routes; fall back to legacy redirect if no build."""
    if full_path.startswith("api/") or full_path.startswith("legacy/") or full_path.startswith("static/"):
        return RedirectResponse("/legacy", status_code=404)

    index = WEB_DIST / "index.html"
    if index.is_file():
        # Prefer real files under dist (favicon etc.)
        candidate = WEB_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)

    # No SPA build yet → send users to legacy console
    if not full_path or full_path == "/":
        return RedirectResponse("/legacy", status_code=302)
    return RedirectResponse("/legacy", status_code=302)
