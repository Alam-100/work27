"""Agent queue + study API for SPA more-menu."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import vault_io as vio

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/jobs")
def list_jobs(status: str | None = None):
    jobs = vio.list_agent_jobs(status=status)
    return {
        "items": [
            {
                "id": j.id,
                "created_at": j.created_at,
                "intent": j.intent,
                "payload": j.payload,
                "status": j.status,
                "result": j.result,
            }
            for j in reversed(jobs[-80:])
        ],
        "pending": len([j for j in jobs if j.status == "待处理"]),
    }


class AgentJobCreate(BaseModel):
    intent: str
    payload: str = ""


@router.post("/jobs")
def create_job(body: AgentJobCreate):
    try:
        job = vio.append_agent_job(body.intent, body.payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "ok": True,
        "job": {
            "id": job.id,
            "created_at": job.created_at,
            "intent": job.intent,
            "payload": job.payload,
            "status": job.status,
            "result": job.result,
        },
    }


@router.get("/study")
def list_study():
    cards = vio.list_study()
    return {
        "items": [vio.note_card_to_dict(c) for c in cards],
        "open": [vio.note_card_to_dict(c) for c in cards if c.meta.get("状态") != "完成"],
        "done": [vio.note_card_to_dict(c) for c in cards if c.meta.get("状态") == "完成"],
    }


class StudyCreate(BaseModel):
    title: str
    study_type: str = "手撕"
    company: str = ""
    due: str = ""
    link: str = ""
    note: str = ""


@router.post("/study")
def create_study(body: StudyCreate):
    link = body.link
    if body.study_type == "手撕" and not link:
        link = "[[秋招/06_知识库/手撕与算法/高频手撕清单]]"
    card = vio.create_study_task(
        body.title,
        body.study_type,
        company=body.company,
        due=body.due,
        link=link,
        note=body.note,
    )
    return {"ok": True, "item": vio.note_card_to_dict(card)}


class StudyStatus(BaseModel):
    status: str


@router.patch("/study/{stem}")
def patch_study(stem: str, body: StudyStatus):
    try:
        card = vio.update_study_fields(stem, {"状态": body.status})
    except FileNotFoundError:
        raise HTTPException(404, "找不到学习任务") from None
    return {"ok": True, "item": vio.note_card_to_dict(card)}
