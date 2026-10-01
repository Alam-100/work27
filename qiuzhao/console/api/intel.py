"""Intel / jobs API."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import vault_io as vio

router = APIRouter(prefix="/intel", tags=["intel"])

_SENTINEL = object()


def _deadline_bucket(deadline: Any) -> str:
    dt = vio.parse_dt(deadline)
    if not dt:
        return "none"
    today = date.today()
    d = dt.date() if isinstance(dt, datetime) else dt
    if d < today:
        return "past"
    if d <= today + timedelta(days=7):
        return "week"
    if d.year == today.year and d.month == today.month:
        return "month"
    return "later"


def _days_left(deadline: Any) -> int | None:
    dt = vio.parse_dt(deadline)
    if not dt:
        return None
    d = dt.date() if isinstance(dt, datetime) else dt
    return (d - date.today()).days


def _parse_multi(raw: str) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def _company_channel_fields(ov_meta: dict[str, Any]) -> dict[str, Any]:
    channels = vio.company_apply_channels(ov_meta)
    primary = vio.primary_referral_channel(ov_meta)
    return {
        "apply_channels": channels,
        "referral_url": (primary or {}).get("链接") or str(ov_meta.get("内推链接") or ""),
        "referral_code": (primary or {}).get("内推码") or str(ov_meta.get("内推码") or ""),
        "delivery_record_url": vio.company_delivery_record_url(ov_meta),
    }


def _serialize_intel(
    card: vio.NoteCard,
    *,
    include_body: bool = False,
    followed_by: str | None | object = _SENTINEL,
) -> dict[str, Any]:
    # 响应侧归一化招聘状态（不强制写盘）
    meta = dict(card.meta)
    meta["公司档次"] = vio.normalize_company_tier(meta.get("公司档次"), str(meta.get("公司") or ""))
    if str(meta.get("岗位族") or "") not in vio.ROLE_FAMILIES:
        meta["岗位族"] = vio.infer_role_family(str(meta.get("岗位") or ""))
    if str(meta.get("投递优先级") or "") not in vio.APPLY_PRIORITIES:
        meta["投递优先级"] = vio.default_apply_priority(str(meta["公司档次"]))
    meta["招聘状态"] = vio.normalize_hiring_status(meta)
    view = vio.NoteCard(path=card.path, stem=card.stem, meta=meta, body=card.body)
    data = vio.note_card_to_dict(view, include_body=include_body)
    if followed_by is _SENTINEL:
        data["followed_by"] = vio.intel_follow_status(card.stem)
    else:
        data["followed_by"] = followed_by
    data["days_left"] = _days_left(meta.get("投递截止"))
    data["deadline_bucket"] = _deadline_bucket(meta.get("投递截止"))
    data["hiring_status"] = meta["招聘状态"]
    data["company_tier"] = meta["公司档次"]
    data["role_family"] = meta["岗位族"]
    data["apply_priority"] = meta["投递优先级"]
    data["archived"] = vio.is_intel_archived(card)
    return data


class IntelPatch(BaseModel):
    updates: dict[str, Any] = Field(default_factory=dict)


def _filter_intel_cards(
    *,
    q: str = "",
    plan: str = "",
    city: str = "",
    min_score: int | None = None,
    deadline: str = "",
    tier: str = "",
    role_family: str = "",
    hiring_status: str = "",
    apply_priority: str = "",
    include_archived: bool = True,
) -> list[dict[str, Any]]:
    cards = vio.list_intel(include_archived=include_archived)
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
    if city:
        cl = city.lower()

        def city_match(c: vio.NoteCard) -> bool:
            cities = c.meta.get("城市") or []
            if isinstance(cities, str):
                cities = [cities]
            return any(cl in str(x).lower() for x in cities)

        cards = [c for c in cards if city_match(c)]
    if min_score is not None:
        cards = [
            c
            for c in cards
            if isinstance(c.meta.get("匹配分"), (int, float)) and int(c.meta["匹配分"]) >= min_score
        ]
    if deadline and deadline != "all":
        cards = [c for c in cards if _deadline_bucket(c.meta.get("投递截止")) == deadline]

    follow = vio.batch_intel_follow_status([c.stem for c in cards])
    items = [
        _serialize_intel(c, followed_by=follow.get(c.stem)) for c in cards
    ]

    tiers = _parse_multi(tier)
    if tiers:
        items = [x for x in items if x.get("company_tier") in tiers]
    families = _parse_multi(role_family)
    if families:
        items = [x for x in items if x.get("role_family") in families]
    statuses = _parse_multi(hiring_status)
    if statuses:
        items = [x for x in items if x.get("hiring_status") in statuses]
    priorities = _parse_multi(apply_priority)
    if priorities:
        items = [x for x in items if x.get("apply_priority") in priorities]
    return items


def _is_closed(item: dict[str, Any]) -> bool:
    return item.get("hiring_status") == "已截止"


def _apply_scope(items: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    scope = (scope or "active").strip().lower()
    if scope == "closed":
        return [x for x in items if _is_closed(x)]
    if scope == "all":
        return items
    # active (default): 在招 = 非已截止（含招满即止 / 将截止 / 热招中 / 待核实 / 未开招）
    return [x for x in items if not _is_closed(x)]


def _score(x: dict[str, Any]) -> int:
    raw = x.get("meta", {}).get("匹配分")
    return int(raw) if isinstance(raw, (int, float)) else 0


def _sort_job_items(items: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
    if sort == "deadline_asc":

        def deadline_key(x: dict[str, Any]) -> tuple:
            dl = x.get("days_left")
            return (1 if dl is None else 0, 99999 if dl is None else dl, x["stem"])

        items.sort(key=deadline_key)
    elif sort == "deadline_then_score":
        # 有未来截止日（含今天）按剩余天数升序；同天数再按匹配分降序；
        # 无截止日的「招满即止」排在有日期之后，仍按匹配分。
        # 已过期岗（days_left < 0）放最后（closed 分区内仍按已过天数升序）。
        def composite_key(x: dict[str, Any]) -> tuple:
            dl = x.get("days_left")
            sc = _score(x)
            if dl is None:
                return (1, 0, -sc, x["stem"])
            if dl < 0:
                return (2, -dl, -sc, x["stem"])
            return (0, dl, -sc, x["stem"])

        items.sort(key=composite_key)
    else:
        items.sort(key=lambda x: (-_score(x), x["stem"]))
    return items


def _company_overview_map() -> dict[str, vio.NoteCard]:
    out: dict[str, vio.NoteCard] = {}
    for card in vio.list_intel_companies():
        name = str(card.meta.get("公司") or card.stem)
        out[name] = card
        out[card.stem] = card
    return out


def _group_by_company(
    items: list[dict[str, Any]],
    sort: str,
    *,
    scope: str = "active",
) -> list[dict[str, Any]]:
    overviews = _company_overview_map()
    buckets: dict[str, list[dict[str, Any]]] = {}
    for it in items:
        co = str(it.get("meta", {}).get("公司") or it.get("stem") or "未知")
        buckets.setdefault(co, []).append(it)

    companies: list[dict[str, Any]] = []
    for co, jobs in buckets.items():
        jobs = _sort_job_items(list(jobs), sort)
        ov = overviews.get(co)
        ov_meta = ov.meta if ov else {}
        limit_raw = ov_meta.get("投递上限")
        try:
            apply_limit = int(limit_raw) if limit_raw not in (None, "") else None
        except (TypeError, ValueError):
            apply_limit = None
        followed = sum(1 for j in jobs if j.get("followed_by"))
        # active：只看在招剩余天数；closed：显示已过天数；all：优先在招剩余
        open_days = [
            j.get("days_left")
            for j in jobs
            if j.get("days_left") is not None and j.get("days_left") >= 0
        ]
        past_days = [
            j.get("days_left")
            for j in jobs
            if j.get("days_left") is not None and j.get("days_left") < 0
        ]
        if scope == "closed":
            earliest = max(past_days) if past_days else None  # 最近过期（最接近 0）
        else:
            earliest = min(open_days) if open_days else None
        scores = [
            j.get("meta", {}).get("匹配分")
            for j in jobs
            if isinstance(j.get("meta", {}).get("匹配分"), (int, float))
        ]
        tier = (
            str(ov_meta.get("公司档次") or "")
            or (jobs[0].get("company_tier") if jobs else "")
            or "—"
        )
        companies.append(
            {
                "company": co,
                "tier": tier,
                "apply_limit": apply_limit,
                "apply_limit_note": str(ov_meta.get("投递上限说明") or ""),
                "portal": str(ov_meta.get("校招门户") or ""),
                **_company_channel_fields(ov_meta),
                "job_count": len(jobs),
                "followed_count": followed,
                "earliest_deadline": earliest,
                "max_score": max(scores) if scores else None,
                "over_limit": bool(
                    apply_limit is not None and followed >= apply_limit
                ),
                "jobs": jobs,
            }
        )

    if sort in ("deadline_asc", "deadline_then_score"):
        # active：剩余天数升序；closed：最近过期优先（earliest 已是 max(past)，取负作升序键）
        # 无统一截止靠后；deadline_then_score 再按匹配分
        def company_deadline_key(c: dict[str, Any]) -> tuple:
            ed = c["earliest_deadline"]
            score_part = -(c["max_score"] or 0) if sort == "deadline_then_score" else 0
            if ed is None:
                return (1, 0, score_part, c["company"])
            if scope == "closed":
                return (0, -ed, score_part, c["company"])  # -(-2)=2 < -(-30)=30 → 最近过期靠前
            return (0, ed, score_part, c["company"])

        companies.sort(key=company_deadline_key)
    else:
        companies.sort(
            key=lambda c: (
                -(c["max_score"] or 0),
                c["company"],
            )
        )
    return companies


@router.get("")
def list_intel(
    q: str = Query(""),
    plan: str = Query(""),
    city: str = Query(""),
    min_score: int | None = Query(None),
    deadline: str = Query(""),  # week | month | none | past | all
    tier: str = Query(""),  # 大厂 | 中厂 | 小厂 | comma multi
    role_family: str = Query(""),
    hiring_status: str = Query(""),
    apply_priority: str = Query(""),
    scope: str = Query("active"),  # active | closed | all
    sort: str = Query("deadline_then_score"),  # deadline_then_score | score_desc | deadline_asc
    group: str = Query(""),  # company | "" (flat, job pagination)
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filtered = _filter_intel_cards(
        q=q,
        plan=plan,
        city=city,
        min_score=min_score,
        deadline=deadline,
        tier=tier,
        role_family=role_family,
        hiring_status=hiring_status,
        apply_priority=apply_priority,
    )
    # stats 基于筛选后的全量（含已截止），便于 Tab 角标
    closed_count = sum(1 for x in filtered if _is_closed(x))
    hiring_count = len(filtered) - closed_count
    followed_all = sum(1 for x in filtered if x.get("followed_by"))
    urgent_open = sum(
        1
        for x in filtered
        if not _is_closed(x) and x.get("deadline_bucket") == "week"
    )

    items = _apply_scope(filtered, scope)
    items = _sort_job_items(items, sort)

    total_jobs = len(items)
    # 档次统计始终基于在招（避免切到已截止 Tab 后顶部档次数字乱跳）
    open_items = [x for x in filtered if not _is_closed(x)]
    tier_counts = {t: 0 for t in vio.COMPANY_TIERS}
    other = 0
    for x in open_items:
        t = x.get("company_tier")
        if t in tier_counts:
            tier_counts[t] += 1
        else:
            other += 1
    tier_counts["other"] = other
    stats = {
        "hiring": hiring_count,
        "closed": closed_count,
        "followed": followed_all,
        "urgent": urgent_open,
        "tiers": tier_counts,
    }

    if group == "company":
        companies = _group_by_company(items, sort, scope=scope)
        total_companies = len(companies)
        pages = max(1, (total_companies + page_size - 1) // page_size) if total_companies else 1
        page = min(page, pages)
        start = (page - 1) * page_size
        page_companies = companies[start : start + page_size]
        flat_items = [j for c in page_companies for j in c["jobs"]]
        return {
            "group": "company",
            "page_unit": "company",
            "companies": page_companies,
            "items": flat_items,
            "total": total_jobs,
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "page": page,
            "page_size": page_size,
            "pages": pages,
            "stats": stats,
            "sort": sort,
            "scope": scope or "active",
        }

    pages = max(1, (total_jobs + page_size - 1) // page_size) if total_jobs else 1
    page = min(page, pages)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    return {
        "group": "",
        "page_unit": "job",
        "companies": [],
        "items": page_items,
        "total": total_jobs,
        "total_jobs": total_jobs,
        "total_companies": len({str(x.get("meta", {}).get("公司") or "") for x in items}),
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "stats": stats,
        "sort": sort,
        "scope": scope or "active",
    }


@router.get("/{stem}")
def get_intel(stem: str):
    card = vio.get_intel(stem)
    if not card:
        raise HTTPException(404, "找不到情报卡")
    data = _serialize_intel(card, include_body=True)
    company = str(card.meta.get("公司") or "")
    bank = vio.get_question_bank(company) if company else None
    data["question_bank"] = (
        {
            "stem": bank.stem,
            "rel": bank.rel,
            "meta": vio._jsonable_meta(bank.meta),
            "groups": vio.parse_question_bank_groups(bank.body),
        }
        if bank
        else None
    )
    ov = vio.get_intel_company(company) if company else None
    if ov:
        limit_raw = ov.meta.get("投递上限")
        try:
            apply_limit = int(limit_raw) if limit_raw not in (None, "") else None
        except (TypeError, ValueError):
            apply_limit = None
        followed = sum(
            1
            for c in vio.list_progress()
            if str(c.meta.get("公司") or "") == company
            and str(c.meta.get("投递状态") or "") not in ("弃投", "已拒")
        )
        data["company_overview"] = {
            "company": company,
            "apply_limit": apply_limit,
            "apply_limit_note": str(ov.meta.get("投递上限说明") or ""),
            "portal": str(ov.meta.get("校招门户") or ""),
            **_company_channel_fields(ov.meta),
            "followed_count": followed,
            "over_limit": bool(apply_limit is not None and followed >= apply_limit),
        }
    else:
        data["company_overview"] = None
    return data


@router.patch("/{stem}")
def patch_intel(stem: str, body: IntelPatch):
    try:
        card = vio.update_intel_fields(stem, body.updates or {})
    except FileNotFoundError:
        raise HTTPException(404, "找不到情报卡") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _serialize_intel(card, include_body=True)


@router.post("/{stem}/follow")
def follow_intel(stem: str):
    intel = vio.get_intel(stem)
    if not intel:
        raise HTTPException(404, "找不到情报卡")
    company = str(intel.meta.get("公司") or "")
    apply_limit = vio.company_apply_limit(company) if company else None
    followed = sum(
        1
        for c in vio.list_progress()
        if str(c.meta.get("公司") or "") == company
        and str(c.meta.get("投递状态") or "") not in ("弃投", "已拒")
    )
    warning = None
    if apply_limit is not None and followed >= apply_limit:
        warning = (
            f"该公司官网核实投递上限为 {apply_limit}，当前已跟进 {followed} 个岗位；"
            "仍可加入投递，但请确认是否超限。"
        )
    try:
        card = vio.create_progress_from_intel(stem)
    except FileNotFoundError:
        raise HTTPException(404, "找不到情报卡") from None
    return {
        "ok": True,
        "progress_stem": card.stem,
        "meta": vio._jsonable_meta(card.meta),
        "apply_limit_warning": warning,
        "apply_limit": apply_limit,
        "followed_before": followed,
    }


@router.post("/{stem}/verify")
def verify_intel(stem: str):
    intel = vio.get_intel(stem)
    if not intel:
        raise HTTPException(404, "找不到情报卡")
    company = str(intel.meta.get("公司") or stem)
    job = vio.append_agent_job("收集公司", f"核实:{company}|{stem}")
    return {"ok": True, "job_id": job.id, "message": "已入队核实，请在 Cursor 说：处理控制台任务"}
