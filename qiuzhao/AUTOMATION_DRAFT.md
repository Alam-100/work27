# Cursor 每日秋招扫描 Automation（可选草稿）

本文件是**草稿说明**，不会自动创建 Automation。若要开启：

1. 打开 Cursor → Automations
2. 新建定时任务（建议每天 09:00）
3. 指令粘贴如下：

```text
使用 qiuzhao-assistant Skill。
1. 读取 Obsidian 库 秋招/05_投递进度 下所有 type=qiuzhao-progress 笔记。
2. 扫描未来 14 天的测评时间 / 笔试时间 / 一面 / 二面 / 三面 / HR面。
3. 读取 秋招/02_情报库 的投递截止；标记核实于超过 14 天的需再核实。
4. 按 Skill 冲突规则更新 秋招/01_看板/本周日程与冲突.md 的「冲突告警」区块。
5. 列出「明日」笔试/面试/截止清单。
6. 跑西电校园活动刷新：
   py -3.12 qiuzhao/scripts/fetch_xidian_events.py --write-vault --update-source-links
   （或确认控制台已用计划任务 schedule-events-refresh.ps1）
7. 若时间字段有变，提醒用户运行 qiuzhao/scripts/export_ics.py 刷新 ICS。
不要创建无关笔记；改库后在 秋招/04_情报/来源日志.md 追加一行日更摘要。
```

4. 工具：需要能访问 Obsidian MCP（若 Automation 无法用本地 MCP，则改为每天在对话里说「扫描冲突」）。

## 西电校园活动（本机计划任务，推荐）

就业网场次更新快，建议用本机脚本而不是只靠 Cursor Automation：

- 脚本：`qiuzhao/console/schedule-events-refresh.ps1`
- 说明：`qiuzhao/console/schedule-events-refresh.md`
- 建议每天 08:00 / 18:00；**默认未注册**，需你确认后再加 Windows 计划任务

公众号周报不能稳定自动抓（验证墙/截图表）；用 SPA「校园活动」补录入队或截图 `_inbox_images/宣讲会/`。

状态：默认**未开启**，需你确认后配置。
