#!/usr/bin/env python3
"""Job-card apply URL quality: list shells vs job permalinks.

Zhiye / Beisen white-label SPAs (vivo ``hr-campus``, ``*.zhiye.com``, etc.):

- ``/campus/jobs?jobAdId=<uuid>`` is the **list shell**; many sites ignore jobAdId
  and every job card appears to open the same page.
- ``/campus/detail?jobAdId=<uuid>`` is the **JD permalink**.

Job cards MUST store a permalink. Company overview ``投递渠道`` MAY store the
list / referral URL (``shareId``, ``recommendCode``).
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

JOB_ID_KEYS = (
    "jobAdId",
    "advertisementId",
    "postid",
    "jobUnionId",
    "jobId",
    "positionId",
    "postId",
    "postID",
)

WEIXIN_RE = re.compile(r"mp\.weixin\.qq\.com|weixin://|wxaurl", re.I)
SHORTENER_RE = re.compile(
    r"(?:^|\.)(?:dwz\.cn|dqr\.cn|url\.cn|t\.cn|bit\.ly|tinyurl\.com)/",
    re.I,
)
REFERRAL_KEYS = (
    "recommendCode",
    "campusShareCode",
    "shareId",
    "referralCode",
    "referer_code",
    "blNtCode",
    "code",
    "pushCode",
    "staffSsoId",
)


def _split(url: str) -> tuple[str, str, str, dict[str, list[str]], str]:
    raw = (url or "").strip()
    parts = urlsplit(raw)
    query = parse_qs(parts.query, keep_blank_values=True)
    return raw, parts.scheme, parts.path, query, parts.fragment


def job_id_from_url(url: str) -> tuple[str, str]:
    """Return (key, value) of the first job-id query param, else ('', '')."""
    _, _, _, query, fragment = _split(url)
    blob_pairs: list[tuple[str, list[str]]] = list(query.items())
    if fragment and "=" in fragment:
        frag_q = fragment.split("?", 1)[-1] if "?" in fragment else fragment
        # hash routes like #/campus/jobs?code=...
        if "=" in frag_q:
            from urllib.parse import parse_qs as _pq

            extra = frag_q.split("?", 1)[-1] if frag_q.startswith("/") else frag_q
            blob_pairs.extend(_pq(extra, keep_blank_values=True).items())
    lower = {k.lower(): (k, v) for k, v in blob_pairs}
    for key in JOB_ID_KEYS:
        hit = lower.get(key.lower())
        if hit and hit[1] and hit[1][0].strip():
            return hit[0], hit[1][0].strip()
    return "", ""


def is_weixin_url(url: str) -> bool:
    return bool(url and WEIXIN_RE.search(url))


def is_shortener(url: str) -> bool:
    host = urlsplit(url or "").netloc.lower()
    return bool(SHORTENER_RE.search(host) or SHORTENER_RE.search(url or ""))


def has_referral_token(url: str, code: str = "") -> bool:
    if (code or "").strip():
        return True
    _, _, _, query, fragment = _split(url)
    keys = {k.lower() for k in query}
    blob = f"{url} {fragment}"
    for k in REFERRAL_KEYS:
        if k.lower() in keys:
            return True
        if k.lower() in blob_lower(blob):
            return True
    return False


def blob_lower(s: str) -> str:
    return (s or "").lower()


def path_is_job_list(path: str) -> bool:
    p = (path or "").rstrip("/")
    return p.endswith("/jobs") or p.endswith("/position") or p.endswith("/campus")


def classify_apply_url(url: str) -> dict[str, str]:
    raw = (url or "").strip()
    if not raw:
        return {"url": "", "kind": "empty", "reason": "空链接"}
    if is_weixin_url(raw):
        return {"url": raw, "kind": "weixin", "reason": "微信墙"}
    parts = urlsplit(raw)
    path = parts.path or ""
    jkey, jid = job_id_from_url(raw)
    if jkey and jid and path.rstrip("/").endswith("/detail"):
        return {"url": raw, "kind": "permalink", "reason": f"{jkey} 详情页"}
    if jkey and jid and path_is_job_list(path) and not parts.fragment.startswith("/"):
        return {
            "url": raw,
            "kind": "list_with_id",
            "reason": f"列表壳带 {jkey}，站点常忽略，岗卡点进去都一样",
        }
    if jkey and jid:
        return {"url": raw, "kind": "permalink", "reason": f"含 {jkey}"}
    if path_is_job_list(path) or path.rstrip("/").endswith("/grad"):
        return {"url": raw, "kind": "generic_list", "reason": "校招列表/门户，不是单岗"}
    return {"url": raw, "kind": "unknown", "reason": "未识别为单岗 permalink"}


def rewrite_job_apply_url(url: str) -> tuple[str, str]:
    """Rewrite Zhiye-style list+jobAdId to /detail permalink. Else unchanged."""
    raw = (url or "").strip()
    if not raw:
        return raw, "empty"
    info = classify_apply_url(raw)
    if info["kind"] != "list_with_id":
        return raw, info["kind"]
    parts = urlsplit(raw)
    path = (parts.path or "").rstrip("/")
    if not path.endswith("/jobs"):
        return raw, info["kind"]
    new_path = path[: -len("/jobs")] + "/detail"
    query = parse_qs(parts.query, keep_blank_values=True)
    # Job card permalink: keep jobAdId only (referral belongs on _公司.md)
    jkey, jid = job_id_from_url(raw)
    new_query = urlencode({jkey: jid}) if jkey and jid else parts.query
    new = urlunsplit((parts.scheme, parts.netloc, new_path, new_query, ""))
    return new, "rewritten_zhiye_detail"


def channel_score(url: str, code: str = "") -> int:
    """Higher = more useful as a company-level apply/referral entry."""
    raw = (url or "").strip()
    score = 0
    if not raw and not code:
        return 0
    if code:
        score += 3
    if raw.startswith("https://"):
        score += 2
    elif raw.startswith("http://"):
        score += 1
    if is_weixin_url(raw):
        return -10
    if is_shortener(raw):
        score -= 4
    if has_referral_token(raw, code):
        score += 4
    info = classify_apply_url(raw)
    if info["kind"] == "permalink":
        score += 2  # rare on group chats; still a valid entry
    if info["kind"] == "list_with_id":
        score += 1
    if info["kind"] == "generic_list" and has_referral_token(raw, code):
        score += 3  # attributed list is what we want on _公司.md
    return score
