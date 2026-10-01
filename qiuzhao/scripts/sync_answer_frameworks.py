# -*- coding: utf-8 -*-
"""从公司面经题库同步生成答案原稿框架 + 标准答进度壳。

要点：
- 题库分节是标签行（#RAG），不是 Markdown 标题；跳转用 [[题库#^qz-…]]（必须带 #^）
- 原稿：分节大标题下挂一条题库块链；每题实例不再写题干/题库链接

用法：
  py -3.12 qiuzhao/scripts/sync_answer_frameworks.py
  py -3.12 qiuzhao/scripts/sync_answer_frameworks.py --company 阿里巴巴
"""
from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from vault_io import vault_root

BANK_DIR = Path("秋招/06_知识库/公司面经摘录")
ANSWER_DIR = Path("秋招/06_知识库/面经答案")

# 题库分节名 → 节缩写（优先）
SECTION_ALIASES: dict[str, str] = {
    "行为面": "行为",
    "RAG": "RAG",
    "RAG与检索": "RAG",
    "RAG与工具": "RAG工具",
    "Agent": "Agent",
    "Multi-Agent": "MultiAgent",
    "上下文管理": "上下文",
    "工具": "工具",
    "工具与可靠性": "工具",
    "规划与Prompt": "规划",
    "幻觉与可靠性": "幻觉",
    "评测": "评测",
    "评测与可靠性": "评测",
    "评测与上下文": "评测",
    "安全与沙箱": "安全",
    "系统设计": "系统",
    "项目深挖": "项目",
    "手撕": "手撕",
    "架构与Agent设计": "架构",
    "Prompt与上下文工程": "Prompt",
    "工程与推理": "工程推理",
    "工程八股": "工程",
    "工程基础": "工程基础",
    "Agent架构": "Agent架构",
    "Agent框架与架构": "Agent框架",
    "Agent基础与业务理解": "Agent基础",
    "Agent控制流": "控制流",
    "Agent执行与编排": "编排",
    "Skill与MCP与工具": "Skill",
    "规划与范式": "范式",
    "上下文工程": "上下文",
    "Memory": "Memory",
    "Trace可观测与评测": "Trace",
    "可观测与评测": "可观测",
    "部署性能与训练工程": "部署",
    "场景题": "场景",
    "场景与评测": "场景",
    "场景设计与评测": "场景",
    "前端与流式": "前端",
    "项目与业务Agent": "业务Agent",
    "系统与内存": "系统内存",
    "LLM推理与并行": "推理",
    "网络": "网络",
    "基座原理": "基座",
    "语音与ASR": "语音",
}

# 中文分节 → 可读块 ID（Obsidian 块 ID 仅 ASCII）
SECTION_BLOCK_ALIASES: dict[str, str] = {
    "行为面": "behavior",
    "行为": "behavior",
    "上下文管理": "context",
    "上下文": "context",
    "上下文工程": "context",
    "工具": "tools",
    "工具与可靠性": "tools",
    "规划与Prompt": "planning",
    "规划": "planning",
    "规划与范式": "paradigm",
    "幻觉与可靠性": "hallucination",
    "幻觉": "hallucination",
    "评测": "eval",
    "评测与可靠性": "eval",
    "评测与上下文": "eval",
    "安全与沙箱": "sandbox",
    "安全": "sandbox",
    "系统设计": "system",
    "系统": "system",
    "项目深挖": "project",
    "项目": "project",
    "手撕": "coding",
    "架构与Agent设计": "arch",
    "架构": "arch",
    "工程八股": "eng",
    "工程": "eng",
    "工程基础": "eng-base",
    "工程与推理": "eng-reason",
    "场景题": "scenario",
    "场景与评测": "scenario",
    "场景设计与评测": "scenario",
    "场景": "scenario",
    "前端与流式": "frontend",
    "网络": "network",
    "基座原理": "foundation",
    "语音与ASR": "asr",
    "系统与内存": "sysmem",
    "LLM推理与并行": "infer",
    "部署性能与训练工程": "deploy",
    "可观测与评测": "obs",
    "项目与业务Agent": "biz-agent",
    "Prompt与上下文工程": "prompt",
    "Agent基础与业务理解": "agent-base",
    "Agent控制流": "control",
    "Agent执行与编排": "orchestrate",
    "Skill与MCP与工具": "skill",
    "Agent框架与架构": "agent-fw",
    "Agent架构": "agent-arch",
}

PLACEHOLDER_HINT = "（在此粘贴未修剪答案；同节第 N 题复制本块，只改标题序号）"
EMPTY_MARKERS = {
    "",
    PLACEHOLDER_HINT,
    "（在此粘贴未修剪答案；同节第 N 题复制本块改标题序号即可）",
    "（粘贴原始答案…）",
    "（粘贴答案；同节第 N 题复制本块改序号）",
    "（清洗后的标准答）",
    "（清洗后的标准答正文）",
}

# 分节标签行：#RAG / #Agent 可选尾随旧块 ID
SECTION_LINE_RE = re.compile(
    r"^(#(?!\s)([^\s^]+(?:[ \t]+[^\s^]+)*))(?:[ \t]+\^([A-Za-z0-9_-]+))?[ \t]*$"
)
BLOCK_ID_RE = re.compile(r"\^[A-Za-z0-9_-]+")


@dataclass
class Question:
    index: int
    stem: str


@dataclass
class Section:
    name: str
    abbr: str
    block_id: str = ""
    questions: list[Question] = field(default_factory=list)


def today() -> str:
    return date.today().isoformat()


def section_abbr(name: str) -> str:
    name = name.strip()
    if name in SECTION_ALIASES:
        return SECTION_ALIASES[name]
    for sep in ("与", "和", "/"):
        if sep in name:
            name = name.split(sep, 1)[0].strip()
            break
    name = re.sub(r"\s+", "", name)
    return name[:8] if len(name) > 8 else name


def section_block_id(name: str, abbr: str) -> str:
    """Obsidian 块 ID 仅允许字母数字与 -_。"""
    name = name.strip()
    abbr = abbr.strip()
    for key in (name, abbr):
        if key in SECTION_BLOCK_ALIASES:
            return f"qz-{SECTION_BLOCK_ALIASES[key]}"
    ascii_part = re.sub(r"[^A-Za-z0-9_-]+", "", abbr or name)
    if ascii_part and len(ascii_part) >= 2:
        return f"qz-{ascii_part}"
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    return f"qz-{digest}"


def qid(abbr: str, index: int) -> str:
    return f"A-{abbr}-{index}"


def _strip_block_id_from_section_name(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"[ \t]+\^[A-Za-z0-9_-]+$", "", raw).strip()
    return raw


def parse_bank(path: Path) -> tuple[str, list[Section]]:
    """返回 (公司名, 分节列表)。"""
    text = path.read_text(encoding="utf-8")
    stem = path.stem
    company = stem.removesuffix("-Agent面经题库")
    if company == stem:
        company = stem.split("-")[0]

    if text.startswith("---"):
        parts = text.split("---", 2)
        body = parts[2] if len(parts) >= 3 else text
    else:
        body = text

    sections: list[Section] = []
    current: Section | None = None

    for line in body.splitlines():
        stripped = line.strip()
        m = SECTION_LINE_RE.match(stripped)
        if m:
            raw = _strip_block_id_from_section_name(m.group(2))
            if "面经题库" in raw or raw == company:
                continue
            abbr = section_abbr(raw)
            bid = section_block_id(raw, abbr)
            current = Section(name=raw, abbr=abbr, block_id=bid)
            sections.append(current)
            continue
        m2 = re.match(r"^##\s+(.+)$", stripped)
        if m2 and current is None:
            raw = _strip_block_id_from_section_name(m2.group(1))
            if "面经题库" not in raw:
                abbr = section_abbr(raw)
                current = Section(
                    name=raw, abbr=abbr, block_id=section_block_id(raw, abbr)
                )
                sections.append(current)
            continue
        if current is None:
            continue
        qm = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if qm:
            stem_q = qm.group(2).strip()
            stem_q = re.sub(r"\s*[→√].*$", "", stem_q).strip()
            stem_q = re.sub(r"\s*\[\[.*?\]\].*$", "", stem_q).strip()
            current.questions.append(Question(index=int(qm.group(1)), stem=stem_q))

    return company, [s for s in sections if s.questions or s.name]


def ensure_bank_block_ids(path: Path, sections: list[Section]) -> bool:
    """给题库分节标签行写入稳定 ^qz-… 块 ID；返回是否改写。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    wanted = {s.name: s.block_id for s in sections}
    changed = False
    out: list[str] = []

    for line in lines:
        stripped = line.strip()
        m = SECTION_LINE_RE.match(stripped)
        if not m:
            out.append(line)
            continue
        name = _strip_block_id_from_section_name(m.group(2))
        if name not in wanted:
            out.append(line)
            continue
        bid = wanted[name]
        # 保留原标签写法（#RAG / #Agent），只规范块 ID
        tag = m.group(1).rstrip()
        new_line = f"{tag} ^{bid}"
        if new_line != stripped:
            changed = True
        out.append(new_line)

    if changed:
        path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return changed


def extract_answer_bodies(text: str) -> dict[str, str]:
    """提取 ### A-… 块中已有实质答案正文（去掉题库/题干/占位）。"""
    filled: dict[str, str] = {}
    pattern = re.compile(r"^### (A-[^\n]+)\n(.*?)(?=^### A-|\Z)", re.M | re.S)
    for m in pattern.finditer(text):
        key = m.group(1).strip()
        body = m.group(2).strip()
        rest = re.sub(r"^题库：.*$", "", body, flags=re.M)
        rest = re.sub(r"^\*\*题干\*\*.*$", "", rest, flags=re.M)
        rest = rest.strip()
        if not rest or rest in EMPTY_MARKERS:
            continue
        if rest.startswith("<!--"):
            continue
        if "在此粘贴未修剪答案" in rest or rest.startswith("（粘贴答案"):
            continue
        filled[key] = rest
    return filled


def parse_progress_status(text: str) -> dict[str, tuple[str, str]]:
    """题号 -> (状态, 更新于)。"""
    out: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        m = re.match(
            r"^\|\s*(A-[^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
            line,
        )
        if not m:
            continue
        q = m.group(1).strip()
        if q in ("题号", "---") or q.startswith("-"):
            continue
        status = m.group(3).strip()
        updated = m.group(4).strip()
        out[q] = (status, updated)
    return out


def extract_std_answer_blocks(text: str) -> dict[str, str]:
    """标准答已处理正文块（整块保留，含标题）。"""
    if "## 答案正文" in text:
        body = text.split("## 答案正文", 1)[1]
    else:
        body = text
    filled_bodies = extract_answer_bodies(body)
    # 重建整块，便于 preserve 写入
    pattern = re.compile(r"^### (A-[^\n]+)\n(.*?)(?=^### A-|\Z)", re.M | re.S)
    out: dict[str, str] = {}
    for m in pattern.finditer(body):
        key = m.group(1).strip()
        if key in filled_bodies:
            out[key] = m.group(0).rstrip()
    return out


def short_stem(stem: str, limit: int = 24) -> str:
    s = re.sub(r"\s+", " ", stem).strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def bank_block_link(company: str, section: Section) -> str:
    # Obsidian 跨笔记块链必须是 [[path#^id]]：
    # - 禁止 [[path^id]]（缺 #，会被当成另一条笔记名）
    # - 禁止 [[path#标签]]（#RAG 是标签不是标题）
    path = f"秋招/06_知识库/公司面经摘录/{company}-Agent面经题库"
    return f"[[{path}#^{section.block_id}|题库 · {section.name}]]"


def build_raw_framework(
    company: str,
    sections: list[Section],
    preserve_bodies: dict[str, str],
) -> str:
    lines: list[str] = [
        "---",
        "type: qiuzhao-answer-raw",
        f"关联公司: {company}",
        f"关联题库: {company}-Agent面经题库",
        f"关联标准答: {company}-Agent面经答案",
        f"更新于: {today()}",
        "tags:",
        "  - 秋招",
        "  - 面经答案",
        "  - 原稿",
        f"  - {company}",
        "---",
        f"# {company}-Agent答案原稿",
        "",
        f"题库：[[秋招/06_知识库/公司面经摘录/{company}-Agent面经题库|{company}-Agent面经题库]]  ",
        f"标准答：[[秋招/06_知识库/面经答案/{company}-Agent面经答案|{company}-Agent面经答案]]",
        "",
        "> 每类题型仅预置 **第 1 题** 空壳；同节其余题复制 `###` 块并改序号。",
        "> **不要**在实例里复写题干——对照大标题下的题库块链看题即可。",
        f"> 题库新增分节时执行：`同步答案框架：{company}`（会给分节标签补 `^qz-…` 块 ID）。",
        "",
    ]
    for sec in sections:
        if not sec.questions:
            continue
        first = sec.questions[0]
        key = qid(sec.abbr, first.index)
        lines.append(f"## {sec.name}")
        lines.append("")
        lines.append(f"题库：{bank_block_link(company, sec)}")
        lines.append("")
        lines.append(f"### {key}")
        lines.append("")
        if key in preserve_bodies:
            lines.append(preserve_bodies[key])
        else:
            lines.append(PLACEHOLDER_HINT)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_std_shell(
    company: str,
    sections: list[Section],
    old_status: dict[str, tuple[str, str]],
    preserve_blocks: dict[str, str],
) -> str:
    rows: list[str] = []
    for sec in sections:
        for q in sec.questions:
            key = qid(sec.abbr, q.index)
            default_status = "跳过" if sec.abbr == "手撕" or sec.name == "手撕" else "无原稿"
            default_updated = today() if default_status == "跳过" else ""
            if key in old_status:
                status, updated = old_status[key]
                if key in preserve_blocks and status != "已处理":
                    status, updated = "已处理", today()
            else:
                status, updated = default_status, default_updated
            rows.append(
                f"| {key} | {short_stem(q.stem)} | {status} | {updated} |"
            )

    lines: list[str] = [
        "---",
        "type: qiuzhao-answer-std",
        f"关联公司: {company}",
        f"关联题库: {company}-Agent面经题库",
        f"关联原稿: {company}-Agent答案原稿",
        f"更新于: {today()}",
        "tags:",
        "  - 秋招",
        "  - 面经答案",
        "  - 标准答",
        f"  - {company}",
        "---",
        f"# {company}-Agent面经答案",
        "",
        f"题库：[[秋招/06_知识库/公司面经摘录/{company}-Agent面经题库|题库]] · "
        f"原稿：[[秋招/06_知识库/面经答案/{company}-Agent答案原稿|原稿]]",
        "",
        f"Skill：`qiuzhao-answer-clean` · 口令 `清洗答案：{company}` / `继续清洗：{company}` / "
        f"`同步答案框架：{company}`",
        "",
        "> 进度表按题库全量列出；正文在清洗后按 `### A-…` 写入。",
        "> 回链题库分节请用块 ID：`[[…题库#^qz-…]]`（分节是标签行，不是标题）。",
        "",
        "## 进度表",
        "",
        "| 题号 | 题干摘要 | 状态 | 更新于 |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
        "---",
        "",
        "## 答案正文",
        "",
    ]
    if preserve_blocks:
        for key in sorted(preserve_blocks.keys()):
            lines.append(preserve_blocks[key])
            lines.append("")
    else:
        lines.append("（有原稿并执行清洗后，按 `### A-…` 写入。）")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def sync_company(vault: Path, bank_path: Path) -> tuple[str, int, int, bool]:
    company, sections = parse_bank(bank_path)
    # 先写块 ID，再解析一次确保一致
    bank_changed = ensure_bank_block_ids(bank_path, sections)
    if bank_changed:
        company, sections = parse_bank(bank_path)

    answer_dir = vault / ANSWER_DIR
    answer_dir.mkdir(parents=True, exist_ok=True)

    raw_path = answer_dir / f"{company}-Agent答案原稿.md"
    std_path = answer_dir / f"{company}-Agent面经答案.md"

    preserve_raw: dict[str, str] = {}
    if raw_path.exists():
        preserve_raw = extract_answer_bodies(raw_path.read_text(encoding="utf-8"))

    old_status: dict[str, tuple[str, str]] = {}
    preserve_std: dict[str, str] = {}
    if std_path.exists():
        old_text = std_path.read_text(encoding="utf-8")
        old_status = parse_progress_status(old_text)
        preserve_std = extract_std_answer_blocks(old_text)

    raw_path.write_text(build_raw_framework(company, sections, preserve_raw), encoding="utf-8")
    std_path.write_text(
        build_std_shell(company, sections, old_status, preserve_std), encoding="utf-8"
    )

    n_sec = sum(1 for s in sections if s.questions)
    n_q = sum(len(s.questions) for s in sections)
    return company, n_sec, n_q, bank_changed


def list_bank_files(vault: Path) -> list[Path]:
    d = vault / BANK_DIR
    files = sorted(d.glob("*-Agent面经题库.md"))
    return [p for p in files if "牛客综摘" not in p.name]


def main() -> None:
    parser = argparse.ArgumentParser(description="同步公司答案原稿框架与标准答进度壳")
    parser.add_argument("--company", help="仅同步指定公司（如 阿里巴巴）")
    parser.add_argument(
        "--vault",
        default=None,
        help="Obsidian vault 根目录（默认 QIUZHAO_VAULT / vault_io）",
    )
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else vault_root()
    banks = list_bank_files(vault)
    if args.company:
        banks = [p for p in banks if p.stem.startswith(f"{args.company}-")]
        if not banks:
            raise SystemExit(f"未找到公司题库：{args.company}")

    junk = vault / ANSWER_DIR / "未命名.md"
    if junk.exists():
        junk.unlink()
        print(f"已删除 {junk}")

    print(f"vault={vault}")
    for bank in banks:
        company, n_sec, n_q, bank_changed = sync_company(vault, bank)
        flag = " +题库块ID" if bank_changed else ""
        print(f"OK {company}: {n_sec} 节 / {n_q} 题 → 原稿(每节一例) + 标准答{flag}")


if __name__ == "__main__":
    main()
