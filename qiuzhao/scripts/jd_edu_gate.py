#!/usr/bin/env python3
"""Education gate for fall-recruitment JDs.

Portrait is 硕士研究生. Jobs whose hard requirement is PhD-only must be skipped.
Master-or-PhD / 硕士及以上 / 博士优先 (master still eligible) stay.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Master's is explicitly eligible. Bare 「硕士」 in notes like 「硕士画像」 must not match.
MASTER_ALLOWED_RE = re.compile(
    r"硕士或博士|"
    r"硕士\s*/\s*博士|"
    r"博士\s*/\s*硕士|"
    r"硕士、博士|"
    r"硕士及?以上|"
    r"硕士学历|"
    r"硕士学位|"
    r"在读硕士|"
    r"本科[\/、及或]*硕士|"
    r"硕博|"
    r"学历.{0,24}硕士"
)

REQ_SPLIT_RE = re.compile(
    r"(?:任职资格|任职要求|职位要求|岗位要求|学历要求|学历背景)\s*[:：]?",
)

# Title looks like a PhD-only track (not "博士优先" on a master-open JD).
TITLE_PHD_TRACK_RE = re.compile(
    r"(?:^|[-\s_（(/])博士(?:$|[-\s_）)])|"
    r"博士生|博士专场|博士课题|博士研究员"
)

# Hard PhD floor when master's is not also listed.
PHD_HARD_RE = re.compile(
    r"获得博士(?:学位|学历)|"
    r"取得博士(?:学位|学历)|"
    r"博士及以上|"
    r"博士学历|"
    r"相关(?:方向|专业)博士|"
    r"计算机系博士|"
    r"须(?:为|是|获得)?博士|"
    r"仅限博士|"
    r"面向博士|"
    r"(?:方向|专业)博士(?:[，,。；;、\s]|$)"
)


def _requirement_blob(title: str, jd: str) -> str:
    """Prefer 任职要求; drop 备注 so collector notes cannot leak."""
    text = jd or ""
    text = re.split(r"\n\s*备注\s*[：:]", text, maxsplit=1)[0]
    parts = REQ_SPLIT_RE.split(text, maxsplit=1)
    req = parts[1] if len(parts) > 1 else text
    return f"{title or ''}\n{req}"


def is_phd_only(title: str = "", jd: str = "") -> tuple[bool, str]:
    """Return (skip, reason). skip=True means do not ingest."""
    title = title or ""
    blob = _requirement_blob(title, jd or "")
    if MASTER_ALLOWED_RE.search(blob):
        return False, "master-allowed"
    if TITLE_PHD_TRACK_RE.search(title):
        return True, "title-phd-track"
    if PHD_HARD_RE.search(blob):
        return True, "phd-hard-requirement"
    return False, "ok"


def skip_phd_only(title: str = "", jd: str = "") -> bool:
    skip, _ = is_phd_only(title, jd)
    return skip


def scan_vault() -> list[dict]:
    from vault_io import list_intel

    hits: list[dict] = []
    for card in list_intel():
        title = str(card.meta.get("岗位") or "")
        jd = str(card.meta.get("岗位简介") or "")
        skip, reason = is_phd_only(title, jd)
        if skip:
            hits.append(
                {
                    "company": card.meta.get("公司"),
                    "title": title,
                    "tier": card.meta.get("公司档次"),
                    "reason": reason,
                    "path": str(card.path),
                }
            )
    return hits


def _self_check() -> None:
    cases = [
        ("Agent开发", "硕士或博士学位", False),
        ("智能体", "硕士及以上学历，博士优先", False),
        ("研发", "本科/硕士/博士", False),
        ("HPC", "硕士/博士及以上学历", False),
        ("研究员-博士", "计算机相关专业博士学历", True),
        ("Commercial AI 博士课题", "2027届毕业，获得博士学位", True),
        ("阿里星", "相关方向博士", True),
        ("自主Agent", "博士及以上学历", True),
        ("工业垂域", "计算机系博士,且在制造算法", True),
        ("蓝极星", "2027届获得博士学历", True),
        ("Agent算法", "任职资格\n1、2027届获得博士学历\n备注：硕士画像默认观望", True),
        ("普通岗", "熟悉 Python 与 Agent", False),
    ]
    failed = 0
    for title, jd, expect in cases:
        got, reason = is_phd_only(title, jd)
        if got != expect:
            failed += 1
            print("FAIL", title, "got", got, reason, "expect", expect)
        else:
            print("OK", title, reason)
    if failed:
        raise SystemExit(f"self-check failed: {failed}")
    print("self-check passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="PhD-only education gate")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--scan-vault", action="store_true")
    parser.add_argument("--title", default="")
    parser.add_argument("--jd", default="")
    args = parser.parse_args()

    if args.self_check:
        _self_check()
        return
    if args.scan_vault:
        hits = scan_vault()
        for h in hits:
            print(f"{h['tier']}\t{h['company']}\t{h['title']}\t{h['reason']}\t{h['path']}")
        print("HITS", len(hits))
        return
    skip, reason = is_phd_only(args.title, args.jd)
    print(reason, "skip" if skip else "keep")
    raise SystemExit(1 if skip else 0)


if __name__ == "__main__":
    main()
