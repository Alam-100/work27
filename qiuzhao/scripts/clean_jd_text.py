#!/usr/bin/env python3
"""Clean scraped JD text: strip UI chrome, drop duplicate titles/meta lines."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


UI_NOISE = re.compile(
    r"^(立即投递|允许\d+个月内投递\d+个职位.*|急|收藏|分享|投递|返回|"
    r"全职|实习|兼职|算法研究|研发|技术|北京市?|上海市?|深圳市?|杭州市?|"
    r"广州市?|成都市?|\||\s*)$"
)
META_DUP = re.compile(
    r"^(全职|实习|兼职|算法研究|研发|技术类?|急|"
    r"(?:北京|上海|深圳|杭州|广州|成都|武汉|南京|苏州)(?:市)?(?:\s+(?:北京|上海|深圳|杭州|广州|成都|武汉|南京|苏州)(?:市)?)*)\s*$"
)


def collapse_duplicate_blocks(text: str) -> str:
    """If the same long block appears twice, keep the first occurrence only."""
    t = text.strip()
    if len(t) < 80:
        return t
    half = len(t) // 2
    for size in range(min(len(t) // 2, 2000), 80, -1):
        chunk = t[:size].strip()
        if not chunk:
            continue
        idx = t.find(chunk, size // 2)
        if idx > 0 and idx < len(t) * 0.7:
            # Prefer structured section start
            rest = t[idx:]
            if "【岗位" in chunk or "岗位职责" in chunk or "任职" in chunk:
                return t[:idx].rstrip()
            if rest.count("【岗位") >= chunk.count("【岗位") and len(chunk) > 200:
                return t[:idx].rstrip()
    return t


def clean_jd(raw: str, job_title: str | None = None) -> str:
    if not raw:
        return ""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines: list[str] = []
    seen_norm: set[str] = set()
    title_norm = re.sub(r"\s+", "", job_title or "")

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        # drop lone pipes / repeated meta
        if s == "|" or META_DUP.match(s) or UI_NOISE.match(s):
            continue
        norm = re.sub(r"\s+", "", s)
        if title_norm and norm == title_norm:
            continue
        # consecutive identical lines
        if lines and re.sub(r"\s+", "", lines[-1]) == norm:
            continue
        # short meta already seen
        if len(norm) <= 40 and norm in seen_norm and (
            META_DUP.match(s) or "市" in s or s in ("全职", "实习", "算法研究")
        ):
            continue
        if len(norm) <= 40:
            seen_norm.add(norm)
        lines.append(s)

    cleaned = "\n".join(lines).strip()
    cleaned = collapse_duplicate_blocks(cleaned)

    # Prefer structured section if both compact+expanded exist
    m = re.search(r"(【岗位描述】|岗位职责|工作职责)", cleaned)
    if m and m.start() > 30:
        head = cleaned[: m.start()].strip()
        # drop head if it's only title/meta repeats
        head_lines = [x for x in head.split("\n") if x.strip()]
        if len(head_lines) <= 4 or all(len(x) < 40 for x in head_lines):
            cleaned = cleaned[m.start() :].strip()

    # Drop one-line compact 【岗位描述】… when expanded numbered block follows
    compact = re.search(
        r"(【岗位描述】|【岗位要求】)[^\n]{80,}\n+",
        cleaned,
    )
    expanded = re.search(
        r"(【岗位描述】|岗位职责)\s*\n\s*1[\.、]",
        cleaned,
    )
    if compact and expanded and compact.start() < expanded.start():
        cleaned = cleaned[: compact.start()] + cleaned[expanded.start() :]
        cleaned = cleaned.strip()

    # If identical 【岗位描述】 blocks appear twice, keep first structured copy
    for marker in ("【岗位描述】", "【岗位要求】"):
        idxs = [m.start() for m in re.finditer(re.escape(marker), cleaned)]
        if len(idxs) >= 2:
            # keep from first marker to just before second occurrence of same marker
            # only when second looks like a re-dump of same section
            first, second = idxs[0], idxs[1]
            chunk1 = cleaned[first:second].strip()
            chunk2 = cleaned[second:].strip()
            # if chunk2 starts with same marker and overlaps heavily, drop chunk1 if it's denser one-liner
            if chunk1.count("\n") < 3 and chunk2.count("\n") >= 3:
                cleaned = cleaned[:first] + cleaned[second:]
            elif abs(len(chunk1) - len(re.sub(r"\s+", "", chunk2)[: len(chunk1)])) < 50 and len(chunk1) > 200:
                # near-duplicate dump: keep the more readable (more newlines)
                if chunk1.count("\n") >= chunk2.count("\n"):
                    cleaned = cleaned[:second].rstrip()
                else:
                    cleaned = cleaned[:first] + cleaned[second:]

    # Trim trailing internship card bleed / UI
    for marker in ("Stepstar实习", "立即投递", "允许3个月内投递", "投递简历", "关注腾讯招聘"):
        idx = cleaned.find(marker)
        if idx > 200:
            cleaned = cleaned[:idx].rstrip()
            break

    return cleaned.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", type=Path)
    ap.add_argument("--title", default="")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    raw = args.text_file.read_text(encoding="utf-8") if args.text_file else ""
    out = clean_jd(raw, args.title or None)
    if args.out:
        args.out.write_text(out, encoding="utf-8")
    else:
        print(json.dumps({"cleaned": out, "len": len(out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
