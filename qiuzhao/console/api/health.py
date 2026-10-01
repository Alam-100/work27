"""Health / enums endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, Query

import vault_io as vio

router = APIRouter(tags=["health"])


def _enums() -> dict:
    return {
        "statuses": vio.PROGRESS_STATUSES,
        "priorities": vio.PRIORITIES,
        "results": vio.RESULTS,
        "plans": vio.PLANS,
        "company_tiers": vio.COMPANY_TIERS,
        "role_families": vio.ROLE_FAMILIES,
        "hiring_statuses": vio.HIRING_STATUSES,
        "apply_priorities": vio.APPLY_PRIORITIES,
        "study_types": vio.STUDY_TYPES,
        "study_statuses": vio.STUDY_STATUSES,
        "agent_intents": vio.AGENT_INTENTS,
        "agent_statuses": vio.AGENT_STATUSES,
        "campus_event_types": vio.CAMPUS_EVENT_TYPES,
        "campus_event_forms": vio.CAMPUS_EVENT_FORMS,
        "campus_event_statuses": vio.CAMPUS_EVENT_STATUSES,
    }


@router.get("/enums")
def api_enums():
    """Static enum lists — no vault scan."""
    return {"enums": _enums()}


@router.get("/health")
def api_health(light: bool = Query(True, description="Skip full vault counts (default)")):
    report = vio.health_check(light=light)
    return {
        "vault": report.vault,
        "qiuzhao_ok": report.qiuzhao_ok,
        "progress_count": report.progress_count,
        "intel_count": report.intel_count,
        "study_count": report.study_count,
        "mianshi_count": report.mianshi_count,
        "pending_jobs": report.pending_jobs,
        "messages": report.messages,
        "env_vault": os.environ.get("QIUZHAO_VAULT", ""),
        "light": light,
        "enums": _enums(),
    }
