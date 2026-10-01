---
name: dora-manual-obsidian-bridge
description: >-
  Bridge DORA interview-manual with Obsidian via NTFS junction and on-demand
  research notes under 资料/. Use when user says 建联结, 检查手册联结, 给XX建研究桩,
  这个我要查, 把资料整理进手册, absorb research, or dora manual obsidian.
---

# DORA 面试手册 ↔ Obsidian 桥接

与 DORA 仓库 Skill **`dora-interview-manual-sync`** 分工：

| Skill | 职责 |
|-------|------|
| `dora-interview-manual-sync`（DORA 仓） | 面经题 → 模块 `06`/`07` |
| **本 Skill**（work 仓） | 目录联结体检；**用户点名**后建研究桩；`资料/` 消化回填 |

手册物理路径（Git SSOT）：

`D:\AgentProjects\DORA-AI-Powered-Virtual-Personal-Assistant\docs\interview-manual`

Obsidian 入口（本机 **Junction**，与 Git 同 inode，**不是拷贝、无需手动同步**）：

`E:\obsidian\My_docs\秋招\06_知识库\DORA面试手册`

研究笔记：`docs/interview-manual/{模块}/资料/`（已 gitignore；**用户自管**，Agent 默认不碰）。

写作标准 / 冻结门禁：DORA 仓 `docs/interview-manual/00-template.md`。  
文件角色：`docs/interview-manual/MAP.md`。

**MCP 分工**：用 MCP 读联结外的面经/主题卡；**禁止**用 MCP 维护「第二份」手册 SSOT（改手册走仓库路径或 Obsidian 同一目录即可）。

---

## 0. 研究桩纪律（强制）

- **默认不建桩**。Agent 不得批量预建 `资料/*.md`，不得把空桩当作业清单。  
- 仅当用户说「这个我要查 / 给 XX 建研究桩」或明确点名缺口时再建。  
- 标题用**面试官口吻**（例：`面试追问-多跳为何不用知识图谱`）；文件名可带 `G-xxx-` 前缀。  
- 「研究提示」最多 **1–2 条追问句**，禁止展开成 HNSW/ColBERT/版面引擎等底层实验大纲。  
- 特别底层主题（向量库调参、晚交互存储倍数、逐工具准确率表）→ **不建桩**，正文一句话划界即可。

---

## 1. 联结体检 / 补建

触发：`检查手册联结` / `建联结`

本步是 **体检/补建联结**，不是「把 Obsidian 内容同步拷贝进仓库」。联结正常时两边已是同一目录。

1. 确认目标为 Junction 且 `resolve` 指向 DORA `docs/interview-manual`（可用 Python `Path(...).resolve()` 或 `dir /AL`）。  
2. 若不存在：

```powershell
cmd /c mklink /J "E:\obsidian\My_docs\秋招\06_知识库\DORA面试手册" "D:\AgentProjects\DORA-AI-Powered-Virtual-Personal-Assistant\docs\interview-manual"
```

3. 若路径被普通目录占用：先停手报告，勿静默删除用户文件。  
4. Vault 根以 `QIUZHAO_VAULT` / `qiuzhao/scripts/vault_io.py` 的 `vault_root()` 为准（默认 `E:\obsidian\My_docs`）。

---

## 2. 建研究桩（仅用户触发）

触发：`给 XX 建研究桩` / `这个我要查`

1. 确认主题满足模板三条（面试官视角 + 正文已够答 + 用户确认）。  
2. 在对应模块 `资料/` 下新建笔记，至少含：

```markdown
# 面试追问-{口语化主题}

相关手册：[[深挖篇文件名不含扩展名]] · [[07-project-gaps]]
缺口 ID：`G-xxx`（若有）

## 追问句（最多 2 条）
1. 面试官可能怎么追问？
2. 需要哪一类可复述对比（禁止编造数字）？

## 待填笔记
（用户粘贴资料）

## 吸收状态
- 状态：待填
- 已吸收于：—
```

3. 可在正式文档对应处加一行 `🔎 **待查证（用户点名）**：[[笔记标题]]`。  
4. 禁止把原始长摘录提交进 Git。

---

## 3. 消化回填（资料 → 正式文档）

触发：`把 XX 资料整理进手册` / `absorb research`

1. 读 `资料/{笔记}.md` 的「待填笔记」；若仍空 → 提示用户先填。  
2. 对照 DORA 仓库真实代码（勿编造已落地能力）。  
3. 在目标深挖篇 / `07` 中：用机制向段落**单点**加厚；遵守模板冻结门禁（禁止借机重写整篇）。  
4. 笔记末改为：`已吸收于 YYYY-MM-DD，见正文 §x`；状态=`已吸收`。  
5. 在 DORA 仓写 changelog，询问后 commit（不 push）。  
6. 不把 `资料/` 原始全文复制进正式文档。

---

## 4. 明确不做

- 不镜像复制整份手册到 vault（联结即同一份；禁止制造第二份 SSOT）。  
- 不擅自改 vault 其它秋招笔记。  
- 不编造基准数字；资料不足就保留待查证并说明缺什么。  
- 不把 `07`「候选加分查证」表自动建成空桩文件。  
- 未经用户点名：不重写已提密深挖、不批量改「为何不做」。

## 5. 回报

- 联结是否 OK  
- 新建/更新的桩或回填的文件列表  
- 是否需用户在 Obsidian 刷新
