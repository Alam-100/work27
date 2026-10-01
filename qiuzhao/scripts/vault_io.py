#!/usr/bin/env python3
"""Shared Obsidian vault IO for qiuzhao console + Agent skill helpers.

Truth source: Markdown notes under 秋招/ (QIUZHAO_VAULT).
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install PyYAML") from exc

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

PROGRESS_STATUSES = [
    "待投",
    "待测评",
    "待笔试",
    "待面试-一面",
    "待面试-二面",
    "待面试-三面",
    "待面试-HR面",
    "等结果",
    "Offer",
    "已拒",
    "弃投",
]

PRIORITIES = ["🔴 明星攻坚", "🟡 重点储备", "🟠 机会窗口", "⚪ 观察池"]
RESULTS = ["进行中", "Offer", "已拒", "待定"]
PLANS = ["校招正式批", "校招提前批", "人才计划", "实习", "其他"]
COMPANY_TIERS = ["大厂", "中厂", "小厂", "央国企", "外企"]
ROLE_FAMILIES = ["Agent", "算法", "研发应用", "后端", "前端", "其他"]
HIRING_STATUSES = ["热招中", "将截止", "已截止", "未开招", "待核实"]
APPLY_PRIORITIES = ["练手优先", "冲刺", "保底", "观望"]
INTEL_EDITABLE = [
    "公司",
    "岗位",
    "公司档次",
    "岗位族",
    "招聘状态",
    "投递优先级",
    "招聘计划",
    "城市",
    "匹配分",
    "投递链接",
    "岗位简介",
    "开放日",
    "投递截止",
    "信息时效",
    "需再核实",
]
STUDY_TYPES = ["面经", "手撕", "知识"]
STUDY_STATUSES = ["待做", "进行中", "完成"]
AGENT_INTENTS = [
    "链接入库",
    "收集公司",
    "每日情报更新",
    "面经图片",
    "跟进投递",
    "宣讲会更新",
    "宣讲会补录",
]
AGENT_STATUSES = ["待处理", "处理中", "完成", "失败"]

CAMPUS_EVENT_TYPES = ["宣讲会", "双选会", "组团招聘"]
CAMPUS_EVENT_FORMS = ["北校线下", "南校线下", "线上"]
CAMPUS_EVENT_STATUSES = ["未开始", "进行中", "已举办", "已取消"]
CAMPUS_EVENT_SOURCES = ["就业网", "公众号"]

# qiuzhao/scripts → qiuzhao/data/company_tiers.json
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_COMPANY_TIERS_CACHE: dict[str, Any] | None = None

EVENT_FIELDS = (
    ("测评时间", "测评"),
    ("笔试时间", "笔试"),
    ("一面", "一面"),
    ("二面", "二面"),
    ("三面", "三面"),
    ("HR面", "HR面"),
)

PROGRESS_EDITABLE = [
    "公司",
    "岗位",
    "投递状态",
    "优先级",
    "结果",
    "招聘计划",
    "Base地",
    "投递时间",
    "测评时间",
    "笔试时间",
    "一面",
    "二面",
    "三面",
    "HR面",
    "内推人",
    "内推码",
    "投递链接",
    "投递记录查询",
    "备注",
    "排序权重",
    "流程",
]

KNOWN_STAGE_FIELDS = {
    "投递时间",
    "测评时间",
    "笔试时间",
    "一面",
    "二面",
    "三面",
    "HR面",
}

STAGE_TYPE_BY_FIELD = {
    "投递时间": "投递",
    "测评时间": "测评",
    "笔试时间": "笔试",
    "一面": "面试",
    "二面": "面试",
    "三面": "面试",
    "HR面": "面试",
}

TIME_KINDS = ("开始", "截止", "安排")


def default_time_kind_for_type(stype: str) -> str:
    """Infer time semantics from stage type: 笔试/测评→截止, 面试→开始."""
    t = str(stype or "").strip()
    if t in ("笔试", "测评"):
        return "截止"
    if t == "面试":
        return "开始"
    return "安排"


def normalize_time_kind(raw: Any, stype: str = "") -> str:
    kind = str(raw or "").strip()
    if kind in TIME_KINDS:
        return kind
    return default_time_kind_for_type(stype)


DEFAULT_PROCESS_TEMPLATE: list[dict[str, Any]] = [
    {
        "id": "apply",
        "label": "投递",
        "type": "投递",
        "field": "投递时间",
        "time_kind": "安排",
    },
    {
        "id": "assessment",
        "label": "测评",
        "type": "测评",
        "field": "测评时间",
        "time_kind": "截止",
    },
    {
        "id": "written",
        "label": "笔试",
        "type": "笔试",
        "field": "笔试时间",
        "time_kind": "截止",
    },
    {
        "id": "r1",
        "label": "一面",
        "type": "面试",
        "field": "一面",
        "time_kind": "开始",
    },
    {
        "id": "r2",
        "label": "二面",
        "type": "面试",
        "field": "二面",
        "time_kind": "开始",
    },
    {
        "id": "r3",
        "label": "三面",
        "type": "面试",
        "field": "三面",
        "time_kind": "开始",
    },
    {
        "id": "hr",
        "label": "HR面",
        "type": "面试",
        "field": "HR面",
        "time_kind": "开始",
    },
    {
        "id": "offer",
        "label": "Offer",
        "type": "Offer",
        "field": None,
        "time_kind": "安排",
    },
]


DEFAULT_VAULT = (
    Path.home()
    / "Documents"
    / "ObsidianRecovery"
    / "my-obsidian-20260921"
    / "My_docs"
)


def vault_root() -> Path:
    return Path(os.environ.get("QIUZHAO_VAULT", str(DEFAULT_VAULT)))


def qiuzhao_root(root: Path | None = None) -> Path:
    return (root or vault_root()) / "秋招"


def progress_dir(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "05_投递进度"


def intel_dir(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "02_情报库"


INTEL_ARCHIVE_DIRNAME = "_归档"


def intel_archive_dir(root: Path | None = None) -> Path:
    """Closed job cards live under 02_情报库/_归档/{公司}/ — kept, not deleted."""
    return intel_dir(root) / INTEL_ARCHIVE_DIRNAME


def _is_under_intel_archive(path: Path, root: Path | None = None) -> bool:
    try:
        rel = path.resolve().relative_to(intel_dir(root).resolve())
    except ValueError:
        return False
    return INTEL_ARCHIVE_DIRNAME in rel.parts


def study_dir(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "07_任务" / "学习"


def agent_queue_path(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "07_任务" / "agent队列.md"


def mianshi_dir(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "03_面经"


def knowledge_bank_dir(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "06_知识库" / "公司面经摘录"


def profile_path(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "00_画像" / "求职画像.md"


def campus_events_dir(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "10_校园活动"


def campus_events_inbox_path(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "04_情报" / "宣讲会收件箱.md"


STAGE_DEFS = (
    ("测评时间", "测评"),
    ("笔试时间", "笔试"),
    ("一面", "一面"),
    ("二面", "二面"),
    ("三面", "三面"),
    ("HR面", "HR面"),
    ("Offer", "Offer"),
)

STATUS_TO_STAGE = {
    "待投": None,
    "待测评": "测评",
    "待笔试": "笔试",
    "待面试-一面": "一面",
    "待面试-二面": "二面",
    "待面试-三面": "三面",
    "待面试-HR面": "HR面",
    "等结果": "HR面",
    "Offer": "Offer",
    "已拒": None,
    "弃投": None,
}


def today_str() -> str:
    return date.today().isoformat()


def parse_note(text: str) -> tuple[dict[str, Any], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, m.group(2) or ""


def dump_note(meta: dict[str, Any], body: str) -> str:
    # Keep Chinese keys readable; allow unicode + no sorting churn
    dumped = yaml.safe_dump(
        meta,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    ).rstrip()
    body = body.lstrip("\n")
    if body and not body.endswith("\n"):
        body += "\n"
    return f"---\n{dumped}\n---\n{body}"


def _looks_like_note_text(text: str) -> bool:
    head = (text or "").lstrip()[:400]
    if not head:
        return False
    if head.startswith("---") or head.startswith("#"):
        return True
    # YAML-less notes still usually have a markdown heading later
    if "\n# " in ("\n" + head):
        return True
    return False


def _decode_note_text(raw: bytes) -> str:
    """Decode note bytes as UTF-8; fall back for legacy UTF-16/GBK PowerShell dumps.

    Binary / unknown blobs (same magic header across many vault files) must NOT
    be silently accepted — raise UnicodeDecodeError so callers can skip.
    """
    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
        if _looks_like_note_text(text):
            return text
        raise UnicodeDecodeError("utf-8", raw, 0, 1, "utf-8-sig but not a note")
    if raw.startswith(b"\xff\xfe"):
        text = raw.decode("utf-16-le")
        if _looks_like_note_text(text):
            return text
        raise UnicodeDecodeError("utf-16-le", raw, 0, 1, "utf-16-le but not a note")
    if raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16-be")
        if _looks_like_note_text(text):
            return text
        raise UnicodeDecodeError("utf-16-be", raw, 0, 1, "utf-16-be but not a note")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        for enc in ("utf-16-le", "utf-16", "gb18030"):
            try:
                text = raw.decode(enc)
            except UnicodeDecodeError:
                continue
            if _looks_like_note_text(text):
                return text
        raise e


def read_note(path: Path) -> tuple[dict[str, Any], str]:
    text = _decode_note_text(path.read_bytes())
    return parse_note(text)


def try_read_note(path: Path) -> tuple[dict[str, Any], str] | None:
    """Read a note; return None on missing/corrupt/non-UTF8 (do not raise)."""
    if not path.is_file():
        return None
    try:
        return read_note(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None


def quarantine_corrupt_note(path: Path) -> Path | None:
    """Rename unreadable note to ``*.md.badenc`` so callers can recreate.

    Returns the quarantine path on success, or None if the file was removed / missing.
    """
    if not path.is_file():
        return None
    bad = path.with_suffix(path.suffix + ".badenc")
    try:
        if bad.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            bad = path.with_suffix(f"{path.suffix}.badenc.{stamp}")
        path.replace(bad)
        return bad
    except OSError:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def write_note(path: Path, meta: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_note(meta, body), encoding="utf-8", newline="\n")


_H2_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.M)

# Only these H2s split an intel-job note. JD text may contain `## 加分项` etc.
INTEL_STRUCTURAL_H2 = {
    "投递入口",
    "岗位简介",
    "匹配分析",
    "匹配说明",
    "待核实项",
    "关联进度",
    "备注",
}


def _iter_structural_h2(body: str):
    for m in _H2_RE.finditer(body or ""):
        if m.group(1).strip() in INTEL_STRUCTURAL_H2:
            yield m


def extract_h2_section(body: str, heading: str) -> str | None:
    """Return text under a structural H2 (without the heading), or None if missing."""
    text = body or ""
    matches = list(_iter_structural_h2(text))
    for i, m in enumerate(matches):
        if m.group(1).strip() != heading:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        return text[start:end]
    return None


def upsert_h2_section(
    body: str,
    heading: str,
    content: str,
    *,
    after: str | None = "投递入口",
) -> str:
    """Insert or replace a structural `## heading` block. Default insert after 投递入口."""
    text = body or ""
    content = (content or "").strip()
    if not content:
        return text
    block = f"## {heading}\n{content}\n"
    matches = list(_iter_structural_h2(text))
    for i, m in enumerate(matches):
        if m.group(1).strip() != heading:
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        before = text[:start].rstrip() + "\n\n"
        rest = text[end:].lstrip("\n")
        return before + block + ("\n" + rest if rest else "")
    if after:
        for i, m in enumerate(matches):
            if m.group(1).strip() != after:
                continue
            insert_at = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            before = text[:insert_at].rstrip() + "\n\n"
            rest = text[insert_at:].lstrip("\n")
            return before + block + ("\n" + rest if rest else "")
    return text.rstrip() + "\n\n" + block


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def sanitize_jd_for_body(jd: str) -> str:
    """Demote ATX headings inside JD so they do not split the note."""

    def _repl(m: re.Match[str]) -> str:
        return f"**{m.group(1).strip()}**"

    return re.sub(r"^#{2,6}[ \t]+(.+?)[ \t]*$", _repl, jd or "", flags=re.M)


def sync_intel_job_body_jd(body: str, jd: str) -> tuple[str, bool]:
    """Copy frontmatter 岗位简介 into readable `## 岗位简介`.

    Obsidian reading view hides YAML properties, so JD must also live in the
    markdown body. Frontmatter remains the machine SSOT (console / Dataview).
    """
    jd = sanitize_jd_for_body((jd or "").strip())
    if not jd:
        return body or "", False
    existing = extract_h2_section(body or "", "岗位简介")
    if existing is not None and _norm_ws(existing) == _norm_ws(jd):
        return body or "", False
    new_body = upsert_h2_section(body or "", "岗位简介", jd, after="投递入口")
    return new_body, new_body != (body or "")


def replace_note_body(path: Path, body: str) -> None:
    """Rewrite markdown body while keeping original frontmatter bytes."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"no frontmatter: {path}")
    body = (body or "").lstrip("\n")
    if body and not body.endswith("\n"):
        body += "\n"
    path.write_text(f"---\n{m.group(1)}\n---\n{body}", encoding="utf-8", newline="\n")


def default_intel_job_body(
    *,
    company: str,
    heading: str,
    apply_url: str,
    portal_url: str = "",
    jd: str = "",
    why: str = "",
    gap: str = "",
    limit_note: str = "",
    extra_checks: list[str] | None = None,
) -> str:
    """Canonical intel-job markdown body. Always includes `## 岗位简介`."""
    _scripts = Path(__file__).resolve().parent
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
    from job_apply_url import rewrite_job_apply_url  # noqa: WPS433

    apply_url, _ = rewrite_job_apply_url(apply_url or "")
    portal = portal_url.strip()
    checks = ["投递截止（官网未给出明确日期，禁止编造）"] + list(extra_checks or [])
    check_lines = "\n".join(f"- [ ] {c}" for c in checks)
    portal_line = f"- **校招门户**：[打开]({portal})\n" if portal else ""
    intro = sanitize_jd_for_body((jd or "").strip()) or "（待从官网详情抽出实质 JD）"
    why_line = why or "见岗位简介"
    gap_line = gap or "待对照画像"
    limit_line = limit_note or "以 `_公司.md` 为准；官网未明示则留空"
    return (
        f"# {heading}\n\n"
        f"[[秋招/02_情报库/{company}/_公司|{company}]] · [[秋招/04_情报/候选池|候选池]]\n\n"
        f"## 投递入口\n"
        f"- **岗位详情**：[打开]({apply_url})\n"
        f"{portal_line}"
        f"- **公司概况**：[[秋招/02_情报库/{company}/_公司|限投见公司页]]\n\n"
        f"## 岗位简介\n"
        f"{intro}\n\n"
        f"## 匹配分析\n"
        f"- 匹配理由：{why_line}\n"
        f"- 缺口：{gap_line}\n"
        f"- 限投：{limit_line}\n\n"
        f"## 待核实项\n"
        f"{check_lines}\n\n"
        f"## 关联进度\n"
        f"（用户确认「加入投递表」后由助手创建）\n"
    )


def parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime(value.year, value.month, value.day)
    s = str(value).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            chunk = s[:19] if "T" in s and len(s) > 19 else s
            return datetime.strptime(chunk, fmt)
        except ValueError:
            continue
    return None


def fmt_dt(value: Any) -> str:
    dt = parse_dt(value)
    if not dt:
        return ""
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M")


@dataclass
class NoteCard:
    path: Path
    stem: str
    meta: dict[str, Any]
    body: str = ""

    @property
    def rel(self) -> str:
        try:
            return self.path.relative_to(vault_root()).as_posix()
        except ValueError:
            return self.path.as_posix()


def _list_typed(
    directory: Path,
    type_name: str,
    *,
    recursive: bool = False,
    include_archived: bool = False,
) -> list[NoteCard]:
    try:
        directory_ok = directory.is_dir()
    except OSError:
        return []
    if not directory_ok:
        return []
    cards: list[NoteCard] = []
    paths = directory.rglob("*.md") if recursive else directory.glob("*.md")
    archive_name = INTEL_ARCHIVE_DIRNAME
    for path in sorted(paths):
        if path.name.startswith("_"):
            continue
        if recursive and not include_archived and archive_name in path.parts:
            continue
        try:
            meta, body = read_note(path)
        except (UnicodeDecodeError, OSError, ValueError):
            continue
        if meta.get("type") != type_name:
            continue
        cards.append(NoteCard(path=path, stem=path.stem, meta=meta, body=body))
    return cards


def list_progress(root: Path | None = None) -> list[NoteCard]:
    return _list_typed(progress_dir(root), "qiuzhao-progress")


def list_intel(
    root: Path | None = None,
    *,
    include_archived: bool = False,
) -> list[NoteCard]:
    """List job intel cards under 02_情报库 (supports company subfolders).

    By default skips ``_归档/`` so closed cards no longer occupy active inventory.
    Pass ``include_archived=True`` for closed-tab / full scans.
    """
    return _list_typed(
        intel_dir(root),
        "qiuzhao-intel-job",
        recursive=True,
        include_archived=include_archived,
    )


def list_study(root: Path | None = None) -> list[NoteCard]:
    return _list_typed(study_dir(root), "qiuzhao-study-task")


def get_progress(stem: str, root: Path | None = None) -> NoteCard | None:
    path = progress_dir(root) / f"{stem}.md"
    parsed = try_read_note(path)
    if parsed is None:
        return None
    meta, body = parsed
    return NoteCard(path=path, stem=stem, meta=meta, body=body)


def find_intel_path(stem: str, root: Path | None = None) -> Path | None:
    """Resolve intel job note by stem; prefer active company folder over ``_归档``."""
    base = intel_dir(root)
    flat = base / f"{stem}.md"
    if flat.is_file():
        return flat
    matches = [
        p
        for p in base.rglob(f"{stem}.md")
        if p.is_file() and not p.name.startswith("_")
    ]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    def rank(p: Path) -> tuple:
        archived = 1 if _is_under_intel_archive(p, root) else 0
        return (archived, -len(p.parts), str(p))

    matches.sort(key=rank)
    return matches[0]


def intel_company_dir(company: str, root: Path | None = None) -> Path:
    safe = re.sub(r'[\\/:*?"<>|]', "-", str(company or "").strip()) or "_未知公司"
    return intel_dir(root) / safe


def intel_job_path(company: str, stem: str, root: Path | None = None) -> Path:
    """Canonical path for a job card under the company folder."""
    return intel_company_dir(company, root) / f"{stem}.md"


def intel_wikilink(stem: str, root: Path | None = None, alias: str | None = None) -> str:
    path = find_intel_path(stem, root)
    if path is None:
        target = f"秋招/02_情报库/{stem}"
    else:
        try:
            rel = path.relative_to(vault_root()).as_posix()
        except ValueError:
            rel = path.as_posix()
        if rel.endswith(".md"):
            rel = rel[:-3]
        target = rel
    if alias:
        return f"[[{target}|{alias}]]"
    return f"[[{target}]]"


def get_intel(stem: str, root: Path | None = None) -> NoteCard | None:
    path = find_intel_path(stem, root)
    if not path:
        return None
    try:
        meta, body = read_note(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    return NoteCard(path=path, stem=stem, meta=meta, body=body)


def list_intel_companies(root: Path | None = None) -> list[NoteCard]:
    """List company overview cards (`_公司.md`, type qiuzhao-intel-company)."""
    base = intel_dir(root)
    if not base.is_dir():
        return []
    cards: list[NoteCard] = []
    for path in sorted(base.rglob("_公司.md")):
        if _is_under_intel_archive(path, root):
            continue
        try:
            meta, body = read_note(path)
        except (UnicodeDecodeError, OSError, ValueError):
            # Sync/encryption corruption: skip so /api/intel stays up
            continue
        if meta.get("type") != "qiuzhao-intel-company":
            continue
        cards.append(NoteCard(path=path, stem=path.parent.name, meta=meta, body=body))
    return cards


def get_intel_company(company: str, root: Path | None = None) -> NoteCard | None:
    path = intel_company_dir(company, root) / "_公司.md"
    if not path.is_file():
        # try exact folder name match via meta
        for card in list_intel_companies(root):
            if str(card.meta.get("公司") or "") == company or card.stem == company:
                return card
        return None
    try:
        meta, body = read_note(path)
    except (UnicodeDecodeError, OSError, ValueError):
        return None
    return NoteCard(path=path, stem=path.parent.name, meta=meta, body=body)


def company_apply_limit(company: str, root: Path | None = None) -> int | None:
    card = get_intel_company(company, root)
    if not card:
        return None
    raw = card.meta.get("投递上限")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def normalize_apply_channels(raw: Any) -> list[dict[str, str]]:
    """Normalize company multi-source apply channels from frontmatter."""
    out: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = str(item.get("链接") or item.get("url") or "").strip()
        code = str(item.get("内推码") or item.get("code") or "").strip()
        if not url and not code:
            continue
        ch_type = str(item.get("类型") or item.get("type") or "其他").strip() or "其他"
        name = str(item.get("名称") or item.get("name") or ch_type).strip() or ch_type
        out.append(
            {
                "类型": ch_type,
                "名称": name,
                "链接": url,
                "内推码": code,
                "备注": str(item.get("备注") or item.get("note") or "").strip(),
                "更新于": str(item.get("更新于") or item.get("updated") or "").strip(),
            }
        )
    return out


def company_apply_channels(meta: dict[str, Any]) -> list[dict[str, str]]:
    channels = normalize_apply_channels(meta.get("投递渠道"))
    if channels:
        return channels
    # Legacy single fields → one channel
    url = str(meta.get("内推链接") or "").strip()
    code = str(meta.get("内推码") or "").strip()
    if url or code:
        return [
            {
                "类型": "HR内推",
                "名称": "HR内推",
                "链接": url,
                "内推码": code,
                "备注": "",
                "更新于": str(meta.get("更新于") or ""),
            }
        ]
    return []


def primary_referral_channel(meta: dict[str, Any]) -> dict[str, str] | None:
    channels = company_apply_channels(meta)
    for ch in channels:
        if ch.get("类型") == "投递记录":
            continue
        if ch.get("类型") in ("HR内推", "员工内推") or ch.get("内推码"):
            return ch
    for ch in channels:
        if ch.get("类型") not in ("投递记录", "汇总站"):
            return ch
    return None


def company_delivery_record_url(meta: dict[str, Any]) -> str:
    """Official application-status / delivery-record query URL for a company."""
    direct = str(meta.get("投递记录查询") or "").strip()
    if direct:
        return direct
    for ch in company_apply_channels(meta):
        if ch.get("类型") == "投递记录" and ch.get("链接"):
            return str(ch["链接"])
    return ""


def set_company_delivery_record_url(
    company: str,
    url: str,
    *,
    note: str = "",
    root: Path | None = None,
) -> NoteCard:
    """Save delivery-record query URL on company overview (SSOT + 投递渠道)."""
    url = str(url or "").strip()
    if not url:
        raise ValueError("投递记录查询链接不能为空")
    card = ensure_intel_company(company, root=root)
    card.meta["投递记录查询"] = url
    # Keep as a first-class channel for multi-source display
    upsert_company_apply_channel(
        company,
        url=url,
        code="",
        channel_type="投递记录",
        name="投递记录查询",
        note=note or "官网个人中心·投递记录/申请进度",
        root=root,
    )
    card = get_intel_company(company, root)
    if not card:
        raise FileNotFoundError(company)
    card.meta["投递记录查询"] = url
    card.meta["更新于"] = today_str()
    write_note(card.path, card.meta, card.body)
    return card


def _render_company_channels_section(channels: list[dict[str, str]]) -> str:
    if not channels:
        return (
            "## 投递渠道\n\n"
            "- （暂无；官网门户见上；HR/员工内推由助手写入本页，不进岗卡）\n"
        )
    lines = ["## 投递渠道", ""]
    for ch in channels:
        label = ch.get("名称") or ch.get("类型") or "渠道"
        url = ch.get("链接") or ""
        code = ch.get("内推码") or ""
        note = ch.get("备注") or ""
        bits = [f"- **{label}**（{ch.get('类型') or '其他'}）"]
        if url:
            bits.append(f"：[打开]({url})")
        if code:
            bits.append(f" · 内推码 `{code}`")
        if note:
            bits.append(f" · {note}")
        lines.append("".join(bits))
    lines.append("")
    return "\n".join(lines)


def _upsert_h2_section(body: str, heading: str, section_md: str) -> str:
    """Replace or append a markdown H2 section (heading included in section_md)."""
    text = body or ""
    pattern = re.compile(
        rf"(^##[ \t]+{re.escape(heading)}[ \t]*\n)(.*?)(?=^##[ \t]+|\Z)",
        re.M | re.S,
    )
    section_md = section_md.strip() + "\n\n"
    if pattern.search(text):
        return pattern.sub(section_md, text, count=1)
    if text and not text.endswith("\n"):
        text += "\n"
    return text.rstrip() + "\n\n" + section_md


def default_intel_company_body(
    company: str,
    *,
    portal: str = "",
    channels: list[dict[str, str]] | None = None,
    limit_note: str = "",
    remarks: list[str] | None = None,
) -> str:
    portal_line = f"- **门户**：[打开]({portal})\n" if portal else "- **门户**：待补\n"
    limit_line = limit_note or "未知（需再核实）；仅收录官网明确数字"
    remark_lines = remarks or [
        "限投数字仅收录官网/JD 明确表述；登录墙或找不到须知时 `需再核实: true`。",
        "HR/员工内推写入「投递渠道」，作为多源投递入口；**不**写入岗位情报卡。",
    ]
    return (
        f"# {company}\n\n"
        f"## 投递规则（仅官网核实）\n\n"
        f"- **投递上限**：{limit_line}\n"
        f"- **原文摘录**：待从官网须知补录。\n\n"
        f"## 校招门户\n\n"
        f"{portal_line}\n"
        f"{_render_company_channels_section(channels or [])}"
        f"## 在招 Agent 相关岗\n\n"
        f"见同目录岗卡；控制台职位页按公司聚合。\n\n"
        f"## 备注\n\n"
        + "".join(f"- {r}\n" for r in remark_lines)
    )


def ensure_intel_company(
    company: str,
    *,
    tier: str | None = None,
    portal: str = "",
    root: Path | None = None,
) -> NoteCard:
    """Ensure ``02_情报库/{公司}/_公司.md`` exists; return the card."""
    existing = get_intel_company(company, root)
    if existing:
        return existing
    safe_tier = normalize_company_tier(tier, company) if tier else normalize_company_tier(None, company)
    path = intel_company_dir(company, root) / "_公司.md"
    meta: dict[str, Any] = {
        "type": "qiuzhao-intel-company",
        "公司": company,
        "公司档次": safe_tier,
        "校招门户": portal or "",
        "投递上限": None,
        "投递上限说明": "",
        "投递渠道": [],
        "内推链接": "",
        "内推码": "",
        "投递记录查询": "",
        "届别窗口": "",
        "提前批是否占用正式批": None,
        "需再核实": True,
        "核实于": "",
        "tags": ["秋招", "情报", "公司"],
        "更新于": today_str(),
    }
    body = default_intel_company_body(company, portal=portal, channels=[])
    write_note(path, meta, body)
    return NoteCard(path=path, stem=path.parent.name, meta=meta, body=body)


def upsert_company_apply_channel(
    company: str,
    *,
    url: str,
    code: str = "",
    channel_type: str = "HR内推",
    name: str = "",
    note: str = "",
    tier: str | None = None,
    portal: str = "",
    root: Path | None = None,
) -> NoteCard:
    """Save/update a multi-source apply channel on the company overview card."""
    card = ensure_intel_company(company, tier=tier, portal=portal, root=root)
    url = str(url or "").strip()
    code = str(code or "").strip()
    if not url and not code:
        raise ValueError("需要内推链接或内推码至少一项")
    ch_type = str(channel_type or "HR内推").strip() or "HR内推"
    ch_name = str(name or ch_type).strip() or ch_type
    channels = company_apply_channels(card.meta)

    def same(a: dict[str, str]) -> bool:
        if code and a.get("内推码") == code and a.get("类型") == ch_type:
            return True
        if url and a.get("链接") == url:
            return True
        return False

    updated = {
        "类型": ch_type,
        "名称": ch_name,
        "链接": url,
        "内推码": code,
        "备注": str(note or "").strip(),
        "更新于": today_str(),
    }
    found = False
    for i, old in enumerate(channels):
        if same(old):
            merged = dict(old)
            merged.update({k: v for k, v in updated.items() if v or k == "更新于"})
            if not merged.get("链接") and url:
                merged["链接"] = url
            if not merged.get("内推码") and code:
                merged["内推码"] = code
            channels[i] = merged
            found = True
            break
    if not found:
        channels.append(updated)

    card.meta["投递渠道"] = channels
    # Convenience mirrors: latest HR/员工内推
    primary = primary_referral_channel({"投递渠道": channels})
    if primary:
        card.meta["内推链接"] = primary.get("链接") or ""
        card.meta["内推码"] = primary.get("内推码") or ""
    if portal:
        card.meta["校招门户"] = portal
    if tier:
        card.meta["公司档次"] = normalize_company_tier(tier, company)
    card.meta["更新于"] = today_str()
    card.body = _upsert_h2_section(
        card.body or default_intel_company_body(company),
        "投递渠道",
        _render_company_channels_section(channels),
    )
    write_note(card.path, card.meta, card.body)
    return NoteCard(path=card.path, stem=card.stem, meta=card.meta, body=card.body)


def load_company_tiers() -> dict[str, Any]:
    """Load company → tier map from qiuzhao/data/company_tiers.json."""
    global _COMPANY_TIERS_CACHE
    if _COMPANY_TIERS_CACHE is not None:
        return _COMPANY_TIERS_CACHE
    path = _DATA_DIR / "company_tiers.json"
    if not path.is_file():
        _COMPANY_TIERS_CACHE = {"companies": {}, "legacy_map": {}}
        return _COMPANY_TIERS_CACHE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    _COMPANY_TIERS_CACHE = raw
    return raw


def lookup_company_tier(company: str) -> str | None:
    """Exact then substring match against company_tiers.json."""
    name = str(company or "").strip()
    if not name:
        return None
    data = load_company_tiers()
    companies = data.get("companies") or {}
    if not isinstance(companies, dict):
        return None
    if name in companies:
        tier = companies[name]
        return tier if tier in COMPANY_TIERS else None
    # longer keys first for substring (e.g. 拼多多集团 before 拼多多)
    for key in sorted(companies.keys(), key=len, reverse=True):
        if key and key in name:
            tier = companies[key]
            if tier in COMPANY_TIERS:
                return tier
    return None


def normalize_company_tier(raw: Any, company: str = "") -> str:
    """Map legacy labels → 大厂/中厂/小厂/央国企/外企; prefer company table."""
    looked = lookup_company_tier(company)
    if looked:
        return looked
    text = str(raw or "").strip()
    data = load_company_tiers()
    legacy = data.get("legacy_map") or {}
    if isinstance(legacy, dict) and text in legacy:
        mapped = legacy[text]
        if mapped in COMPANY_TIERS:
            return mapped
    if text in COMPANY_TIERS:
        return text
    return "中厂"


def infer_role_family(position: str) -> str:
    """Infer 岗位族 from job title keywords."""
    t = str(position or "")
    tl = t.lower()
    if any(k in t or k in tl for k in ("Agent", "agent", "智能体", "Coze", "豆包")):
        return "Agent"
    if any(k in t for k in ("算法", "研究员", "研究")):
        return "算法"
    if any(k in t for k in ("前端", "Web", "web", "H5")):
        return "前端"
    if any(k in t for k in ("后端", "服务端", "基础架构", "SRE")):
        return "后端"
    if any(k in t for k in ("研发", "应用", "开发", "全栈", "工程")):
        return "研发应用"
    return "其他"


def default_apply_priority(tier: str) -> str:
    if tier in ("中厂", "小厂"):
        return "练手优先"
    if tier == "大厂":
        return "冲刺"
    if tier == "央国企":
        return "保底"
    if tier == "外企":
        return "冲刺"
    return "观望"


def normalize_hiring_status(meta: dict[str, Any], *, today: date | None = None) -> str:
    """Auto-correct 将截止/已截止 from 投递截止; keep explicit 未开招."""
    today = today or date.today()
    stored = str(meta.get("招聘状态") or "").strip()
    if stored == "未开招":
        return "未开招"
    dt = parse_dt(meta.get("投递截止"))
    if dt:
        d = dt.date() if isinstance(dt, datetime) else dt
        if d < today:
            return "已截止"
        if d <= today + timedelta(days=7):
            return "将截止"
        return "热招中"
    if stored in HIRING_STATUSES:
        return stored
    return "待核实"


def enrich_intel_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Fill/normalize classification fields on an intel card meta dict (in place)."""
    company = str(meta.get("公司") or "")
    position = str(meta.get("岗位") or "")
    tier = normalize_company_tier(meta.get("公司档次"), company)
    meta["公司档次"] = tier
    family = str(meta.get("岗位族") or "").strip()
    if family not in ROLE_FAMILIES:
        meta["岗位族"] = infer_role_family(position)
    pri = str(meta.get("投递优先级") or "").strip()
    if pri not in APPLY_PRIORITIES:
        meta["投递优先级"] = default_apply_priority(tier)
    link = str(meta.get("投递链接") or "").strip()
    if link:
        _scripts = Path(__file__).resolve().parent
        if str(_scripts) not in sys.path:
            sys.path.insert(0, str(_scripts))
        from job_apply_url import rewrite_job_apply_url  # noqa: WPS433

        meta["投递链接"] = rewrite_job_apply_url(link)[0]
    meta["招聘状态"] = normalize_hiring_status(meta)
    return meta


def update_intel_fields(
    stem: str,
    updates: dict[str, Any],
    root: Path | None = None,
) -> NoteCard:
    card = get_intel(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    for key, val in updates.items():
        if key not in INTEL_EDITABLE and key != "更新于":
            continue
        if val is None:
            card.meta[key] = None
        elif isinstance(val, str) and val.strip() == "" and key in (
            "开放日",
            "投递截止",
        ):
            card.meta[key] = None
        else:
            if key == "匹配分":
                try:
                    card.meta[key] = int(val)
                except (TypeError, ValueError):
                    card.meta[key] = val
            elif key == "需再核实":
                card.meta[key] = bool(val) if not isinstance(val, str) else val.lower() in (
                    "true",
                    "1",
                    "yes",
                    "是",
                )
            else:
                card.meta[key] = val
    enrich_intel_meta(card.meta)
    card.meta["更新于"] = today_str()
    new_body, body_changed = sync_intel_job_body_jd(
        card.body, str(card.meta.get("岗位简介") or "")
    )
    if body_changed:
        card.body = new_body
    write_note(card.path, card.meta, card.body)
    return card


def set_intel_apply_url(
    stem: str,
    new_url: str,
    *,
    root: Path | None = None,
) -> NoteCard:
    """Replace job-card 投递链接 in frontmatter, 来源链接, and body 岗位详情."""
    _scripts = Path(__file__).resolve().parent
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
    from job_apply_url import rewrite_job_apply_url  # noqa: WPS433

    card = get_intel(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    new_url = str(new_url or "").strip()
    if not new_url:
        raise ValueError("投递链接不能为空")
    new_url, _kind = rewrite_job_apply_url(new_url)
    old = str(card.meta.get("投递链接") or "").strip()
    card.meta["投递链接"] = new_url
    src = card.meta.get("来源链接")
    if isinstance(src, list):
        replaced = False
        out: list[str] = []
        for item in src:
            s = str(item or "").strip()
            if old and s == old:
                out.append(new_url)
                replaced = True
            else:
                out.append(s)
        if new_url not in out:
            out.insert(0, new_url)
        elif not replaced and old:
            pass
        card.meta["来源链接"] = out
    body = card.body or ""
    if old and old != new_url and old in body:
        body = body.replace(old, new_url)
    else:
        body = re.sub(
            r"(\*\*岗位详情\*\*：\[打开\]\()[^)]+(\))",
            rf"\1{new_url}\2",
            body,
            count=1,
        )
    card.body = body
    card.meta["更新于"] = today_str()
    write_note(card.path, card.meta, card.body)
    return NoteCard(path=card.path, stem=card.stem, meta=card.meta, body=card.body)


def backfill_intel_classification(root: Path | None = None) -> list[str]:
    """Normalize all intel cards; return list of updated stems."""
    updated: list[str] = []
    for card in list_intel(root):
        before = {
            "公司档次": card.meta.get("公司档次"),
            "岗位族": card.meta.get("岗位族"),
            "招聘状态": card.meta.get("招聘状态"),
            "投递优先级": card.meta.get("投递优先级"),
        }
        enrich_intel_meta(card.meta)
        after = {
            "公司档次": card.meta.get("公司档次"),
            "岗位族": card.meta.get("岗位族"),
            "招聘状态": card.meta.get("招聘状态"),
            "投递优先级": card.meta.get("投递优先级"),
        }
        if before != after or "岗位族" not in card.meta or "投递优先级" not in card.meta:
            card.meta["更新于"] = today_str()
            write_note(card.path, card.meta, card.body)
            updated.append(card.stem)
    return updated


def update_progress_fields(
    stem: str,
    updates: dict[str, Any],
    root: Path | None = None,
) -> NoteCard:
    card = get_progress(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    # Dedicated process replace (also syncs classic date fields)
    if "流程" in updates and updates["流程"] is not None:
        stages = updates["流程"]
        if not isinstance(stages, list):
            raise ValueError("流程 must be a list")
        return replace_progress_process(stem, stages, root=root)

    for key, val in updates.items():
        if key not in PROGRESS_EDITABLE and key != "更新于":
            continue
        if key == "流程":
            continue
        if val is None:
            card.meta[key] = None
        elif isinstance(val, str) and val.strip() == "":
            card.meta[key] = None if key.endswith("时间") or key in (
                "一面",
                "二面",
                "三面",
                "HR面",
                "投递时间",
                "测评时间",
                "笔试时间",
            ) else ""
        else:
            if key == "排序权重":
                try:
                    card.meta[key] = int(val)
                except (TypeError, ValueError):
                    card.meta[key] = val
            else:
                card.meta[key] = val
    card.meta["更新于"] = today_str()
    write_note(card.path, card.meta, card.body)
    return card


def _slug_id(label: str, fallback: str) -> str:
    raw = re.sub(r"\s+", "", str(label or "")).strip()
    raw = re.sub(r'[\\/:*?"<>|]', "-", raw)
    return (raw or fallback)[:40]


def normalize_process_stage(raw: Any, index: int = 0) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    label = str(raw.get("label") or raw.get("name") or f"环节{index + 1}").strip()
    sid = str(raw.get("id") or _slug_id(label, f"s{index + 1}")).strip()
    field_name = raw.get("field")
    if field_name is not None:
        field_name = str(field_name).strip() or None
    stype = str(raw.get("type") or "").strip()
    if not stype:
        if field_name and field_name in STAGE_TYPE_BY_FIELD:
            stype = STAGE_TYPE_BY_FIELD[field_name]
        elif label in ("Offer", "offer"):
            stype = "Offer"
        else:
            stype = "面试"
    when_raw = raw.get("when")
    if when_raw is None or when_raw == "":
        when_out: str | None = None
    else:
        when_out = fmt_dt(when_raw) or str(when_raw).strip() or None
    time_kind = normalize_time_kind(raw.get("time_kind"), stype)
    return {
        "id": sid,
        "label": label,
        "type": stype,
        "field": field_name,
        "when": when_out,
        "time_kind": time_kind,
    }


def default_process_template() -> list[dict[str, Any]]:
    return [dict(s) for s in DEFAULT_PROCESS_TEMPLATE]


def legacy_process_from_meta(meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Build process list from classic fixed fields (no 流程 yet)."""
    stages: list[dict[str, Any]] = []
    apply_when = fmt_dt(meta.get("投递时间")) or None
    stages.append(
        {
            "id": "apply",
            "label": "投递",
            "type": "投递",
            "field": "投递时间",
            "when": apply_when,
            "time_kind": default_time_kind_for_type("投递"),
        }
    )
    for field_name, label in STAGE_DEFS:
        if field_name == "Offer":
            stages.append(
                {
                    "id": "offer",
                    "label": "Offer",
                    "type": "Offer",
                    "field": None,
                    "when": None,
                    "time_kind": default_time_kind_for_type("Offer"),
                }
            )
            continue
        stype = STAGE_TYPE_BY_FIELD.get(field_name, "面试")
        stages.append(
            {
                "id": _slug_id(label, field_name),
                "label": label,
                "type": stype,
                "field": field_name,
                "when": fmt_dt(meta.get(field_name)) or None,
                "time_kind": default_time_kind_for_type(stype),
            }
        )
    return stages


def get_progress_process(card: NoteCard) -> list[dict[str, Any]]:
    raw = card.meta.get("流程")
    if isinstance(raw, list) and raw:
        return [normalize_process_stage(item, i) for i, item in enumerate(raw)]
    return legacy_process_from_meta(card.meta)


def _sync_classic_fields_from_process(
    meta: dict[str, Any], stages: list[dict[str, Any]]
) -> None:
    """Mirror known field/when pairs onto classic YAML keys for calendar compat."""
    used: set[str] = set()
    for stage in stages:
        field_name = stage.get("field")
        if not field_name or field_name not in KNOWN_STAGE_FIELDS:
            continue
        used.add(str(field_name))
        when = stage.get("when")
        meta[str(field_name)] = when if when else None
    for field_name in KNOWN_STAGE_FIELDS:
        if field_name not in used:
            # Keep value if still present but not in process? Clear for consistency.
            meta[field_name] = None


def replace_progress_process(
    stem: str,
    stages: list[Any],
    root: Path | None = None,
) -> NoteCard:
    card = get_progress(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    normalized = [normalize_process_stage(s, i) for i, s in enumerate(stages)]
    if not normalized:
        normalized = default_process_template()
    card.meta["流程"] = normalized
    _sync_classic_fields_from_process(card.meta, normalized)
    card.meta["更新于"] = today_str()
    write_note(card.path, card.meta, card.body)
    return card


def create_progress_manual(
    *,
    company: str,
    position: str,
    plan: str = "校招正式批",
    base: str = "",
    link: str = "",
    priority: str = "⚪ 观察池",
    root: Path | None = None,
) -> NoteCard:
    company = (company or "").strip()
    position = (position or "").strip()
    if not company or not position:
        raise ValueError("公司 and 岗位 are required")
    safe_name = re.sub(r'[\\/:*?"<>|]', "-", f"{company}-{position}")
    safe_name = re.sub(r"\s+", "", safe_name)[:80].strip("-") or "progress"
    out = progress_dir(root) / f"{safe_name}.md"
    if out.exists():
        # Unique suffix
        safe_name = f"{safe_name}-{uuid.uuid4().hex[:6]}"
        out = progress_dir(root) / f"{safe_name}.md"

    mianshi_stem = f"{company}-面经与复盘"
    mianshi_path = mianshi_dir(root) / f"{mianshi_stem}.md"
    ensure_mianshi_shell(company, mianshi_path, "")

    process = default_process_template()
    for s in process:
        s["when"] = None

    meta: dict[str, Any] = {
        "type": "qiuzhao-progress",
        "公司": company,
        "岗位": position,
        "招聘计划": plan if plan in PLANS else "校招正式批",
        "Base地": base or "",
        "投递状态": "待投",
        "优先级": priority if priority in PRIORITIES else "⚪ 观察池",
        "结果": "进行中",
        "投递时间": None,
        "测评时间": None,
        "笔试时间": None,
        "一面": None,
        "二面": None,
        "三面": None,
        "HR面": None,
        "内推人": "",
        "内推码": "",
        "投递链接": link or "",
        "投递记录查询": "",
        "备注": "",
        "关联情报": "",
        "关联面经": f"[[秋招/03_面经/{mianshi_stem}]]",
        "排序权重": 3,
        "流程": process,
        "tags": ["秋招", "进度"],
        "更新于": today_str(),
    }
    # Prefill from company SSOT when available
    ov = get_intel_company(company, root) if company else None
    if ov:
        referral = primary_referral_channel(ov.meta)
        if referral and referral.get("内推码"):
            meta["内推码"] = referral["内推码"]
        record_url = company_delivery_record_url(ov.meta)
        if record_url:
            meta["投递记录查询"] = record_url
        if not meta["投递链接"]:
            meta["投递链接"] = str(ov.meta.get("校招门户") or ov.meta.get("内推链接") or "")
    body = (
        f"# {company} · {position} 投递进度\n\n"
        f"由控制台手动新增。\n\n"
        f"## 关联\n"
        f"- 面经：[[秋招/03_面经/{mianshi_stem}]]\n"
    )
    write_note(out, meta, body)
    return NoteCard(path=out, stem=out.stem, meta=meta, body=body)


def archive_progress(stem: str, root: Path | None = None) -> Path:
    card = get_progress(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    archive_dir = progress_dir(root) / "_归档"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / card.path.name
    if dest.exists():
        dest = archive_dir / f"{card.path.stem}-{uuid.uuid4().hex[:6]}.md"
    card.path.rename(dest)
    return dest


def is_intel_archived(card_or_path: NoteCard | Path, root: Path | None = None) -> bool:
    path = card_or_path.path if isinstance(card_or_path, NoteCard) else card_or_path
    return _is_under_intel_archive(path, root)


def archive_intel(stem: str, root: Path | None = None) -> Path:
    """Move a closed job card to ``02_情报库/_归档/{公司}/``; keep file, mark 已截止."""
    card = get_intel(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    if _is_under_intel_archive(card.path, root):
        # Already archived — still ensure status
        enrich_intel_meta(card.meta)
        card.meta["招聘状态"] = "已截止"
        card.meta["更新于"] = today_str()
        write_note(card.path, card.meta, card.body)
        return card.path

    company = str(card.meta.get("公司") or "").strip() or "_未知公司"
    enrich_intel_meta(card.meta)
    card.meta["招聘状态"] = "已截止"
    card.meta["更新于"] = today_str()
    write_note(card.path, card.meta, card.body)

    dest_dir = intel_archive_dir(root) / re.sub(r'[\\/:*?"<>|]', "-", company)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / card.path.name
    if dest.exists():
        dest = dest_dir / f"{card.path.stem}-{uuid.uuid4().hex[:6]}.md"
    card.path.rename(dest)
    return dest


def scan_closed_intel(root: Path | None = None) -> list[NoteCard]:
    """All job cards whose normalized hiring status is 已截止 (active + archived)."""
    closed: list[NoteCard] = []
    for card in list_intel(root, include_archived=True):
        meta = dict(card.meta)
        if normalize_hiring_status(meta) == "已截止":
            closed.append(card)
    return closed


def archive_closed_intel(
    root: Path | None = None,
    *,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Scan vault, mark past-deadline jobs 已截止, move them under ``_归档``."""
    results: list[dict[str, Any]] = []
    for card in scan_closed_intel(root):
        already = _is_under_intel_archive(card.path, root)
        entry: dict[str, Any] = {
            "stem": card.stem,
            "company": card.meta.get("公司"),
            "position": card.meta.get("岗位"),
            "deadline": str(card.meta.get("投递截止") or ""),
            "from": str(card.path),
            "already_archived": already,
        }
        if already:
            entry["action"] = "skip"
            results.append(entry)
            continue
        if dry_run:
            entry["action"] = "would_archive"
            results.append(entry)
            continue
        dest = archive_intel(card.stem, root)
        entry["action"] = "archived"
        entry["to"] = str(dest)
        results.append(entry)
    return results


def progress_phase(card: NoteCard) -> str:
    """Fine stage for list tabs.

    Returns one of:
    apply | assessment | written | interview | waiting | offer | rejected | stopped
    """
    status = str(card.meta.get("投递状态") or "").strip()
    result = str(card.meta.get("结果") or "").strip()

    if status == "弃投":
        return "stopped"
    if result == "已拒" or status == "已拒":
        return "rejected"
    if result == "Offer" or status == "Offer":
        return "offer"
    if status == "等结果":
        return "waiting"
    if status == "待测评" or status.startswith("待测评"):
        return "assessment"
    if status == "待笔试" or status.startswith("待笔试"):
        return "written"
    if status.startswith("待面试"):
        return "interview"
    if status == "待投":
        return "apply"
    if status.startswith("待"):
        # Custom waiting statuses (e.g. 待ai面) → interview-ish unless测评/笔试
        if "测评" in status:
            return "assessment"
        if "笔试" in status:
            return "written"
        return "interview"

    # Infer from process schedule when status is blank / ambiguous
    for stage in get_progress_process(card):
        stype = str(stage.get("type") or "")
        label = str(stage.get("label") or "")
        has_when = bool(stage.get("when")) or (
            bool(stage.get("field")) and bool(parse_dt(card.meta.get(stage["field"])))
        )
        if not has_when:
            continue
        if stype == "面试" or label in ("一面", "二面", "三面", "HR面") or "面" in label:
            return "interview"
        if stype == "测评" or label == "测评":
            return "assessment"
        if stype == "笔试" or label == "笔试":
            return "written"
    return "apply"


def progress_bucket(card: NoteCard) -> str:
    """Coarse bucket: applying | interviewing | offer | stopped."""
    phase = progress_phase(card)
    if phase == "offer":
        return "offer"
    if phase in ("rejected", "stopped"):
        return "stopped"
    if phase == "apply":
        return "applying"
    return "interviewing"


def progress_stats(root: Path | None = None) -> dict[str, int]:
    """Counts for directory tabs + legacy coarse cards.

    Fine phases: apply / assessment / written / interview / waiting /
                 offer / rejected / stopped
    Coarse: applying (=apply) / interviewing (assessment+written+interview+waiting)
    active = all except offer/rejected/stopped
    stopped here means 弃投 only; rejected is separate.
    """
    counts = {
        "applying": 0,
        "interviewing": 0,
        "offer": 0,
        "stopped": 0,
        "rejected": 0,
        "active": 0,
        "apply": 0,
        "assessment": 0,
        "written": 0,
        "interview": 0,
        "waiting": 0,
        "total": 0,
    }
    for card in list_progress(root):
        counts["total"] += 1
        phase = progress_phase(card)
        if phase == "offer":
            counts["offer"] += 1
        elif phase == "rejected":
            counts["rejected"] += 1
        elif phase == "stopped":
            counts["stopped"] += 1
        elif phase == "apply":
            counts["apply"] += 1
            counts["applying"] += 1
            counts["active"] += 1
        elif phase == "assessment":
            counts["assessment"] += 1
            counts["interviewing"] += 1
            counts["active"] += 1
        elif phase == "written":
            counts["written"] += 1
            counts["interviewing"] += 1
            counts["active"] += 1
        elif phase == "interview":
            counts["interview"] += 1
            counts["interviewing"] += 1
            counts["active"] += 1
        elif phase == "waiting":
            counts["waiting"] += 1
            counts["interviewing"] += 1
            counts["active"] += 1
        else:
            counts["apply"] += 1
            counts["applying"] += 1
            counts["active"] += 1
    return counts


def create_progress_from_intel(intel_stem: str, root: Path | None = None) -> NoteCard:
    intel = get_intel(intel_stem, root)
    if not intel:
        raise FileNotFoundError(f"intel:{intel_stem}")
    company = str(intel.meta.get("公司") or "")
    position = str(intel.meta.get("岗位") or "")
    plan = str(intel.meta.get("招聘计划") or "校招正式批")
    safe_name = re.sub(r'[\\/:*?"<>|]', "-", f"{company}-{position}")
    safe_name = re.sub(r"\s+", "", safe_name)[:80].strip("-")
    if not safe_name:
        safe_name = intel_stem
    out = progress_dir(root) / f"{safe_name}.md"
    if out.exists():
        existing = try_read_note(out)
        if existing is not None:
            meta, body = existing
            return NoteCard(path=out, stem=out.stem, meta=meta, body=body)
        # Corrupt / non-UTF8 / encrypted remnant: quarantine and recreate
        quarantine_corrupt_note(out)

    intel_link = intel_wikilink(intel_stem, root)
    mianshi_stem = f"{company}-面经与复盘" if company else f"{intel_stem}-面经与复盘"
    mianshi_path = mianshi_dir(root) / f"{mianshi_stem}.md"
    ensure_mianshi_shell(company or intel_stem, mianshi_path, intel_link)

    process = default_process_template()
    for s in process:
        s["when"] = None

    ov = get_intel_company(company, root) if company else None
    referral = primary_referral_channel(ov.meta) if ov else None
    referral_code = (referral or {}).get("内推码") or (
        str(ov.meta.get("内推码") or "") if ov else ""
    )
    record_url = company_delivery_record_url(ov.meta) if ov else ""

    meta = {
        "type": "qiuzhao-progress",
        "公司": company,
        "岗位": position,
        "招聘计划": plan if plan in PLANS else "校招正式批",
        "Base地": "",
        "投递状态": "待投",
        "优先级": "⚪ 观察池",
        "结果": "进行中",
        "投递时间": None,
        "测评时间": None,
        "笔试时间": None,
        "一面": None,
        "二面": None,
        "三面": None,
        "HR面": None,
        "内推人": "",
        "内推码": referral_code,
        "投递链接": intel.meta.get("投递链接") or "",
        "投递记录查询": record_url,
        "备注": (
            f"公司内推渠道：{(referral or {}).get('链接')}"
            if referral and referral.get("链接")
            else ""
        ),
        "关联情报": intel_link,
        "关联面经": f"[[秋招/03_面经/{mianshi_stem}]]",
        "排序权重": 3,
        "流程": process,
        "tags": ["秋招", "进度"],
        "更新于": today_str(),
    }
    body = (
        f"# {company} · {position} 投递进度\n\n"
        f"由控制台从情报跟进生成。\n\n"
        f"## 关联\n"
        f"- 情报：{intel_link}\n"
        f"- 面经：[[秋招/03_面经/{mianshi_stem}]]\n"
    )
    write_note(out, meta, body)
    return NoteCard(path=out, stem=out.stem, meta=meta, body=body)


def ensure_mianshi_shell(company: str, path: Path, intel_link: str) -> None:
    if path.exists():
        return
    meta = {
        "type": "qiuzhao-mianshi",
        "公司": company,
        "tags": ["秋招", "面经"],
        "更新于": today_str(),
    }
    body = (
        f"# {company} · 面经与复盘\n\n"
        f"> 个人复盘壳；题库见知识库公司面经摘录。\n\n"
        f"## 关联情报\n- {intel_link}\n\n"
        f"## 复盘\n\n（待填写）\n"
    )
    write_note(path, meta, body)


def create_study_task(
    title: str,
    study_type: str,
    *,
    company: str = "",
    due: str = "",
    link: str = "",
    note: str = "",
    root: Path | None = None,
) -> NoteCard:
    study_type = study_type if study_type in STUDY_TYPES else "知识"
    safe = re.sub(r'[\\/:*?"<>|]', "-", title)[:60].strip("-") or "学习任务"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = study_dir(root) / f"{safe}-{stamp}.md"
    meta = {
        "type": "qiuzhao-study-task",
        "标题": title,
        "类型": study_type,
        "关联公司": company,
        "截止日期": due or None,
        "状态": "待做",
        "关联笔记": link,
        "备注": note,
        "tags": ["秋招", "任务", study_type],
        "更新于": today_str(),
    }
    body = f"# {title}\n\n类型：{study_type}\n\n{note}\n"
    write_note(path, meta, body)
    return NoteCard(path=path, stem=path.stem, meta=meta, body=body)


def update_study_fields(
    stem: str,
    updates: dict[str, Any],
    root: Path | None = None,
) -> NoteCard:
    path = study_dir(root) / f"{stem}.md"
    if not path.is_file():
        raise FileNotFoundError(stem)
    meta, body = read_note(path)
    for key in ("状态", "截止日期", "备注", "关联公司", "关联笔记", "标题", "类型"):
        if key in updates:
            meta[key] = updates[key] if updates[key] != "" else None
    meta["更新于"] = today_str()
    write_note(path, meta, body)
    return NoteCard(path=path, stem=stem, meta=meta, body=body)


# ----- Agent queue (single markdown table) -----

QUEUE_HEADER = (
    "| id | 创建于 | 意图 | 载荷 | 状态 | 结果摘要 |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
)


@dataclass
class AgentJob:
    id: str
    created_at: str
    intent: str
    payload: str
    status: str
    result: str = ""


def ensure_agent_queue(root: Path | None = None) -> Path:
    path = agent_queue_path(root)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "---\n"
            "type: qiuzhao-agent-queue\n"
            "tags:\n"
            "  - 秋招\n"
            "  - 任务\n"
            f"更新于: {today_str()}\n"
            "---\n"
            "# Agent 任务队列\n\n"
            "控制台写入「待处理」；Cursor 说 `处理控制台任务` 消费。\n\n"
            f"{QUEUE_HEADER}"
        )
        path.write_text(content, encoding="utf-8", newline="\n")
    return path


def _parse_queue_rows(text: str) -> list[AgentJob]:
    jobs: list[AgentJob] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 6:
            continue
        if parts[0] in ("id", "---") or parts[0].startswith("-"):
            continue
        jobs.append(
            AgentJob(
                id=parts[0],
                created_at=parts[1],
                intent=parts[2],
                payload=parts[3],
                status=parts[4],
                result=parts[5] if len(parts) > 5 else "",
            )
        )
    return jobs


def list_agent_jobs(root: Path | None = None, status: str | None = None) -> list[AgentJob]:
    path = ensure_agent_queue(root)
    # Use the same resilient decoder as notes (E: disk corruption / magic 241a9c92).
    try:
        raw = path.read_bytes()
        text = _decode_note_text(raw)
    except Exception:
        # Last resort: never crash health/SPA on a single bad queue file.
        text = ""
    jobs = _parse_queue_rows(text)
    if status:
        jobs = [j for j in jobs if j.status == status]
    return jobs

def _write_queue(jobs: list[AgentJob], root: Path | None = None) -> None:
    path = ensure_agent_queue(root)
    meta, _body = read_note(path)
    meta["type"] = "qiuzhao-agent-queue"
    meta["更新于"] = today_str()
    if "tags" not in meta:
        meta["tags"] = ["秋招", "任务"]
    lines = [
        "# Agent 任务队列\n",
        "\n控制台写入「待处理」；Cursor 说 `处理控制台任务` 消费。\n\n",
        QUEUE_HEADER,
    ]
    for j in jobs:
        payload = j.payload.replace("|", "\\|")
        result = (j.result or "").replace("|", "\\|")
        lines.append(
            f"| {j.id} | {j.created_at} | {j.intent} | {payload} | {j.status} | {result} |\n"
        )
    write_note(path, meta, "".join(lines))


def append_agent_job(
    intent: str,
    payload: str = "",
    root: Path | None = None,
) -> AgentJob:
    if intent not in AGENT_INTENTS:
        raise ValueError(f"unknown intent: {intent}")
    jobs = list_agent_jobs(root)
    job = AgentJob(
        id=uuid.uuid4().hex[:8],
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        intent=intent,
        payload=payload.strip(),
        status="待处理",
        result="",
    )
    jobs.append(job)
    _write_queue(jobs, root)
    return job


def update_agent_job(
    job_id: str,
    *,
    status: str | None = None,
    result: str | None = None,
    root: Path | None = None,
) -> AgentJob:
    jobs = list_agent_jobs(root)
    for j in jobs:
        if j.id == job_id:
            if status:
                j.status = status
            if result is not None:
                j.result = result
            _write_queue(jobs, root)
            return j
    raise FileNotFoundError(job_id)


# ----- Timeline / conflicts / health -----


@dataclass
class TimelineEvent:
    when: datetime
    label: str
    company: str
    position: str
    stem: str
    field: str


def collect_progress_events(root: Path | None = None) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for card in list_progress(root):
        company = str(card.meta.get("公司") or card.stem)
        position = str(card.meta.get("岗位") or "")
        seen_fields: set[str] = set()
        for stage in get_progress_process(card):
            when = stage.get("when")
            dt = parse_dt(when)
            if not dt:
                continue
            field_name = str(stage.get("field") or stage.get("id") or stage.get("label") or "")
            seen_fields.add(field_name)
            base = str(stage.get("label") or field_name)
            kind = normalize_time_kind(stage.get("time_kind"), str(stage.get("type") or ""))
            events.append(
                TimelineEvent(
                    when=dt,
                    label=f"{base}（{kind}）",
                    company=company,
                    position=position,
                    stem=card.stem,
                    field=field_name,
                )
            )
        # Also classic fields not already covered (legacy notes without full 流程 sync)
        for field_name, label in EVENT_FIELDS:
            if field_name in seen_fields:
                continue
            dt = parse_dt(card.meta.get(field_name))
            if dt:
                events.append(
                    TimelineEvent(
                        when=dt,
                        label=label,
                        company=company,
                        position=position,
                        stem=card.stem,
                        field=field_name,
                    )
                )
    events.sort(key=lambda e: e.when)
    return events


def events_in_window(
    days: int = 3,
    root: Path | None = None,
    now: datetime | None = None,
) -> list[TimelineEvent]:
    now = now or datetime.now()
    end = now + timedelta(days=days)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return [e for e in collect_progress_events(root) if start <= e.when <= end]


def find_conflicts(
    window_hours: float = 2.0,
    horizon_days: int = 14,
    root: Path | None = None,
) -> list[tuple[TimelineEvent, TimelineEvent]]:
    now = datetime.now()
    end = now + timedelta(days=horizon_days)
    events = [e for e in collect_progress_events(root) if now <= e.when <= end]
    conflicts: list[tuple[TimelineEvent, TimelineEvent]] = []
    gap = timedelta(hours=window_hours)
    for i, a in enumerate(events):
        for b in events[i + 1 :]:
            if b.when - a.when > gap:
                break
            if a.stem == b.stem and a.field == b.field:
                continue
            conflicts.append((a, b))
    return conflicts


def study_due_soon(days: int = 3, root: Path | None = None) -> list[NoteCard]:
    now = date.today()
    end = now + timedelta(days=days)
    due: list[NoteCard] = []
    for card in list_study(root):
        if card.meta.get("状态") == "完成":
            continue
        d = parse_dt(card.meta.get("截止日期"))
        if not d:
            due.append(card)
            continue
        if now <= d.date() <= end:
            due.append(card)
    return due


@dataclass
class HealthReport:
    vault: str
    qiuzhao_ok: bool
    progress_count: int
    intel_count: int
    study_count: int
    pending_jobs: int
    mianshi_count: int = 0
    messages: list[str] = field(default_factory=list)


def health_check(root: Path | None = None, *, light: bool = False) -> HealthReport:
    """Vault connectivity + counts.

    ``light=True`` skips full typed scans (intel/progress/study/mianshi) so the
    SPA can fetch enums / pending queue without waiting on hundreds of markdown reads.
    """
    root = root or vault_root()
    q = qiuzhao_root(root)
    messages: list[str] = []
    try:
        ok = q.is_dir()
    except OSError as exc:
        ok = False
        messages.append(f"无法访问秋招目录: {q} ({exc})")
    if not ok:
        if not messages:
            messages.append(f"找不到秋招目录: {q}")
        return HealthReport(
            vault=str(root),
            qiuzhao_ok=False,
            progress_count=0,
            intel_count=0,
            study_count=0,
            pending_jobs=0,
            mianshi_count=0,
            messages=messages,
        )
    ensure_agent_queue(root)
    study_dir(root).mkdir(parents=True, exist_ok=True)
    campus_events_dir(root).mkdir(parents=True, exist_ok=True)
    ensure_campus_events_inbox(root)
    if light:
        pending = len(list_agent_jobs(root, status="待处理"))
        return HealthReport(
            vault=str(root),
            qiuzhao_ok=ok,
            progress_count=0,
            intel_count=0,
            study_count=0,
            pending_jobs=pending,
            mianshi_count=0,
            messages=messages,
        )
    return HealthReport(
        vault=str(root),
        qiuzhao_ok=ok,
        progress_count=len(list_progress(root)),
        intel_count=len(list_intel(root)),
        study_count=len(list_study(root)),
        pending_jobs=len(list_agent_jobs(root, status="待处理")),
        mianshi_count=len(list_mianshi(root)),
        messages=messages,
    )


# ----- Mianshi / knowledge bank / profile / SPA helpers -----


def list_mianshi(root: Path | None = None) -> list[NoteCard]:
    return _list_typed(mianshi_dir(root), "qiuzhao-mianshi")


def get_mianshi(stem: str, root: Path | None = None) -> NoteCard | None:
    path = mianshi_dir(root) / f"{stem}.md"
    if not path.is_file():
        return None
    meta, body = read_note(path)
    return NoteCard(path=path, stem=stem, meta=meta, body=body)


def update_mianshi_fields(
    stem: str,
    *,
    body: str | None = None,
    meta_updates: dict[str, Any] | None = None,
    root: Path | None = None,
) -> NoteCard:
    card = get_mianshi(stem, root)
    if not card:
        raise FileNotFoundError(stem)
    if meta_updates:
        for key, val in meta_updates.items():
            if key == "type":
                continue
            card.meta[key] = val
    if body is not None:
        card.body = body
    card.meta["更新于"] = today_str()
    write_note(card.path, card.meta, card.body)
    return card


def get_question_bank(company: str, root: Path | None = None) -> NoteCard | None:
    """Match company to 公司面经摘录/*-Agent面经题库.md by 关联公司 or filename."""
    company = (company or "").strip()
    if not company:
        return None
    directory = knowledge_bank_dir(root)
    if not directory.is_dir():
        return None
    exact = directory / f"{company}-Agent面经题库.md"
    if exact.is_file():
        meta, body = read_note(exact)
        return NoteCard(path=exact, stem=exact.stem, meta=meta, body=body)
    for path in sorted(directory.glob("*面经题库.md")):
        if path.name.startswith("_"):
            continue
        meta, body = read_note(path)
        if meta.get("type") and meta.get("type") != "qiuzhao-knowledge":
            continue
        linked = str(meta.get("关联公司") or "")
        if company in linked or linked in company or company in path.stem:
            return NoteCard(path=path, stem=path.stem, meta=meta, body=body)
    return None


def parse_question_bank_groups(body: str) -> list[dict[str, Any]]:
    """Parse `#类型` + numbered list into groups."""
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in (body or "").splitlines():
        s = line.strip()
        if s.startswith("#") and not s.startswith("##"):
            title = s.lstrip("#").strip()
            if not title or title.endswith("面经题库"):
                continue
            current = {"type": title, "questions": []}
            groups.append(current)
            continue
        m = re.match(r"^(\d+)[\.\)、]\s*(.+)$", s)
        if m and current is not None:
            current["questions"].append({"index": int(m.group(1)), "text": m.group(2).strip()})
    return groups


def coding_checklist_path(root: Path | None = None) -> Path:
    return qiuzhao_root(root) / "06_知识库" / "手撕与算法" / "高频手撕清单.md"


def parse_coding_checklist(body: str) -> list[dict[str, Any]]:
    """Parse `#知识点` + `- [ ]` / `- [x]` rows from 高频手撕清单."""
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    item_re = re.compile(r"^- \[([ xX])\]\s+(.+)$")
    for line in (body or "").splitlines():
        s = line.strip()
        if s.startswith("##"):
            continue
        if s.startswith("#"):
            title = s.lstrip("#").strip()
            if not title:
                continue
            current = {"topic": title, "items": []}
            groups.append(current)
            continue
        m = item_re.match(s)
        if m and current is not None:
            done = m.group(1).lower() == "x"
            rest = re.sub(r"\s*✅.*$", "", m.group(2).strip()).strip()
            text, sources = rest, []
            if "· 来源：" in rest:
                text, src = rest.split("· 来源：", 1)
                sources = [x.strip() for x in src.split(",") if x.strip()]
            current["items"].append(
                {"text": text.strip(), "sources": sources, "done": done}
            )
    return [g for g in groups if g.get("items")]


def get_coding_checklist(root: Path | None = None) -> dict[str, Any]:
    path = coding_checklist_path(root)
    if not path.is_file():
        return {"stem": None, "rel": "", "meta": {}, "groups": []}
    meta, body = read_note(path)
    return {
        "stem": path.stem,
        "rel": str(path),
        "meta": _jsonable_meta(meta),
        "groups": parse_coding_checklist(body),
    }


def get_profile(root: Path | None = None) -> NoteCard | None:
    path = profile_path(root)
    parsed = try_read_note(path)
    if parsed is None:
        return None
    meta, body = parsed
    return NoteCard(path=path, stem=path.stem, meta=meta, body=body)


def _wikilink_stem(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        for item in value:
            s = _wikilink_stem(item)
            if s:
                return s
        return None
    s = str(value).strip()
    m = re.search(r"\[\[([^\]|#]+)", s)
    if not m:
        return None
    target = m.group(1).strip()
    return Path(target.replace("\\", "/")).name


def intel_follow_status(
    intel_stem: str,
    root: Path | None = None,
    *,
    progress: list[NoteCard] | None = None,
) -> str | None:
    """Return progress stem if any progress card links this intel, else None.

    Pass ``progress`` (preloaded cards) when serializing many intel rows so we do
    not re-read ``05_投递进度`` once per job.
    """
    needle = intel_stem
    cards = progress if progress is not None else list_progress(root)
    for card in cards:
        linked = _wikilink_stem(card.meta.get("关联情报"))
        if linked == needle or linked == f"{needle}.md":
            return card.stem
        # also match by company+position filename prefix
        if card.stem.startswith(needle) or needle in str(card.meta.get("关联情报") or ""):
            return card.stem
    return None


def batch_intel_follow_status(
    intel_stems: list[str],
    root: Path | None = None,
) -> dict[str, str | None]:
    """Resolve followed_by for many intel stems with a single progress directory read."""
    progress = list_progress(root)
    return {stem: intel_follow_status(stem, progress=progress) for stem in intel_stems}


def progress_current_stage(card: NoteCard) -> str | None:
    status = str(card.meta.get("投递状态") or "")
    result = str(card.meta.get("结果") or "")
    process = get_progress_process(card)
    labels = [str(s["label"]) for s in process]

    if result == "Offer" or status == "Offer":
        if "Offer" in labels:
            return "Offer"
        return labels[-1] if labels else None

    mapped = STATUS_TO_STAGE.get(status)
    if mapped and mapped in labels:
        return mapped
    # Fuzzy: status contains label
    for label in labels:
        if label and label in status:
            return label

    # Last stage that has a when
    last: str | None = None
    for stage in process:
        if stage.get("label") == "Offer":
            continue
        if parse_dt(stage.get("when")):
            last = str(stage["label"])
        elif stage.get("field") and parse_dt(card.meta.get(stage["field"])):
            last = str(stage["label"])
    return last


def progress_next_event(card: NoteCard, now: datetime | None = None) -> dict[str, Any] | None:
    now = now or datetime.now()
    upcoming: list[tuple[datetime, str, str]] = []
    for stage in get_progress_process(card):
        when = stage.get("when")
        if not when and stage.get("field"):
            when = card.meta.get(stage["field"])
        dt = parse_dt(when)
        if dt and dt >= now:
            field_name = str(stage.get("field") or stage.get("id") or "")
            base = str(stage.get("label") or field_name)
            kind = normalize_time_kind(stage.get("time_kind"), str(stage.get("type") or ""))
            label = f"{base}（{kind}）" if kind else base
            upcoming.append((dt, label, field_name))
    if not upcoming:
        return None
    upcoming.sort(key=lambda x: x[0])
    dt, label, field_name = upcoming[0]
    return {"when": fmt_dt(dt), "label": label, "field": field_name}


def progress_to_stages(card: NoteCard) -> list[dict[str, Any]]:
    current = progress_current_stage(card)
    result = str(card.meta.get("结果") or "")
    status = str(card.meta.get("投递状态") or "")
    process = get_progress_process(card)
    labels = [str(s["label"]) for s in process]
    current_idx = labels.index(current) if current in labels else -1
    stages: list[dict[str, Any]] = []

    for i, stage in enumerate(process):
        label = str(stage["label"])
        field_name = stage.get("field")
        when = stage.get("when")
        if not when and field_name:
            when = fmt_dt(card.meta.get(field_name)) or None
        else:
            when = when or None

        if label == "Offer" or stage.get("type") == "Offer":
            if result == "Offer" or status == "Offer":
                state = "done"
            elif current == label:
                state = "active"
            else:
                state = "pending"
        elif current == label:
            state = "active"
        elif when and current_idx >= 0 and i < current_idx:
            state = "done"
        elif when and current_idx < 0:
            state = "done"
        elif current_idx >= 0 and i < current_idx:
            state = "done"
        else:
            state = "pending"

        stages.append(
            {
                "key": str(stage.get("id") or label),
                "id": str(stage.get("id") or label),
                "label": label,
                "type": str(stage.get("type") or ""),
                "field": field_name,
                "when": when,
                "time_kind": normalize_time_kind(
                    stage.get("time_kind"), str(stage.get("type") or "")
                ),
                "state": state,
            }
        )
    return stages


def collect_deadline_events(root: Path | None = None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for card in list_intel(root):
        dt = parse_dt(card.meta.get("投递截止"))
        if not dt:
            continue
        events.append(
            {
                "when": dt.isoformat(timespec="minutes"),
                "when_fmt": fmt_dt(dt),
                "label": "投递截止",
                "company": str(card.meta.get("公司") or card.stem),
                "position": str(card.meta.get("岗位") or ""),
                "stem": card.stem,
                "kind": "deadline",
                "source": "intel",
            }
        )
    return events


def list_campus_events(root: Path | None = None) -> list[NoteCard]:
    return _list_typed(campus_events_dir(root), "qiuzhao-campus-event")


def get_campus_event(stem: str, root: Path | None = None) -> NoteCard | None:
    path = campus_events_dir(root) / f"{stem}.md"
    if not path.is_file():
        return None
    meta, body = read_note(path)
    return NoteCard(path=path, stem=stem, meta=meta, body=body)


def _safe_filename(text: str, limit: int = 48) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "-", str(text or "").strip())
    safe = re.sub(r"\s+", "", safe)
    return (safe[:limit].strip("-") or "活动")


def campus_event_stem(ev: dict[str, Any]) -> str:
    ext = str(ev.get("外部ID") or "").strip()
    if ext:
        kind, _, eid = ext.partition("/")
        kind = kind or "event"
        eid = eid or ext
        return f"{kind}-{eid}"
    day = str(ev.get("开始") or "")[:10].replace("-", "") or today_str().replace("-", "")
    company = _safe_filename(str(ev.get("公司") or ev.get("标题") or "活动"), 36)
    return f"{day}-{company}"


_CAMPUS_TITLE_SUFFIXES = (
    "专场宣讲会",
    "专场招聘会",
    "专场双选会",
    "校园宣讲会",
    "宣讲会",
    "招聘会",
    "双选会",
    "专场",
)


def strip_campus_event_suffix(name: str) -> str:
    """Remove 宣讲会/专场 etc. so cross-source titles compare equal."""
    s = str(name or "").strip()
    changed = True
    while changed and s:
        changed = False
        for suf in _CAMPUS_TITLE_SUFFIXES:
            if s.endswith(suf):
                s = s[: -len(suf)].strip(" ·-—_")
                changed = True
                break
    return s


def campus_company_key(name: str) -> str:
    return _normalize_company_key(strip_campus_event_suffix(name))


def normalize_campus_place(place: str) -> str:
    """Fuzzy place key: drop room suffixes, unify A楼/A-, strip separators."""
    s = str(place or "")
    for junk in ("报告厅", "会议室", "教室", "北会议室", "南会议室"):
        s = s.replace(junk, "")
    s = s.replace("·", "").replace(" ", "").replace("　", "").replace("-", "")
    s = s.replace("楼", "")
    # A105 vs A¥105 already handled by 楼 strip → A105
    return s.lower()


def campus_places_compatible(a: str, b: str) -> bool:
    """True if places likely refer to the same room (or one missing)."""
    pa, pb = str(a or "").strip(), str(b or "").strip()
    if not pa or not pb:
        return True
    na, nb = normalize_campus_place(pa), normalize_campus_place(pb)
    if not na or not nb:
        return True
    if na == nb:
        return True
    # substring (西大楼204教室 vs 西大楼204)
    if na in nb or nb in na:
        return True
    # room digits + campus token
    def campus_token(p: str) -> str:
        for t in ("雁塔", "长安", "北校", "南校"):
            if t in p:
                return t
        return ""

    ca, cb = campus_token(pa), campus_token(pb)
    if ca and cb and ca != cb:
        # 雁塔 vs 长安 are different campuses — never merge
        if {ca, cb} <= {"雁塔", "长安"} or {ca, cb} <= {"北校", "南校"}:
            return False
        if (ca in ("雁塔", "北校") and cb in ("长安", "南校")) or (
            ca in ("长安", "南校") and cb in ("雁塔", "北校")
        ):
            return False
    # extract trailing room code like 204 / a105 / b101
    ra = re.sub(r".*?([a-z]?\d{2,4})$", r"\1", na)
    rb = re.sub(r".*?([a-z]?\d{2,4})$", r"\1", nb)
    if ra and rb and ra == rb and len(ra) >= 2:
        # same room number; require shared campus or no campus conflict
        if not ca or not cb or ca == cb:
            return True
        if ca in ("雁塔", "北校") and cb in ("雁塔", "北校"):
            return True
        if ca in ("长安", "南校") and cb in ("长安", "南校"):
            return True
    return False


def merge_campus_sources(*sources: Any) -> str:
    parts: list[str] = []
    for raw in sources:
        if raw is None or raw == "":
            continue
        for piece in re.split(r"[·+/|,，、]", str(raw)):
            p = piece.strip()
            if p and p not in parts:
                parts.append(p)
    return " · ".join(parts)


def _campus_place_quality(place: str) -> int:
    """Higher = more likely a real venue (not company name pasted into 地点)."""
    p = str(place or "").strip()
    if not p:
        return 0
    score = len(p)
    for tip in ("报告厅", "教室", "会议室", "食堂", "体育馆", "图书馆", "A-", "B-", "西大楼", "会议中心"):
        if tip in p:
            score += 20
    # employment site sometimes puts company into 地点
    if "有限公司" in p or "研究所" in p and "楼" not in p and "厅" not in p:
        score -= 40
    return score


def find_matching_campus_event(
    ev: dict[str, Any],
    root: Path | None = None,
    *,
    cards: list[NoteCard] | None = None,
) -> NoteCard | None:
    """Match by 外部ID, else company+start+compatible place (cross-source)."""
    cards = cards if cards is not None else list_campus_events(root)
    ext = str(ev.get("外部ID") or "").strip()
    if ext:
        for card in cards:
            if str(card.meta.get("外部ID") or "") == ext:
                return card
    company = str(ev.get("公司") or ev.get("标题") or "").strip()
    start = str(ev.get("开始") or "").strip()
    place = str(ev.get("地点") or "").strip()
    ck = campus_company_key(company)
    if not ck or not start:
        return None
    for card in cards:
        m = card.meta
        if str(m.get("开始") or "").strip() != start:
            continue
        other = campus_company_key(str(m.get("公司") or m.get("标题") or ""))
        if not other or other != ck:
            # allow key containment for long institute names
            if not other or (ck not in other and other not in ck) or min(len(ck), len(other)) < 4:
                continue
        if campus_places_compatible(place, str(m.get("地点") or "")):
            return card
    return None


def _normalize_company_key(name: str) -> str:
    s = re.sub(r"\s+", "", str(name or ""))
    for junk in (
        "股份有限公司",
        "有限责任公司",
        "有限公司",
        "集团有限公司",
        "集团公司",
        "科技",
        "集团",
        "公司",
        "（",
        "）",
        "(",
        ")",
    ):
        s = s.replace(junk, "")
    return s.lower()


def match_intel_company(company: str, root: Path | None = None) -> str | None:
    """Return company name if intel library has a matching company.

    Skips unreadable notes so one corrupt file does not block campus upserts.
    """
    company = (company or "").strip()
    if not company:
        return None
    key = _normalize_company_key(company)
    if not key:
        return None
    best: str | None = None
    best_score = 0
    candidates: list[str] = []
    base = intel_dir(root)
    if base.is_dir():
        for child in base.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                candidates.append(child.name)
            overview = child / "_公司.md" if child.is_dir() else None
            if overview and overview.is_file():
                try:
                    meta, _ = read_note(overview)
                    cand = str(meta.get("公司") or "").strip()
                    if cand:
                        candidates.append(cand)
                except (UnicodeDecodeError, OSError, ValueError):
                    continue
    seen: set[str] = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        ck = _normalize_company_key(cand)
        if not ck:
            continue
        score = 0
        if ck == key:
            score = 100
        elif key in ck or ck in key:
            score = min(len(key), len(ck))
        if score > best_score:
            best_score = score
            best = cand
    if best_score >= 4:
        return best
    return None


def default_campus_event_body(meta: dict[str, Any]) -> str:
    title = str(meta.get("标题") or meta.get("公司") or "校园活动")
    link = str(meta.get("来源链接") or "")
    intel = str(meta.get("关联情报") or "")
    lines = [
        f"# {title}",
        "",
        f"- 活动类型：{meta.get('活动类型') or ''}",
        f"- 形式：{meta.get('形式') or ''}",
        f"- 地点：{meta.get('地点') or ''}",
        f"- 开始：{meta.get('开始') or ''}",
        f"- 结束：{meta.get('结束') or ''}",
        f"- 状态：{meta.get('状态') or ''}",
        f"- 来源：{meta.get('来源') or ''}",
        f"- 来源链接：{link}" if link else "- 来源链接：",
        f"- 关联情报：{intel}" if intel else "- 关联情报：",
        "",
        "## 备注",
        "",
        str(meta.get("备注") or meta.get("原始摘要") or ""),
        "",
    ]
    return "\n".join(lines)


def upsert_campus_event(ev: dict[str, Any], root: Path | None = None) -> NoteCard:
    """Create or update one campus event note.

    Dedupes by 外部ID, else fuzzy company+start+compatible place so 就业网/公众号
    do not create duplicate cards for the same talk.
    """
    root = root or vault_root()
    directory = campus_events_dir(root)
    directory.mkdir(parents=True, exist_ok=True)

    cards = list_campus_events(root)
    existing = find_matching_campus_event(ev, root, cards=cards)

    # Prefer keeping employment-site stem (external id) when merging into 公众号 note
    prefer_new_path = False
    if existing and str(ev.get("外部ID") or "").strip():
        new_stem = campus_event_stem(ev)
        if existing.stem != new_stem and not str(existing.meta.get("外部ID") or "").strip():
            prefer_new_path = True

    if prefer_new_path:
        stem = campus_event_stem(ev)
        path = directory / f"{stem}.md"
    else:
        stem = existing.stem if existing else campus_event_stem(ev)
        path = existing.path if existing else directory / f"{stem}.md"

    company_raw = str(ev.get("公司") or "").strip() or strip_campus_event_suffix(
        str(ev.get("标题") or "")
    )
    matched = match_intel_company(company_raw, root)
    intel_link = f"[[秋招/02_情报库/{matched}]]" if matched else (ev.get("关联情报") or None)

    meta: dict[str, Any] = dict(existing.meta) if existing else {"type": "qiuzhao-campus-event"}
    meta["type"] = "qiuzhao-campus-event"

    # Merge sources instead of overwriting
    meta["来源"] = merge_campus_sources(meta.get("来源"), ev.get("来源"))

    for key in (
        "公司",
        "标题",
        "活动类型",
        "形式",
        "地点",
        "开始",
        "结束",
        "状态",
        "来源链接",
        "外部ID",
        "备注",
    ):
        val = ev.get(key)
        if val in (None, ""):
            continue
        if key == "地点":
            old_p = str(meta.get("地点") or "")
            if _campus_place_quality(str(val)) >= _campus_place_quality(old_p):
                meta[key] = val
            continue
        if key == "标题":
            # Prefer shorter clean title without redundant 宣讲会 if company known
            old_t = str(meta.get("标题") or "")
            if not old_t or (str(val) and len(str(val)) < len(old_t)):
                meta[key] = val
            continue
        if key == "公司":
            cleaned = strip_campus_event_suffix(str(val)) or str(val)
            meta[key] = cleaned
            continue
        if key in ("来源链接", "外部ID") and meta.get(key) and not str(ev.get("外部ID") or ""):
            # don't let 公众号 wipe employment-site id/url
            continue
        meta[key] = val

    if company_raw and not meta.get("公司"):
        meta["公司"] = strip_campus_event_suffix(company_raw) or company_raw
    if intel_link:
        meta["关联情报"] = intel_link
    meta["核实于"] = today_str()
    meta["更新于"] = today_str()
    tags = meta.get("tags")
    if not isinstance(tags, list):
        tags = []
    for t in ("秋招", "校园活动", str(meta.get("活动类型") or "宣讲会")):
        if t and t not in tags:
            tags.append(t)
    meta["tags"] = tags

    body = existing.body if existing and existing.body.strip() else default_campus_event_body(meta)
    if existing is None or "## 备注" in body:
        note = ""
        if existing and "## 备注" in existing.body:
            note = existing.body.split("## 备注", 1)[-1].strip()
        meta_for_body = dict(meta)
        if note:
            meta_for_body["备注"] = note
        elif ev.get("原始摘要"):
            meta_for_body["备注"] = str(ev.get("原始摘要"))
        body = default_campus_event_body(meta_for_body)

    write_note(path, meta, body)

    # If we relocated 公众号 note onto teachin-* stem, remove old file
    if existing and prefer_new_path and existing.path != path and existing.path.is_file():
        try:
            existing.path.unlink()
        except OSError:
            pass

    return NoteCard(path=path, stem=path.stem, meta=meta, body=body)


def dedupe_campus_events(root: Path | None = None) -> dict[str, Any]:
    """Merge existing cross-source duplicates in vault; keep best note, delete extras."""
    cards = list_campus_events(root)
    buckets: list[list[NoteCard]] = []
    for card in cards:
        m = card.meta
        ck = campus_company_key(str(m.get("公司") or m.get("标题") or ""))
        start = str(m.get("开始") or "").strip()
        if not ck or not start:
            continue
        found = False
        for bucket in buckets:
            head = bucket[0].meta
            hck = campus_company_key(str(head.get("公司") or head.get("标题") or ""))
            if hck != ck and not (
                min(len(hck), len(ck)) >= 4 and (ck in hck or hck in ck)
            ):
                continue
            if str(head.get("开始") or "").strip() != start:
                continue
            if campus_places_compatible(str(m.get("地点") or ""), str(head.get("地点") or "")):
                bucket.append(card)
                found = True
                break
        if not found:
            buckets.append([card])

    merged = 0
    deleted = 0
    for bucket in buckets:
        if len(bucket) < 2:
            continue

        def rank(c: NoteCard) -> tuple:
            m = c.meta
            return (
                0 if str(m.get("外部ID") or "").strip() else 1,
                0 if str(m.get("来源链接") or "").strip() else 1,
                -_campus_place_quality(str(m.get("地点") or "")),
                c.stem,
            )

        bucket.sort(key=rank)
        keeper = bucket[0]
        meta = dict(keeper.meta)
        for other in bucket[1:]:
            meta["来源"] = merge_campus_sources(meta.get("来源"), other.meta.get("来源"))
            if not meta.get("来源链接") and other.meta.get("来源链接"):
                meta["来源链接"] = other.meta.get("来源链接")
            if not meta.get("外部ID") and other.meta.get("外部ID"):
                meta["外部ID"] = other.meta.get("外部ID")
            if _campus_place_quality(str(other.meta.get("地点") or "")) > _campus_place_quality(
                str(meta.get("地点") or "")
            ):
                meta["地点"] = other.meta.get("地点")
            if other.meta.get("关联情报") and not meta.get("关联情报"):
                meta["关联情报"] = other.meta.get("关联情报")
            if other.meta.get("形式") and not meta.get("形式"):
                meta["形式"] = other.meta.get("形式")
            co = strip_campus_event_suffix(str(meta.get("公司") or ""))
            if co:
                meta["公司"] = co
        meta["更新于"] = today_str()
        meta["核实于"] = today_str()
        body = keeper.body
        if "## 备注" in body:
            note = body.split("## 备注", 1)[-1].strip()
            meta_for_body = dict(meta)
            if note:
                meta_for_body["备注"] = note
            body = default_campus_event_body(meta_for_body)
        write_note(keeper.path, meta, body)
        merged += 1
        for other in bucket[1:]:
            if other.path != keeper.path and other.path.is_file():
                try:
                    other.path.unlink()
                    deleted += 1
                except OSError:
                    pass
    return {"ok": True, "groups_merged": merged, "files_deleted": deleted}


def upsert_campus_events_from_fetch(
    events: list[dict[str, Any]],
    root: Path | None = None,
) -> dict[str, Any]:
    created = 0
    updated = 0
    stems: list[str] = []
    before = {c.stem for c in list_campus_events(root)}
    for ev in events:
        card = upsert_campus_event(ev, root)
        stems.append(card.stem)
        if card.stem in before:
            updated += 1
        else:
            created += 1
    return {
        "ok": True,
        "created": created,
        "updated": updated,
        "total_written": len(stems),
        "stems": stems[:40],
        "dir": str(campus_events_dir(root)),
    }


def ensure_campus_events_inbox(root: Path | None = None) -> Path:
    path = campus_events_inbox_path(root)
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "type: qiuzhao-campus-inbox\n"
        "tags:\n"
        "  - 秋招\n"
        "  - 校园活动\n"
        f"更新于: {today_str()}\n"
        "---\n"
        "# 宣讲会收件箱\n\n"
        "公众号周报（西电科大就业指导服务中心）常有验证墙 / 表格截图，"
        "自动抓取失败时把链接贴到下表，或把截图放到 "
        "`秋招/03_面经/_inbox_images/宣讲会/`（也可用控制台「校园活动」入队）。\n\n"
        "| 添加于 | URL 或备注 | 状态 | 结果 |\n"
        "| --- | --- | --- | --- |\n"
    )
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def append_campus_inbox_url(url: str, root: Path | None = None) -> Path:
    path = ensure_campus_events_inbox(root)
    text = path.read_text(encoding="utf-8")
    line = f"| {today_str()} | {url.strip()} | 待处理 |  |\n"
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line, encoding="utf-8", newline="\n")
    return path


_DEFAULT_DIRECTION_KEYWORDS = (
    "Agent",
    "AI Agent",
    "Agent开发",
    "智能体",
    "大模型应用",
    "RAG",
    "Function Calling",
    "MCP",
    "Multi-Agent",
    "工具调用",
    "人工智能",
    "大模型",
    "LLM",
    "计算机",
    "网络安全",
    "AI应用",
)

_FIT_RANK = {"intel": 0, "direction": 1, "normal": 2}


def profile_direction_keywords(root: Path | None = None) -> list[str]:
    """Keywords from 求职画像筛选关键词 section; always union campus-fit defaults."""
    found: list[str] = []
    card = get_profile(root)
    if card and card.body:
        body = card.body
        for line in body.splitlines():
            s = line.strip()
            if "筛选关键词" in s or (s.startswith("`") and ("Agent" in s or "智能体" in s)):
                m = re.search(r"`([^`]+)`", s)
                if m:
                    for part in re.split(r"[,，、]", m.group(1)):
                        p = part.strip()
                        if p and p not in found:
                            found.append(p)
        for line in body.splitlines():
            if "**主攻**" in line:
                for kw in ("Agent", "LLM", "智能体", "RAG"):
                    if kw.lower() in line.lower() and kw not in found:
                        found.append(kw)
    for kw in _DEFAULT_DIRECTION_KEYWORDS:
        if kw not in found:
            found.append(kw)
    return found


def campus_event_fit_level(
    meta: dict[str, Any],
    *,
    keywords: list[str] | None = None,
    root: Path | None = None,
) -> str:
    """intel | direction | normal — never excludes; used for sort/emphasis only."""
    if meta.get("关联情报"):
        return "intel"
    kws = keywords if keywords is not None else profile_direction_keywords(root)
    blob = f"{meta.get('公司') or ''} {meta.get('标题') or ''}"
    blob_l = blob.lower()
    for kw in kws:
        k = (kw or "").strip()
        if not k:
            continue
        if k.lower() in blob_l or k in blob:
            return "direction"
    return "normal"


def campus_session_key(meta_or_item: dict[str, Any]) -> str:
    """Merge key: start|norm_place|type|form. Empty start/place → unique stem key."""
    start = str(meta_or_item.get("开始") or meta_or_item.get("start") or "").strip()
    place = str(meta_or_item.get("地点") or meta_or_item.get("place") or "").strip()
    et = str(meta_or_item.get("活动类型") or meta_or_item.get("event_type") or "").strip()
    form = str(meta_or_item.get("形式") or meta_or_item.get("form") or "").strip()
    if not start or not place:
        stem = str(meta_or_item.get("stem") or meta_or_item.get("外部ID") or id(meta_or_item))
        return f"singleton|{stem}"
    return f"{start}|{normalize_campus_place(place)}|{et}|{form}"


def campus_identity_key(meta_or_item: dict[str, Any]) -> str:
    """Cross-source identity: company+start+norm_place."""
    company = str(
        meta_or_item.get("公司")
        or meta_or_item.get("company")
        or meta_or_item.get("标题")
        or meta_or_item.get("title")
        or ""
    )
    start = str(meta_or_item.get("开始") or meta_or_item.get("start") or "").strip()
    place = str(meta_or_item.get("地点") or meta_or_item.get("place") or "").strip()
    ck = campus_company_key(company)
    return f"{ck}|{start}|{normalize_campus_place(place)}"


def campus_event_bucket(meta: dict[str, Any], *, now: datetime | None = None) -> str:
    """today / tomorrow / week / later / past."""
    now = now or datetime.now()
    start = parse_dt(meta.get("开始"))
    status = str(meta.get("状态") or "")
    if status == "已取消":
        return "past"
    if not start:
        return "later" if status != "已举办" else "past"
    day = start.date()
    today = now.date()
    if day < today or status == "已举办":
        return "past"
    if day == today:
        return "today"
    tomorrow = today + timedelta(days=1)
    if day == tomorrow:
        return "tomorrow"
    week_end = today + timedelta(days=(6 - today.weekday()))
    if day <= week_end:
        return "week"
    return "later"


def collect_campus_calendar_events(
    root: Path | None = None,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for card in list_campus_events(root):
        dt = parse_dt(card.meta.get("开始"))
        if not dt:
            continue
        if start and dt < start:
            continue
        if end and dt > end:
            continue
        label = str(card.meta.get("活动类型") or "校园活动")
        events.append(
            {
                "when": dt.isoformat(timespec="minutes"),
                "when_fmt": fmt_dt(dt),
                "label": label,
                "company": str(card.meta.get("公司") or card.meta.get("标题") or card.stem),
                "position": str(card.meta.get("地点") or card.meta.get("形式") or ""),
                "stem": card.stem,
                "kind": "campus",
                "source": "campus",
                "field": "开始",
            }
        )
    return events


def collect_all_calendar_events(
    root: Path | None = None,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for e in collect_progress_events(root):
        if start and e.when < start:
            continue
        if end and e.when > end:
            continue
        events.append(
            {
                "when": e.when.isoformat(timespec="minutes"),
                "when_fmt": fmt_dt(e.when),
                "label": e.label,
                "company": e.company,
                "position": e.position,
                "stem": e.stem,
                "field": e.field,
                "kind": "interview",
                "source": "progress",
            }
        )
    for d in collect_deadline_events(root):
        dt = parse_dt(d["when"])
        if not dt:
            continue
        if start and dt < start:
            continue
        if end and dt > end:
            continue
        events.append(d)
    events.extend(collect_campus_calendar_events(root, start=start, end=end))
    events.sort(key=lambda x: x["when"])
    return events


def note_card_to_dict(card: NoteCard, *, include_body: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "stem": card.stem,
        "rel": card.rel,
        "meta": _jsonable_meta(card.meta),
    }
    if include_body:
        data["body"] = card.body
    return data


def _jsonable_meta(meta: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, datetime):
            out[k] = fmt_dt(v)
        elif isinstance(v, date):
            out[k] = v.isoformat()
        elif isinstance(v, Path):
            out[k] = str(v)
        else:
            out[k] = v
    return out


def infer_mianshi_status(card: NoteCard) -> str:
    body = (card.body or "").strip()
    if "（待填写）" in body or "## 复盘\n\n（待填写）" in body:
        return "待复盘"
    if "| 问题 |" in body or re.search(r"^\d+[\.\)、]", body, re.M):
        reflection = ""
        if "## 反思" in body:
            reflection = body.split("## 反思", 1)[-1]
            if "##" in reflection:
                reflection = reflection.split("##", 1)[0]
        if reflection.strip() and not re.match(
            r"^[\s\-\*]*答得好的[：:].*卡住的点[：:].*知识盲区[：:]\s*$",
            reflection.strip(),
            re.S,
        ):
            # has some content beyond empty template bullets
            filled = any(
                line.strip() and not line.strip().startswith("-") or (
                    line.strip().startswith("-") and len(line.strip()) > 8
                    and not line.strip().endswith("：")
                    and not line.strip().endswith(":")
                )
                for line in reflection.splitlines()
            )
            if filled and "答得好的：" not in reflection.replace("- 答得好的：", "").strip():
                pass
        return "复盘中"
    return "待复盘"
