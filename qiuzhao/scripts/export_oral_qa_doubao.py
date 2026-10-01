# -*- coding: utf-8 -*-
"""从 09_口述题答 卡片导出 doubao_bank JSON。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"E:/obsidian/My_docs/秋招/09_口述题答")
OUT = ROOT / "_导出"
OUT.mkdir(parents=True, exist_ok=True)


def parse_card(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"')
            body = parts[2]

    def sec(name: str) -> str:
        m = re.search(rf"## {re.escape(name)}\n+(.*?)(?=\n## |\Z)", body, re.S)
        if not m:
            return ""
        s = m.group(1).strip()
        s = re.sub(r"^>\s?", "", s, flags=re.M)
        return s.strip()

    qid = fm.get("qid") or path.stem.split("-")[0]
    related_raw = fm.get("related", "[]")
    try:
        related_list = json.loads(related_raw.replace("'", '"')) if related_raw.startswith("[") else []
    except json.JSONDecodeError:
        related_list = []

    question = sec("规范题干").split("\n")[0].strip()
    return {
        "id": qid,
        "question": question,
        "answer_30s": sec("30 秒骨架").lstrip("> ").strip(),
        "answer_90s": sec("90 秒展开"),
        "tags": [fm.get("主题", path.parent.name)],
        "related": related_list,
        "coverage": fm.get("覆盖", ""),
        "path": path.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    cards: list[dict] = []
    for p in sorted(ROOT.rglob("*.md")):
        if p.name.startswith("_") or "_导出" in p.parts:
            continue
        c = parse_card(p)
        if c["id"] and c["question"]:
            cards.append(c)

    (OUT / "doubao_bank_all.json").write_text(
        json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for theme in ["Agent", "RAG", "行为面"]:
        subset = [c for c in cards if theme in c["tags"] or c["path"].startswith(theme + "/")]
        (OUT / f"doubao_bank_{theme}.json").write_text(
            json.dumps(subset, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    company_ids = {
        "字节跳动": [
            "AGT-01", "AGT-02", "AGT-10", "AGT-12", "AGT-20", "AGT-21", "RAG-11",
            "AGT-40", "AGT-41", "RAG-10", "RAG-13", "RAG-12", "RAG-03", "RAG-02",
            "AGT-03", "BEH-01", "BEH-02",
        ],
        "阿里巴巴": [
            "AGT-21", "AGT-50", "AGT-20", "AGT-11", "RAG-01", "RAG-03", "RAG-10",
            "RAG-13", "RAG-11", "AGT-03", "AGT-01", "AGT-02", "AGT-23", "RAG-02",
            "AGT-40", "BEH-01", "BEH-02",
        ],
        "美团": [
            "AGT-10", "AGT-11", "AGT-12", "AGT-20", "AGT-23", "AGT-21", "AGT-02",
            "RAG-11", "AGT-01", "AGT-03", "AGT-40", "AGT-41", "AGT-50", "RAG-02",
            "BEH-01", "BEH-02",
        ],
    }
    by_id = {c["id"]: c for c in cards}
    for name, ids in company_ids.items():
        subset = [by_id[i] for i in ids if i in by_id]
        (OUT / f"doubao_bank_{name}.json").write_text(
            json.dumps(subset, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    readme = OUT / "_说明.md"
    readme.write_text(
        "\n".join(
            [
                "---",
                "type: qiuzhao-guide",
                "tags: [秋招, 导出]",
                "更新于: 2026-08-10",
                "---",
                "# 口述题答导出",
                "",
                "字段：`id` / `question` / `answer_30s` / `answer_90s` / `tags` / `related` / `coverage` / `path`。",
                "",
                "用途：手工导入豆包题库，或打印前筛选。**本期不接豆包 API**。",
                "",
                "重新生成：`py -3.12 qiuzhao/tmp/export_oral_qa_doubao.py`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"cards={len(cards)} files={len(list(OUT.glob('*.json')))}")


if __name__ == "__main__":
    main()
