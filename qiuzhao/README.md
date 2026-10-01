# 秋招智能管理助手（配套仓库）

**混合模式**：本机 Web SPA（日常）+ Obsidian（复习）+ Cursor Agent（深挖）。

数据真相源仍在 Obsidian 库 `秋招/`；本仓库存放 Skill、控制台、抓取/ICS 脚本与修改日志。

## 快速开始（推荐）

```powershell
cd d:\AgentProjects\work
py -3.12 -m pip install -r qiuzhao\scripts\requirements.txt
cd qiuzhao\web; npm install; npm run build; cd ..\..
qiuzhao\console\run.ps1
```

打开 http://127.0.0.1:8765

| 页 | 作用 |
| --- | --- |
| 职位信息 | 浏览情报卡；按档次/岗位族/状态/优先级筛选；「练手视图」；加入投递 |
| 我的秋招 | 流程条、改状态/时间（写回 Obsidian） |
| 校园活动 | 西电宣讲会/双选会；就业网立即刷新；公众号周报补录 |
| 面试日历 | 月历 + 冲突 + 校园活动 + 导出 ICS |
| 面试复盘 | 题目/题库/总结写回 `03_面经` |
| 更多 | Agent 入队、学习任务、旧版入口 |

| 场景 | 入口 | 地址 |
| --- | --- | --- |
| 日常成品 | 桌面 `Qiuzhao-Console` / `start-console.bat` | http://127.0.0.1:8765 |
| 改界面热更新 | 桌面 `Qiuzhao-Console-Dev` / `start-console-dev.bat` | http://127.0.0.1:5173（Vite HMR + API `--reload`） |

刷新桌面图标：`qiuzhao\console\create-desktop-shortcut.ps1`  
旧版 Jinja：http://127.0.0.1:8765/legacy

有待处理时，打开 Cursor 说一句：

```text
处理控制台任务
```

另外两句快捷口令：聊天贴 URL；`每日情报更新`。

## Cursor 口令（仅 3 句）

| 说法 | 作用 |
| --- | --- |
| `处理控制台任务` | 消费 `秋招/07_任务/agent队列.md` |
| 贴 `https://...` | 快捷链接入库 |
| `每日情报更新` | 日更（也可控制台入队） |

## 面试准备 Skills（专享）

对某一公司某一岗位做材料时，用仓库内 Skill（`.cursor/skills/`）：

| Skill | 作用 |
| --- | --- |
| `qiuzhao-interview-prep` | 主控：全流程编排与验收 |
| `qiuzhao-job-analysis` | 岗位分析 → `08_面试准备/{公司}-{岗位}/` |
| `qiuzhao-mianshi-search` | 面经搜寻汇总（来源链接库书签 → 多方校验；清洗/分类/去重） |
| `qiuzhao-interview-answers` | 自我介绍 + 逐题回答（默认 MD）；**强制读 DORA 面试手册**，可选核对代码 |
| `qiuzhao-oral-qa` | 默认按需 `润色口述`（一次一题）；必练短名单 + 答法模版；模拟卷 / 豆包 JSON |
| `qiuzhao-answer-clean` | 同步答案框架（每节一例）+ 原稿→标准答清洗；`06_知识库/面经答案/` |

示例口令：

```text
公司：某某科技
岗位：Agent 应用开发
执行阶段：全流程
```

练口（推荐）：`润色口述：AGT-10`（要点可空）。出卷：`出模拟卷：字节跳动-Agent开发工程师-豆包`。批量仅明确点名时使用。  
答案框架：`同步答案框架：全部`（或指定公司）。书面清洗：`清洗答案：阿里巴巴` / `继续清洗：阿里巴巴`。

事实源：`00_画像/求职画像.md`；JD：`02_情报库`；阶段三项目深度：`06_知识库/DORA面试手册/`（≡ DORA 仓 `docs/interview-manual/`）；口语 SSOT：`09_口述题答/`（必练见 `_索引`，结构见 `_答法模版`）；公司标准答：`06_知识库/面经答案/`。与「处理控制台任务」分工不同，见各 Skill 正文。

## 抓取 CLI

```powershell
$env:QIUZHAO_VAULT = "E:\obsidian\My_docs"
py -3.12 -m playwright install chromium
py -3.12 qiuzhao\scripts\fetch_url.py --url "https://example.com/" --out raw.json
py -3.12 qiuzhao\scripts\fetch_fangzhou.py --out fangzhou.json --limit 30
py -3.12 qiuzhao\scripts\fetch_nowcoder_schedule.py --batch 1203,1206,1210 --update-source-links
```

质量门：无 JD 不入库；微信墙丢弃；不要实习岗；博士硬门槛（硕士不可投）直接剔除。

## Vault IO

`qiuzhao/scripts/vault_io.py` — 控制台与 Skill 共用读写进度/情报/队列/学习任务。

## 开发文档

见 `qiuzhao/DEV.md`。Obsidian 侧说明：`秋招/使用说明.md`、`秋招/文件夹与职责说明.md`。
