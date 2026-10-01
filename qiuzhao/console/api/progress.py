"""Progress / applications API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import vault_io as vio

router = APIRouter(prefix="/progress", tags=["progress"])


def _serialize_progress(card: vio.NoteCard, *, detail: bool = False) -> dict[str, Any]:
    data = vio.note_card_to_dict(card, include_body=detail)
    data["current_stage"] = vio.progress_current_stage(card)
    data["next_event"] = vio.progress_next_event(card)
    data["stages"] = vio.progress_to_stages(card)
    data["process"] = vio.get_progress_process(card)
    data["phase"] = vio.progress_phase(card)
    data["bucket"] = vio.progress_bucket(card)
    data["intel_stem"] = vio._wikilink_stem(card.meta.get("关联情报"))
    data["mianshi_stem"] = vio._wikilink_stem(card.meta.get("关联面经"))
    company = str(card.meta.get("公司") or "")
    position = str(card.meta.get("岗位") or "")
    intel = vio.get_intel(data["intel_stem"]) if data["intel_stem"] else None
    if intel:
        tier = vio.normalize_company_tier(intel.meta.get("公司档次"), company)
        role = str(intel.meta.get("岗位族") or "") or vio.infer_role_family(
            str(intel.meta.get("岗位") or position)
        )
        priority = str(intel.meta.get("投递优先级") or "") or vio.default_apply_priority(tier)
        if detail:
            data["intel"] = {
                "stem": intel.stem,
                "meta": vio._jsonable_meta(intel.meta),
                "body": intel.body,
            }
    else:
        tier = vio.normalize_company_tier("", company)
        role = vio.infer_role_family(position)
        priority = vio.default_apply_priority(tier)
    data["company_tier"] = tier
    data["role_family"] = role if role in vio.ROLE_FAMILIES else vio.infer_role_family(position)
    data["apply_priority"] = (
        priority if priority in vio.APPLY_PRIORITIES else vio.default_apply_priority(tier)
    )
    if detail and company:
        ov = vio.get_intel_company(company)
        if ov:
            data["company_overview"] = {
                "company": company,
                "apply_limit": vio.company_apply_limit(company),
                "apply_limit_note": str(ov.meta.get("投递上限说明") or ""),
                "portal": str(ov.meta.get("校招门户") or ""),
                "apply_channels": vio.company_apply_channels(ov.meta),
                "referral_url": str(ov.meta.get("内推链接") or ""),
                "referral_code": str(ov.meta.get("内推码") or ""),
                "delivery_record_url": vio.company_delivery_record_url(ov.meta),
            }
        else:
            data["company_overview"] = None
    return data


@router.get("/stats")
def progress_stats():
    return vio.progress_stats()


@router.get("")
def list_progress(tab: str = "all"):
    """tab filters for applications directory.

    Coarse: all | active | applying | interviewing | offer | rejected | stopped
    Fine:   apply | assessment | written | interview | waiting
    """
    cards = vio.list_progress()
    items = []
    fine_tabs = {"apply", "assessment", "written", "interview", "waiting"}
    for c in cards:
        phase = vio.progress_phase(c)
        bucket = vio.progress_bucket(c)

        if tab == "active" and phase in ("offer", "rejected", "stopped"):
            continue
        if tab == "applying" and bucket != "applying":
            continue
        if tab == "interviewing" and bucket != "interviewing":
            continue
        if tab in fine_tabs and phase != tab:
            continue
        if tab == "offer" and phase != "offer":
            continue
        if tab == "rejected" and phase != "rejected":
            continue
        if tab == "stopped" and phase != "stopped":
            continue
        items.append(_serialize_progress(c))

    def sort_key(x: dict[str, Any]):
        weight = x["meta"].get("排序权重")
        try:
            weight = int(weight)
        except (TypeError, ValueError):
            weight = 3
        return (weight, x["stem"])

    items.sort(key=sort_key)
    return {"items": items, "total": len(items)}


class ProgressCreate(BaseModel):
    company: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    plan: str = "校招正式批"
    base: str = ""
    link: str = ""
    priority: str = "⚪ 观察池"


@router.post("")
def create_progress(body: ProgressCreate):
    try:
        card = vio.create_progress_manual(
            company=body.company,
            position=body.position,
            plan=body.plan,
            base=body.base,
            link=body.link,
            priority=body.priority,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _serialize_progress(card, detail=True)


@router.get("/{stem}")
def get_progress(stem: str):
    if stem in ("stats", "from-intel"):
        raise HTTPException(404, "找不到进度卡")
    card = vio.get_progress(stem)
    if not card:
        raise HTTPException(404, "找不到进度卡")
    return _serialize_progress(card, detail=True)


class ProgressPatch(BaseModel):
    updates: dict[str, Any] = Field(default_factory=dict)


@router.patch("/{stem}")
def patch_progress(stem: str, body: ProgressPatch):
    if stem in ("from-intel", "stats"):
        raise HTTPException(400, "非法 stem")
    try:
        card = vio.update_progress_fields(stem, body.updates)
    except FileNotFoundError:
        raise HTTPException(404, "找不到进度卡") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    return _serialize_progress(card, detail=True)


class ProcessReplace(BaseModel):
    stages: list[dict[str, Any]] = Field(default_factory=list)


@router.put("/{stem}/process")
def put_process(stem: str, body: ProcessReplace):
    try:
        card = vio.replace_progress_process(stem, body.stages)
    except FileNotFoundError:
        raise HTTPException(404, "找不到进度卡") from None
    return _serialize_progress(card, detail=True)


@router.delete("/{stem}")
def delete_progress(stem: str):
    try:
        dest = vio.archive_progress(stem)
    except FileNotFoundError:
        raise HTTPException(404, "找不到进度卡") from None
    return {"ok": True, "archived_to": str(dest)}


@router.post("/from-intel/{intel_stem}")
def from_intel(intel_stem: str):
    try:
        card = vio.create_progress_from_intel(intel_stem)
    except FileNotFoundError:
        raise HTTPException(404, "找不到情报卡") from None
    return _serialize_progress(card, detail=True)
