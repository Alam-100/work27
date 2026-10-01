"""Interview review API."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import vault_io as vio

router = APIRouter(prefix="/review", tags=["review"])


def _serialize_review(card: vio.NoteCard, *, include_body: bool = False) -> dict[str, Any]:
    data = vio.note_card_to_dict(card, include_body=include_body)
    data["status"] = vio.infer_mianshi_status(card)
    data["intel_stem"] = vio._wikilink_stem(card.meta.get("关联情报"))
    data["progress_stem"] = vio._wikilink_stem(card.meta.get("关联进度"))
    if include_body:
        data["questions"] = _parse_review_questions(card.body)
        data["reflection"] = _extract_section(card.body, "反思")
        data["next_actions"] = _extract_section(card.body, "下次改进")
    return data


_KIND_OK = {"面试", "手撕"}


def _normalize_kind(raw: str) -> str:
    text = (raw or "").strip()
    if text in _KIND_OK:
        return text
    if "手撕" in text or "算法" in text or "coding" in text.lower():
        return "手撕"
    return "面试"


def _parse_review_questions(body: str) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    in_table = False
    has_kind = False
    for line in (body or "").splitlines():
        s = line.strip()
        if s.startswith("|") and "问题" in s and ("掌握" in s or "掌握度" in s):
            in_table = True
            headers = [p.strip() for p in s.strip("|").split("|")]
            has_kind = bool(headers) and headers[0] in ("类型", "题型")
            continue
        if in_table:
            if not s.startswith("|"):
                in_table = False
                continue
            parts = [p.strip() for p in s.strip("|").split("|")]
            if len(parts) < 1 or parts[0].startswith("---"):
                continue
            if has_kind:
                kind = _normalize_kind(parts[0] if parts else "面试")
                text = parts[1] if len(parts) > 1 else ""
                answer = parts[2] if len(parts) > 2 else ""
                ref = parts[3] if len(parts) > 3 else ""
                mastery = parts[4] if len(parts) > 4 else ""
            else:
                kind = "面试"
                text = parts[0]
                answer = parts[1] if len(parts) > 1 else ""
                ref = parts[2] if len(parts) > 2 else ""
                mastery = parts[3] if len(parts) > 3 else ""
            if not text:
                continue
            questions.append(
                {
                    "kind": kind,
                    "text": text,
                    "answer": answer,
                    "ref": ref,
                    "mastery": mastery,
                }
            )
    if questions:
        return questions
    collecting = False
    for line in (body or "").splitlines():
        s = line.strip()
        if s.startswith("##") and "问题" in s:
            collecting = True
            continue
        if collecting and s.startswith("##"):
            break
        m = re.match(r"^(\d+)[\.\)、]\s*(.+)$", s)
        if collecting and m:
            questions.append(
                {"kind": "面试", "text": m.group(2).strip(), "answer": "", "ref": "", "mastery": ""}
            )
        elif collecting and s.startswith("- "):
            questions.append(
                {"kind": "面试", "text": s[2:].strip(), "answer": "", "ref": "", "mastery": ""}
            )
    return questions


def _extract_section(body: str, title: str) -> str:
    pattern = rf"##\s*{re.escape(title)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, body or "", re.S)
    return (m.group(1).strip() if m else "")


def _rebuild_body(
    card: vio.NoteCard,
    *,
    questions: list[dict[str, str]] | None = None,
    reflection: str | None = None,
    next_actions: str | None = None,
    body: str | None = None,
) -> str:
    if body is not None:
        return body
    original = card.body or ""
    company = str(card.meta.get("公司") or card.stem)
    # Keep header / 关联 / 历史资料 sections if present
    header_end = original.find("## 问题清单")
    if header_end < 0:
        header_end = original.find("## 复盘")
    if header_end < 0:
        header = f"# {company} · 面经与复盘\n\n"
    else:
        header = original[:header_end]

    qs = questions if questions is not None else _parse_review_questions(original)
    refl = reflection if reflection is not None else _extract_section(original, "反思")
    nxt = next_actions if next_actions is not None else _extract_section(original, "下次改进")

    lines = [header.rstrip() + "\n\n", "## 问题清单\n"]
    lines.append("| 类型 | 问题 | 我的回答要点 | 参考/标准答 | 掌握度 |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")
    for q in qs:
        kind = _normalize_kind(str(q.get("kind") or "面试"))
        text = (q.get("text") or "").replace("|", "\\|")
        answer = (q.get("answer") or "").replace("|", "\\|")
        ref = (q.get("ref") or "").replace("|", "\\|")
        mastery = (q.get("mastery") or "").replace("|", "\\|")
        lines.append(f"| {kind} | {text} | {answer} | {ref} | {mastery} |\n")
    lines.append("\n## 反思\n")
    lines.append((refl or "- 答得好的：\n- 卡住的点：\n- 知识盲区：") + "\n")
    lines.append("\n## 下次改进\n")
    lines.append((nxt or "- [ ] ") + "\n")
    return "".join(lines)


@router.get("")
def list_reviews(q: str = ""):
    cards = vio.list_mianshi()
    if q:
        ql = q.lower()
        cards = [
            c
            for c in cards
            if ql in str(c.meta.get("公司", "")).lower()
            or ql in str(c.meta.get("岗位", "")).lower()
            or ql in c.stem.lower()
        ]
    items = [_serialize_review(c) for c in cards]
    return {"items": items, "total": len(items)}


@router.get("/coding-list")
def coding_list(company: str = ""):
    data = vio.get_coding_checklist()
    groups = data.get("groups") or []
    if company.strip():
        needle = company.strip()
        filtered = []
        for g in groups:
            items = [
                it
                for it in g.get("items") or []
                if any(needle in str(src) for src in (it.get("sources") or []))
            ]
            if items:
                filtered.append({"topic": g.get("topic"), "items": items})
        data = {**data, "groups": filtered, "company": needle}
    return data


@router.get("/{stem}")
def get_review(stem: str):
    card = vio.get_mianshi(stem)
    if not card:
        raise HTTPException(404, "找不到面经复盘")
    return _serialize_review(card, include_body=True)


@router.get("/{stem}/bank")
def get_review_bank(stem: str):
    card = vio.get_mianshi(stem)
    if not card:
        raise HTTPException(404, "找不到面经复盘")
    company = str(card.meta.get("公司") or "")
    bank = vio.get_question_bank(company) if company else None
    if not bank:
        return {"stem": None, "groups": [], "meta": {}}
    return {
        "stem": bank.stem,
        "rel": bank.rel,
        "meta": vio._jsonable_meta(bank.meta),
        "groups": vio.parse_question_bank_groups(bank.body),
        "body": bank.body,
    }


class ReviewPatch(BaseModel):
    body: str | None = None
    questions: list[dict[str, str]] | None = None
    reflection: str | None = None
    next_actions: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


@router.patch("/{stem}")
def patch_review(stem: str, payload: ReviewPatch):
    card = vio.get_mianshi(stem)
    if not card:
        raise HTTPException(404, "找不到面经复盘")
    new_body = _rebuild_body(
        card,
        questions=payload.questions,
        reflection=payload.reflection,
        next_actions=payload.next_actions,
        body=payload.body,
    )
    updated = vio.update_mianshi_fields(
        stem,
        body=new_body,
        meta_updates=payload.meta or None,
    )
    return _serialize_review(updated, include_body=True)
