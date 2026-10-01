# 西电校园活动定时刷新（可选）

本脚本只负责**跑一遍**就业网抓取并写入 Obsidian `秋招/10_校园活动/`。
默认**不**自动注册 Windows 计划任务；需要定时时按下方说明自行添加。

## 立即跑一次

```powershell
qiuzhao\console\schedule-events-refresh.ps1
```

## 建议节奏

- 每天 **08:00**、**18:00** 各一次（宣讲会常当天新增）
- 或在控制台「校园活动 → 立即刷新」
- 日更口令 `每日情报更新` 也会跑同款抓取

## 注册计划任务（需你确认后执行）

以管理员 PowerShell：

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"D:\AgentProjects\work\qiuzhao\console\schedule-events-refresh.ps1`""
$t1 = New-ScheduledTaskTrigger -Daily -At 8:00am
$t2 = New-ScheduledTaskTrigger -Daily -At 6:00pm
Register-ScheduledTask -TaskName "Qiuzhao-XidianEvents" -Action $action -Trigger $t1,$t2 -Description "刷新西电宣讲会/双选会"
```

取消：

```powershell
Unregister-ScheduledTask -TaskName "Qiuzhao-XidianEvents" -Confirm:$false
```
