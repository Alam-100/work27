- 2026-10-04: 秋招续采 — 新入库税友×2 / 达梦数据 / 快递100 / 拓维信息 / 思谋科技 / 树根科技；歌尔 Agent 面经 14 问；未改已有目录结构
- 2026-09-18: 我的秋招 — 按阶段拆页（测评/笔试/面试等）+ 已拒软归档可恢复；重建 dist
- 2026-09-18: 牛客校招日程深挖入库中移互联网 / 中移在线智能体岗；跳过咪咕金种子博士硬门槛
- 2026-09-18: sma-wiki 新公司补漏入库中海达 / 白杨智能；备份脚本补 git/robocopy 超时，防 E 盘损坏时卡死
- 2026-09-17: vault_dual_backup 加固——E盘git损坏自动改走D盘镜像推远程；Skill强制有改必推
- 2026-09-17: 登记 sma-wiki 校招汇总源 + fetch_sma_wiki.py；入库懂车帝×2 / 百川源点；缺口清单待下轮
- 2026-09-17: 补录收件箱笔试完整题面（滴滴/携程/拼多多），禁清单短标题偷懒；Skill 强制条款；双重备份
- 2026-09-17: 秋招非面经改动双重备份：情报库京东/云帐房/深信服 + 补回 AI面与行为面/高频题答遗漏文件，push GitHub 并刷新 D 盘镜像
- 2026-09-17: 未入库公司深挖入库京东×2 / 云帐房 / 深信服 X-STAR Agent；跳过已入库扩岗与低匹配
- 2026-09-17: E盘NTFS修复 + 知识库从GitHub干净重建/push；D盘镜像与 vault_dual_backup.py；面经加大火力入库已抢救回库
- 2026-09-16: 我的秋招 — 投递状态下拉按流程环节动态生成（自定义环节如 ai面 → 待面试-ai面）
- 2026-09-14: 秋招早报自动化 — 新增 Agent/智能体岗卡 10；华为/商汤/携程核实；西电校园活动刷新；面经百度/商汤/携程 +38
# Changelog

## 2026-10-04

### 秋招情报与面经续采

- 快照里没有历史 vault。新笔记写在 `秋招/`，路径与原先 Obsidian 相对路径一致；未重命名、未移动已有文件夹
- 情报：税友 AI Agent 算法工程师、税友知识库与 RAG、达梦数据 Agent 开发、快递100 Agent 开发、拓维信息 Agent 开发、思谋科技 Agent 应用开发、树根科技 AI 算法/智能体工程师
- 面经：`歌尔-Agent面经题库` 14 问（1 篇牛客真帖）。字节等已有题库公司不新建同名文件
- 来源：sma-wiki、牛客日程、OfferStar、求职方舟已复检；西电首页抓到但未写入活动库
- `company_tiers.json`、`source_links.json` 原地更新

## 2026-09-18

### 我的秋招状态分组与归档

- 进度列表按阶段分页：待投 / 测评 / 笔试 / 面试 / 等结果
- 已拒进入「未通过」软归档，可一键恢复；物理删除仍走 `_归档`
- 重建 `web/dist`

## 2026-09-17

### vault 双重备份加固（E 盘损坏兜底）

- `vault_dual_backup.py`：E: git 损坏时自动经 D: 镜像同步可读工作树并 push GitHub，再尝试修复 E: `.git`
- `qiuzhao-assistant` / `qiuzhao-mianshi-search` / 每日刷新清单：凡 vault 改动必须推远程干净副本

### sma-wiki 校招汇总源

- 固定来源 `campus.sma-wiki.cn`（互联网 + 27届秋招）
- 脚本 `qiuzhao/scripts/fetch_sma_wiki.py`；与方舟/OfferStar 并列用于每日情报
- 深挖入库懂车帝（Agent架构/AI应用）、百川智能（源点 Agent算法）

### 笔试完整题面补录（反偷懒）

- 从原图重录滴滴 / 携程 9.6 / 拼多多 8.23·9.6·9.13 完整题面到 `笔试题型/`
- `高频手撕清单` `#其他` 改为回链；`qiuzhao-assistant` Skill 增加强制条款

### 非面经改动同步 GitHub（双重备份）

- 推送待提交情报库：京东×2 / 云帐房 / 深信服 / 得物复核删卡
- 从损坏备份补回：携程 AI 面题干清单/口述答/背诵打印版；高频题答前30题/背诵打印版
- 执行 `vault_dual_backup.py`（GitHub push + D 盘镜像）

### 得物岗复核

- 保留中间件 AI（Java/Golang）为最匹配全职；删除已变实习的风控大模型卡
- 跳过 Golang/视觉/产品等低匹配扩岗

### 未入库秋招公司：京东 / 云帐房 / 深信服

- 京东 TGT：零售全场景 Agent、国际电商 Agent 应用（官网详情 permalink）
- 云帐房：AI Agent 开发工程师（北森单岗）
- 深信服：X-STAR 本硕·方向三 Agent（Delivery/4520）
- 策略：不扩已入库公司岗位；低匹配研究向跳过

### E 盘损坏修复与知识库双重备份

- 根因：E 盘 `ST2000DM008` HDD 的 NTFS `$I30` 索引损坏（非编码冲突）；`Repair-Volume -OfflineScanAndFix` 后卷恢复 Healthy
- 从 GitHub 干净重建 `E:\obsidian\My_docs`，合并抢救的 09-17 面经加厚，并 push（`b48218e`）
- 新增 D 盘镜像 `D:\backup\my-obsidian-mirror` + 脚本 `qiuzhao/scripts/vault_dual_backup.py`
- 面经 Skill 写入「双重备份强制」条款

### 面经加大火力（技术面 + AI 面）

- 恢复缺失的 `字节跳动-Agent面经题库`，并入库热榜「字节 Agent 秋招一面」与 09-15 凉经
- 加厚淘天 / 拼多多 / 美团 / 蚂蚁 / Shopee / 长鑫存储 / 去哪儿（含去哪儿 AI 面测开）
- 收获笔记：`qiuzhao/tmp/mianshi_harvest_20260917.md`

## 2026-09-16

### 投递状态随流程动态变化

- 「我的秋招」详情投递状态不再只用固定枚举；随本流程环节生成（含新增的自定义环节）
- 重建 `web/dist`

## 2026-09-14

### 我的秋招：统一邮箱跳转

- 进度页增加邮箱入口（打开收件箱 + 可选按公司搜邮件）
- 预设 Gmail / QQ / Outlook / 163，配置存浏览器 localStorage

### 重建 SPA dist

- `web/dist` 停在 09-10，导致「开始/截止/安排」与邮箱条在成品控制台不可见；已重新 `npm run build`

## 2026-09-12

### 秋招深挖写回

- 商汤科技：Feishu ATS 深挖，新增 Agent/Harness/Agentic/智能体/大模型应用相关岗卡 8
- 华为：Agent技术/AI技术应用/AI应用安全核实于刷新；2 张损坏岗卡自 harvest 恢复
- 截止态修正：点点互动已截止；天锐星通 D-day 将截止

## 2026-09-11

### 职位列表加载加速

- 修复 `/api/intel`：跟进状态批量解析，避免每岗重读进度目录（约 5s → 亚秒）
- `/api/health?light=true`（默认）+ `/api/enums`；职位页不再每次全量 health

### 环节时间可选 + 开始/截止语义

- 修复「我的秋招」详情侧栏 `datetime-local` 选不中（受控组件无本地 state）
- 流程环节增加 `time_kind`：开始 / 截止 / 安排；UI 显示「笔试截止时间」「面试开始时间」等
- 无字段时按类型推断；写入 Obsidian `流程[]`，日历展示带语义

### 跟进投递遇损坏进度卡不再 500

- 原因：`05_投递进度` 下个别笔记（及 `_索引.md`）被同步成二进制，旧逻辑 `read_note` 硬崩
- `create_progress_from_intel` 遇损坏同名卡 → `*.md.badenc` 隔离后重建；`get_progress` 容错
- **必须重启控制台**才能加载新 `vault_io`

### 中兴微电子用户已投补录

- 补 `中兴微电子` 公司卡与 JW27040 岗卡；进度标待测评；内推码与 [投递记录查询](https://app.mokahr.com/candidate/applications/deliver-query/sanechips) 已写入

### 群消息筛选 + 岗卡 permalink + 央国企

- 新增 `qiuzhao/scripts/job_apply_url.py`：岗卡禁止北森/智联白牌列表壳；`/campus/jobs?jobAdId=` → `/campus/detail?jobAdId=`
- `vault_io.enrich_intel_meta` / `set_intel_apply_url` / `default_intel_job_body` 写卡时自动规范化
- 群消息：无关内容丢弃；已入库比链接有效性后替换渠道
- 合合 J14436/J14439、神州 J22513、讯飞 Harness 岗补 `/campus/detail` permalink（讯飞原「AI agent开发」官网已下架）
- Obsidian：平安银行×3、航天502所；vivo 等 permalink 已改

### 修复画像 UTF-8 读盘崩溃

- 原因：`00_画像/求职画像.md` 再次损坏为二进制（与此前招商银行卡同类）
- `get_profile` / `try_read_note`：非 UTF-8 时返回空，校园活动页不再 500
- 损坏件备份为 `求职画像.corrupt-2026-09-11.bin`；按履历+模板重建可读画像（细节待你补全）

## 2026-09-10

### 秋招群消息收件箱

- 口令 `处理群消息`：群导出 → 抽内推码/校招链 → 已有公司只补 `_公司.md` 投递渠道；新公司深挖过门才写岗卡
- 档次表补银河通用/卧安/普渡/蔚来/地平线/MiniMax/小马智行/搜狐/九号公司
- 本轮入库见 Obsidian；实习生链与腾讯文档汇总表不写岗卡

### 投递记录查询链接

- 进度卡新增字段 `投递记录查询`；公司 `_公司.md` SSOT + 渠道类型「投递记录」
- SPA「我的秋招」详情/列表可打开官网申请进度；跟进时预填
- 已写入科大讯飞：[投递记录](https://iflytek.zhiye.com/personal/deliveryRecord)

### 科大讯飞官网投递渠道补全

- 校招门户改为 [官网校招列表](https://iflytek.zhiye.com/campus/jobs?queryId=0e17ee07-26f3-4975-832f-e7b1729652a5)；内推码 `EVK4VV`
- 增补 [飞星计划](https://iflytek.zhiye.com/4/jobs?queryId=a4f141a2-3d4e-44df-a1b4-918b00f23a00)；牛客详情降为备份渠道
- 岗卡 `科大讯飞-AI-agent开发` 投递入口同步优先官网

### 公司多源投递渠道（HR内推）

- `vault_io.upsert_company_apply_channel`：内推链接/码写入 `_公司.md`「投递渠道」（可多条）
- 首条：中兴微电子 · 内推码 `NTAW078`（与中兴通讯分卡）
- API/职位页展示内推按钮；跟进投递时自动带出内推码

## 2026-09-09

### 点进校招列表补 JD

- `company_tiers.json`：固德威（中厂）、北方华创（央国企）、傅利叶（小厂）、新华三（中厂）
- 本轮入库见 Obsidian 情报库；抓取须点校招入口、搜 Agent/ai/智能体、锁定 2027 全职

### 秋招情报续收（新开公司）

- `company_tiers.json`：中兴通讯/中国电子云/网易有道/深城交/FunPlus/网易智企
- 本轮入库见 Obsidian 情报库；仓库只改档次表与日志

### 已截止岗归档到 `02_情报库/_归档`

- 扫描：按截止日归一化为「已截止」共 2 岗（帆软 Agent、阶跃星辰 Code Agent）→ 挪入 `_归档/{公司}/`，不删文件
- `vault_io.list_intel()` 默认跳过归档；`archive_closed_intel()` 可复跑；API `scope=closed/all` 仍可读归档卡
- 在招库存 237；已截止仍可在控制台「已截止」Tab 查看

### 校园活动续抓 +「明天」过滤

- 西电就业网再刷：+7 / 更新 66；前端时间桶新增「明天」

### 校园活动跨来源去重

- 就业网与公众号同场同公司合并；vault 已清 47 条重复

### 校园活动同场合并 + 对口强调 + 周报截图入库

- 同场合并键：`开始|地点|活动类型|形式`；对口优先级情报库 → 画像/方向关键词 → 其它（不排除）
- 公众号周报截图 `640.jpg`（9.7–9.13）补录入库并归档

### 修复情报页 UTF-8 读盘崩溃

- Vault 中招商银行公司卡、阿里巴巴 AI-Agent 岗卡文件损坏（二进制非 Markdown）
- `vault_io` 公司概览/单岗读取遇 `UnicodeDecodeError` 时跳过，恢复 `/api/intel`

### 校园宣讲会 / 双选会追踪

- 主数据源：西电就业网 `job.xidian.edu.cn`（teachin / jobfair）；公众号周报因验证墙改为人工补录
- 抓取：`qiuzhao/scripts/fetch_xidian_events.py` → Obsidian `秋招/10_校园活动/`（`qiuzhao-campus-event`）
- 控制台：新页 `/events`（今天/本周/更后、情报库命中、立即刷新、公众号入队）
- 日历与 ICS 叠加校园活动；`source_links.json` 增加就业网书签
- 时效：SPA 刷新 + 日更 checklist + 可选 `schedule-events-refresh.ps1`（08:00/18:00，默认未注册）

## 2026-09-06

### 岗卡正文补回 JD（Obsidian 阅读视图）

- 原因：阅读视图默认隐藏 YAML，部分写卡只把 JD 放进 frontmatter `岗位简介`，打开笔记只剩「打开」链接
- 处理：`vault_io.sync_intel_job_body_jd` + `scripts/sync_intel_body_jd.py`；242 岗正文均有 `## 岗位简介`
- 以后写卡必须正文+YAML 双写；模板 `default_intel_job_body`

### 面经加大马力：沐瞳新建 + 字节/阿里加厚

- 牛客热帖：新建沐瞳题库（数仓 AI 向）；加厚字节 9.3 Agent 一面、阿里 Agent 开发岗一面
- 缺口检索：金蝶/58同城/思必驰/BOSS/国机数科/美团北斗 无 2026 Agent 真帖
- 脚本 `qiuzhao/tmp/apply_mianshi_20260906d.py`；线索 `qiuzhao/tmp/mianshi_harvest_20260906d.md`

### 下午加大马力：米哈游研究员 + Shopee 新岗 + 大疆限投

- 复拉汇总表后官网深挖：米哈游 Agent 算法研究员；Shopee 购物 Agent / Agent 后训练（ASP 限投 1）
- 更新大疆智能作业三城分帖；详情页原文「拓疆者允许投递1次」
- 跳过快手 12766/12783 标题党、Shopee MPI 博士、实习包装、新公司列表 0 Agent
- 库存：**88 家 / 242 岗**（大厂 152 · 中厂 60 · 小厂 19 · 央国企 10 · 外企 1）

### 加大马力：字节新岗 + 思必驰 + 金蝶 AI 应用

- 汇总表：牛客 filtered=252；方舟 520；OfferStar agent=69；华为 advertisementId 未变
- 官网深挖入库 13 岗 / +1 家：思必驰 Agent 开发；字节 Tako/生态后端/推荐智能体/交易广告全栈/AIOps/TikTok Shop/抖音研发 Harness/抖音直播；小米 Camera Agent；美团北斗×2；金蝶应用开发-AI
- 金蝶官网限投 3；学历门 scan-vault HITS 0
- 库存：**88 家 / 239 岗**（大厂 150 · 中厂 59 · 小厂 19 · 央国企 10 · 外企 1）

## 2026-09-04

### 面经续挖：新建帆软/亚信 + 加厚 4 家

- 牛客检索 + 待续帖：新建帆软、亚信安全 Agent 题库
- 加厚深信服（工具注册中心）、去哪儿（AI 面）、滴滴（数开二面）、快手（SQL 注入/MVP）
- 脚本 `qiuzhao/tmp/apply_mianshi_20260904.py`；线索 `qiuzhao/tmp/mianshi_harvest_20260904.md`

## 2026-09-02

### 学历门：博士硬门槛直接剔除

- 求职画像为硕士。官网任职要求只要博士（硕士不可投）→ 不入库、不标观望
- 新增 `qiuzhao/scripts/jd_edu_gate.py`；Skill / DEV / 华为 harvest 接入
- 已删 8 卡：阿里星代码 RL / 在线 RL / 自主编程；字节 Commercial AI 博士课题；vivo 蓝极星×2；度小满研究员-博士；小米工业垂域
- 库存：**75 家 / 213 岗**（大厂 139 · 中厂 50 · 小厂 16 · 央国企 7 · 外企 1）
- 仍收：硕士或博士 / 硕士及以上 / 博士优先

### 加大马力：新公司 3 + 飞书全栈 / 阿里星新岗

- 官网核实（Beisen / 飞书招聘 / 字节 / 阿里校园）：亿联网络 Agent 开发、中国联合工程智能体应用、自变量机器人 Agent 开发
- 已入库新岗：字节飞书全栈×2 + Commercial AI 博士课题；阿里星×4（含新加坡数据库岗、09-02 更新的运行时安全岗）
- 库存：**75 家 / 221 岗**（大厂 146 · 中厂 51 · 小厂 16 · 央国企 7 · 外企 1）
- 截止一律官网；自变量不写方舟 09-03；威迈斯/策划岗/产品经理/微信墙未入库
- `company_tiers` / `source_links` 同步；脚本 `qiuzhao/tmp/write_cards_20260902.py`

## 2026-09-01

### 收件箱图片：56 张入库 11 家 + 新建商汤/宇树题库

- 处理 `_inbox_images` 全部待处理截图；原图归档；新建商汤科技、宇树 Agent 题库
- 加厚 OPPO/Shopee/字节/拼多多/携程/淘天/百度/腾讯/阿里巴巴；手撕清单同步
- 脚本：`qiuzhao/tmp/apply_inbox_images_20260901.py`

### 续挖面经：秋招爆发期加厚 7 家 + 新建 DeepSeek 库

- 牛客多源检索消化 8 篇真帖；加厚快手/蚂蚁/阿里/OPPO/哔哩/字节/小鹏；新建 DeepSeek
- Vault：来源日志、综摘、手撕清单同步；`_inbox_images` 无待处理图片
- 脚本：`qiuzhao/tmp/apply_mianshi_20260901.py`；线索 `qiuzhao/tmp/mianshi_harvest_20260901.md`

### 职位列表：截止优先 + 公司分页 + 已截止分区

- API：`GET /api/intel` 新增 `scope=active|closed|all`、默认排序 `deadline_then_score`；`stats.closed`；公司 `earliest_deadline` 忽略已过期岗
- SPA：在招/已截止 Tab；默认每页 20 家、公司默认折叠（将截止自动展开）；全部展开/折叠
- 已截止岗位先做 UI 分区（后于同日改为物理 `_归档/`，见上文「已截止岗归档」）

## 2026-08-31 晚 加大马力（vivo / 昇腾 Infra / 平头哥 / 长鑫）

- 官网核实：vivo FAQ 秋招网申 **2026-09-15 12:00**；华为 `--include-infra`；平头哥阿里 SPA；长鑫 `cxmt.zhiye.com`
- 新增 31 岗（vivo×9、华为 Infra×8、平头哥×10、长鑫×4）；新公司平头哥、长鑫存储
- 库存：**72 家 / 211 岗**（大厂 139 · 中厂 50 · 小厂 15 · 央国企 6 · 外企 1）
- Skill / harvest_huawei：用户点名昇腾/AI Infra 时加 `--include-infra`，默认仍严筛 Agent 三意向

## 2026-08-31 秋招情报补跑

- 新增：阿里 AI Agent平台开发工程师（199907780033）；因克斯智能 Agent开发工程师；启云方 AI Agent工程师；英特尔 Agentic AI Customer Co-Val CG
- 更新：华为 6 张岗位意向卡核实于；阿里 `_公司.md` 限投
- 库存：**70 家 / 180 岗**（大厂 112 · 中厂 46 · 小厂 15 · 央国企 6 · 外企 1）

## 2026-08-30

### 秋招情报日更

- 牛客 filtered=212；方舟 row_count=443；OfferStar agent=52 / ai=335
- Vault：新增博思软件×2 + 阿里巴巴算法工程师-AI Agent；复检 OPPO / 点点互动 / Momenta；库存 **67 家 / 176 岗**（大厂 111 · 中厂 46 · 小厂 14 · 央国企 5）
- company_tiers 补博思软件=中厂；来源链接库/每日刷新清单/来源日志已回写


## 2026-08-28

### 华为岗位意向入库

- 根因：列表页点击新开 `job-details?advertisementId=…`，JD 由 `getPositionIntentionList(jobId)` 按岗位意向返回
- `qiuzhao/scripts/harvest_huawei_campus.py`：去重旧广告、严筛 Agent/大模型应用/AI应用安全意向
- Vault：新增华为×6（新公司）；库存 **66 家 / 173 岗**（大厂 110）
- Skill / 日更清单：遇到华为默认走该脚本，禁止因「详见岗位意向」跳过
- 跳过：Infra/算子/训推/空间智能/后训练/评测等非应用意向

### 携程核实入库（华为当时跳过）

- 牛客/方舟复检；携程官网核实 4 个 Agent 全职校招岗（Agent开发 / 云原生 AI Agent / 大数据 AI Agent / LLM算法）
- Vault：新增携程×4（新公司）；库存 **65 家 / 167 岗**
- 华为当时列表页无实质 JD（「详见岗位意向」）→ 随后已按意向 API 补抓入库

### 秋招情报加大马力（新公司 + 已入库新岗）

- 拉表：牛客 filtered=213；方舟 row_count=421（+8）；OfferStar 持平
- Vault：新增 14 岗（鹰角网络 Agent 测试开发；合合 J14436；度小满算法/博士研究员；阿里星×4；快手×6）；库存 **64 家 / 163 岗**
- `company_tiers` 加鹰角网络=中厂；来源链接库方舟/牛客计数更新
- 跳过：海康/途牛/南方基金/蚂蚁智能体未展开实质 JD；字节新 ID 实习；无过关外企校招 Agent JD

### 秋招情报续挖（已入库复检 + 差分深挖）

- 拉表：牛客 filtered=212（+24）；方舟 row_count=413（+6）；OfferStar agent=50 / ai=322
- Vault：新增 41 岗（新公司昆仑/海能达/海艺/吉利/卓驭/盒马/容知/遨森/长园深瑞/数坤/电科32所/千里/星网锐捷/合合/千曙/知象 + 字节×11 + 小米工业垂域 + 小红书 REDstar×4 + 米哈游/智元分卡 + 大华/千里新岗）；vivo 蓝极星改官网 JD；库存 **63 家 / 149 岗**
- 大厂核实于刷新；帆软→将截止；`company_tiers`/`source_links` 更新至 2026-08-28
- 跳过：字节大量实习；vivo 前端 Agent；顺丰/炎魂/深信服 AI 编程工具岗；希奥端芯片 Runtime；华为问卷墙；南方基金无 JD；海康/途牛/58/智谱未展开；外企本轮无过关校招 Agent JD

## 2026-08-26

### 秋招情报续挖（已入库复检 + 差分深挖）

- 拉表：牛客 filtered=188（+2）；方舟 row_count=407（+12）；OfferStar agent=42 / ai=49
- Vault：新增 3 岗（小米 Harness 开发 / AI属性工程师-汽车 / AI数据基础架构）；库存 **47 家 / 108 岗**（大厂 77）
- 差分新公司 FUNPLUS/携程/贝壳等深挖；字节 66 新 ID 全为实习
- 大厂核实于刷新；帆软→将截止；`source_links` last_checked=2026-08-26
- 跳过：容知日新/深信服门户失效；Wind 仅实习；亚马逊社招 1 年+

### 续挖面经（Agent + 后端/数据库）

- 牛客热榜 + 后端 AI Agent 检索；实质帖约 6 篇入库
- 新建 `网易-Agent面经题库`；加厚美团/阿里/腾讯/字节工程题（MySQL/Redis/MVCC/零拷贝等）
- 手撕 +2：最长有效括号（LC32）、奇偶链表
- harvest `mianshi_harvest_20260826.md`；方法论/卖课帖跳过

## 2026-08-25

### 履历学术事实卡 + 自我介绍 STAR 口径

- Vault：新建 `秋招/00_画像/履历学术与荣誉.md`；画像与阿里 `自我介绍和回答` 挂接
- 口径：自我介绍用压缩项目句；完整 STAR（情境/任务/行动/结果）放行为面与项目深挖；手册更新后再加厚项目段

### 阿里 AI 应用研发：岗位分析 + 自我介绍和回答

- 产出（Obsidian vault `08_面试准备/阿里巴巴-AI应用研发工程师/`）：岗位分析与经历匹配、面经汇总按题库轻量对齐、自我介绍和回答（中英 + 分组合并答）
- 强制引用 DORA 面试手册覆盖标签；复盘 `03_面经/阿里巴巴-面经与复盘` 回写准备区摘要与 wikilink
- 不编造姓名/学校/实习/竞赛；不出 DOCX、不跑口述卡阶段

### 收件箱图片入库（面经去重 + 美团笔试）

- 字节 22 张截图加厚题库（Kafka/ClickHouse/JWT/评测等），与牛客帖去重
- 阿里 3 张（淘天/飞猪 B）：KV cache、HNSW/IVF、MCP 上下文膨胀等
- 新建 `美团-Agent笔试题库`（10 单选 + 另类与运算）；手撕 +5
- 笔试口径：牛客往年题作摸底，不作当年高频推断；`oppo/` 3 张待处理

### 续挖面经（多源过滤去重）

- 牛客实质帖约 5：新建月之暗面；加厚字节 agent 一面、百度大模型 Agent、阿里云 Agent、虾皮 Agent
- 知乎营销汇总帖丢弃；脉脉登录墙；手撕双栈队列与二叉树遍历组合题
- harvest `mianshi_harvest_20260825.md`；缺口公司仍记 inbox

### 秋招情报续挖（已入库复检 + 差分深挖）

- 拉表：牛客 1203/1206/1210 filtered=186；方舟 row_count=395；OfferStar agent=42 / ai=274
- Vault：新增 3 岗（美团×1；字节×1；小米×1）；库存 **47 家 / 105 岗**（大厂 74）
- 外企深挖：亚马逊 AI Agent 岗为社招未入库；谷歌中国 0 岗
- 大厂核实于刷新；帆软→将截止；`source_links` last_checked=2026-08-25
- 跳过：鹰角 LLM、字节实习 position、微软非 Agent 研发列表

## 2026-08-24

### 收集口径：新增外企第五档

- `公司档次` 增 **外企**（亚马逊/微软/谷歌等总部在境外知名外企）；默认投递优先级=冲刺
- 三门收集口径：互联网严筛 Agent；央国企宽 AI 应用；**外企以岗为主**收 Agent/AI/ML（须实质 JD）
- `company_tiers.json` 登记常见外企别名；牛客白名单扩外企名；控制台职位页统计第五格 + 筛选

### 秋招情报续挖（已入库复检 + 差分深挖）

- 拉表：牛客 1203/1206/1210 filtered=186；方舟 row_count=395；OfferStar agent=42 / ai=269
- Vault：新增 4 岗（拓竹×1；字节×3）；库存 **47 家 / 102 岗**（大厂 71）
- 字节 2 岗补城市；大厂核实于刷新；帆软→将截止
- `company_tiers` 登记拓竹科技；`source_links` last_checked=2026-08-24
- 跳过：AML Harness 与火山方舟同岗、南方基金/杭银/七牛实训/深信服 404/京东无 Agent 标题

## 2026-08-23

### 续挖面经（Agent + 工程题）

- 牛客实质帖约 6：新建小鹏 AI Infra；加厚哔哩哔哩后端 AI、Shopee 大模型、蚂蚁多模态、小米轨迹 Agent、字节广告 agent 后端
- 手撕课程表 Plus；harvest `mianshi_harvest_20260823.md`；缺口公司再扫无真帖记 inbox；脉脉登录墙；小红书停用

### 秋招情报续挖（已入库复检 + 差分深挖）

- 拉表：牛客 1203/1206/1210 filtered=168；方舟 row_count=388；OfferStar agent=40 / ai=242
- Vault：新增 12 岗（字节×8；小米×4）；库存 **46 家 / 98 岗**（大厂 68）
- 帆软复检仍在招→将截止；大厂门户核实于批量刷新
- `source_links` 更新 last_checked=2026-08-23；本轮不做面经；未自动建投递进度
- 跳过：南方基金 JD 不足、深信服弱 Agent、京东/杭银/七牛实训、旧缺口 LLM 厂

## 2026-08-20

### 续挖面经（Agent + MySQL/Redis/后端）

- 牛客实质帖约 14：阿里云/剪映/京东全栈 agent（含 MySQL·Redis）/快手/美团后端 AI/哔哩/智象 infra/百度多模态 B
- 工程题归 `#工程与系统`；手撕大数加减、单词频率；harvest `mianshi_harvest_20260820.md`
- 08-20 新缺口九家 + 旧缺口再扫无真帖记 inbox；知乎营销帖丢弃；脉脉登录墙；小红书仍停用

### 秋招情报续挖（已入库复检 + 新公司）

- 拉表：牛客 1203/1206/1210 filtered=161；方舟 row_count=373；OfferStar agent=36 / ai=80
- Vault：新增约 18 岗（新公司大华/微博/智明星通/点点/天锐/万店掌/帆软/云深处/星环；字节×5；小米×3；快手×1）；库存 **46 家 / 86 岗**
- 队列 3 条字节核实完成；限投：微博=2、星环=1、云深处=2/3月
- `company_tiers` / `source_links` 更新；本轮不做面经；未自动建投递进度
- 跳过：盒马产品经理、高德共享岗、深信服弱 Agent、世纪华通实习、京东/美团详情不足、旧缺口 LLM 厂

## 2026-08-19

### 广扫加厚面经

- 牛客实质帖约 15+；新建多益网络/迅雷/科大讯飞题库；加厚字节/淘天/阿里/百度/滴滴/影石
- 手撕：LC110；Cross-Attention / RMSNorm；`company_tiers` 补多益/迅雷
- 待续挖 `qiuzhao/tmp/mianshi_harvest_20260819.md`；知乎可达、脉脉登录墙；小红书仍停用

### 秋招情报续挖（已入库复检 + 新公司）

- 拉表：牛客 1203/1206/1210 filtered=160；方舟关键词行 371；OfferStar agent=35 / ai=215
- Vault：新增 15 岗（字节×5、小米×4、阿里×2、Shopee 算法、度小满/镁信/金证）；库存 **37 家 / 68 岗**
- 阿里 `_公司.md` 写入限投：每业务集团 2 意向；候选池补记 08-17 平安/招行；`_索引` 补央国企 Dataview
- `company_tiers` 补度小满=中厂、镁信健康=小厂、金证科技=中厂；`source_links` 更新最近检查
- 本轮不做面经；未自动建投递进度

## 2026-08-18

### 按公司×岗位补缺口面经

- Skill `qiuzhao-mianshi-search`：情报库有、题库缺的公司必须走公司×JD 岗位检索
- Vault：新建小米/滴滴/OPPO/Shopee/阶跃/智元/同花顺题库；Momenta 二面；综摘回链；手撕 LC209/240/Coding Agent Demo
- 待续挖 `qiuzhao/tmp/mianshi_harvest_20260818.md`；inbox 缺口待补图清单
- 知乎可搜、脉脉登录墙；小红书仍停用

### 前端同步：分页、四档、复盘手撕

- 职位页分页：`/api/intel` 缺省按岗；`page_unit` 区分岗/公司；按公司默认每页 50 家；页码按钮；统计卡含央国企/未分档
- 我的秋招/日历/更多：档次 pill、新建计划/优先级、截止事件带公司搜索、入队意图走 enums
- 面试复盘：手撕 Tab + `GET /api/review/coding-list`；题目卡片补回答/参考/掌握；问题表增加类型列
- 重建 `qiuzhao/web/dist`，避免 :8765 继续吃旧包

## 2026-08-17

### SOP 广扫续挖面经

- 牛客 Code_Agent 约 6 篇；新建 `Momenta-Agent面经题库`；增补阿里巴巴（+约 20 题）、影石
- 补淘宝闪购综摘回链；待续挖 `qiuzhao/tmp/mianshi_harvest_20260817.md`
- 知乎登录墙、脉脉 404 → 待核实；小红书路径仍停用

### 央国企/银行第四档 + 续挖秋招

- 枚举：`公司档次` 增 **央国企**（银行/央企/国有保险）；默认投递优先级=保底
- 控制台：JobsPage 统计第四格 +「保底视图」；Skill/日更 checklist 双门口径
- 拉表：牛客白名单扩央国企名；方舟关键词扩 AI应用/智能科研；差分 `diff_soe_20260817.txt`
- 新增：平安银行 AI应用研发 / Agent Infra / AI应用算法；招商银行·招银网络算法工程师
- 互联网复检：字节 豆包大模型Agent算法(MaaS)-火山方舟；AI Agent安全研究员-TikTok；既有字节卡刷新核实日
- 跳过：杭州银行 0 岗、浪潮公众号墙、京东方暂无、电科/兵器无独立 LLM Agent、联通登录墙、OfferStar 微信墙

## 2026-08-16

### 淘宝闪购面经入库与题干纠偏

- Vault：新建 `淘宝闪购-Agent面经题库` + `淘宝闪购-面经与复盘`；综摘回链；不混入淘天题库
- 清洗：丢弃复述收束 2 条；Skill 埋点 4 连问合并；SSE/记忆层/Codex/Cursor 口语改准
- `company_tiers` 补淘宝闪购/闪购/淘天=大厂

### 续挖秋招 + 情报库按公司聚拢

- 牛客/方舟/OfferStar `20260816` 拉表差分；已入库门户复检 + 新公司深挖
- 新增：字节抖音客户端 Agent、字节自进化算法；恒生智能体/AI应用；Shopee SSC AI Agent（限投1）；同花顺金融 Agent 平台算法
- 存储：`02_情报库/{公司}/` + `_公司.md`；`vault_io` 递归读写；米哈游重卡合并
- 控制台：`/api/intel?group=company` + JobsPage 父子列表与限投超限警告
- `company_tiers` 补恒生/Shopee/同花顺等；跳过深信服/华为问卷墙/微信墙

### 停用小红书面经路径 + 牛客续挖

- Skill / `source_links`：小红书面经入口标停用；禁止 Agent 访问（不做规避检测）
- 牛客续挖：新建京东/深信服题库；增补大疆、字节；手撕补 LC88 来源与 List→树形结构
- 知乎登录墙、脉脉搜索 404 → 待核实；脚本 `qiuzhao/tmp/mianshi_harvest_20260816.py`

## 2026-08-14

### 加大火力续挖新开秋招

- 牛客/方舟/OfferStar 拉表差分；已入库公司门户复检新 Agent 岗
- 新增情报卡：小米×3、滴滴×2、货拉拉×1、字节火山方舟/Aime/Infra/抖音增长/抖音研发
- 更新：字节 AI Platform/豆包/Coze、腾讯 Agent 开发核实日；`company_tiers` 补货拉拉/深信服/滴滴
- 跳过：深信服无独立 Agent 岗、华为问卷墙、OfferStar 微信墙

### Cursor 孤立工作区对话修复

- 重建 `%APPDATA%\\Cursor\\Workspaces\\1786347249089\\workspace.json`（work + DORA 多根工作区定义），消除「路径不存在」
- 将 11 条孤立对话（含「秋招信息收集」「秋招：面试模拟」等）从 orphan project 改绑到 `D:\\AgentProjects\\work`
- 脚本：`qiuzhao/scripts/cursor_rebind_orphan_workspace.py`、`cursor_verify_rebind.py`；改绑前已备份 `state.vscdb`

## 2026-08-14

### 修复 Cursor work 工作区对话绑定

- 清理 orphan `1786347249089` / plans 下 `.code-workspace` 的多套 workspace 身份
- 秋招相关 composer 统一 membership 到 glass project「秋招」；脚本 `qiuzhao/scripts/cursor_fix_work_binding.py`
- 多根工作区文件迁至 `work.code-workspace`（仓库根）；plans 下旧副本归档到 `_archived_workspaces`

## 2026-08-13

### 已入库题库二次聚类精修

- 21 家公司 `*-Agent面经题库` 节内二次聚类/同义合并/重编号（排除初创小厂；未挖新帖）
- 人工精修字节 `#架构与Agent设计`、腾讯 `#Agent`、小红书 Harness 合并、快手 RAG/系统设计顺序
- 脚本：`qiuzhao/tmp/mianshi_recluster_20260813.py`、`mianshi_manual_polish_20260813.py`

### 面经续挖 + 手撕代办化 + 题库聚类

- 牛客 Code_Agent + 小红书面经多方续挖；新建大疆题库；增补腾讯/字节/即梦/快手/小红书/百度等
- `高频手撕清单` 知识点节改为 `- [ ]` 代办（便于勾选排查）；补翻转整数（LC7）
- 公司题库大类内相似题聚类、同义合并与重编号（美团/字节/阿里优先，其余库扫一遍）
- 跳过总结卖课/初创小厂/付费墙后；脚本：`qiuzhao/tmp/mianshi_cluster_20260813.py`

### 新开秋招情报续挖（广扫 + 结清待核）

- 渠道：牛客 1203/1206/1210、方舟、OfferStar；官网深挖哔哩/米哈游/千寻/小红书/蚂蚁/瓴羊入口
- 新增：哔哩多模态 Agent（截止 12-31）；米哈游 Agent 全栈；千寻 Agent 算法；小红书 REDstar（观望）；蚂蚁 Agent Infra（观望）；阿里共享 AI Agent 研发（瓴羊筛选入口）
- 结清：千寻入库；瓴羊部门列表暂无独立岗；vivo 仍博士观望
- 跳过：海康实习、携程/影石/追觅/即梦无 27 全职 Agent JD、微信墙
- `company_tiers.json` 含小红书=大厂、千寻智能=中厂、瓴羊别名

## 2026-08-12

### 小红书 Agent 面经续挖（已登录 + 筛选收紧）

- Skill：对口岗 / 26 优先 / 排除初创极小厂
- 小红书点开识图入库；新建海康威视；大增哔哩哔哩；续挖字节腾讯影石拼多多阿里；快手/携程复核
- 手撕补 LC560、并查集、棋盘可达、车票路线

### 多路径 Agent 面经续挖（广扫 + 质量门）

- Skill：广告/总结帖丢弃、2B 通用题筛选、小红书须点开读详情
- 牛客搜索深挖；新建哔哩哔哩/小红书/腾讯/思阳/初创小厂题库；续挖字节阿里百度米哈游
- 小红书 MCP 未登录标待核实；手撕补 LC316；综摘与来源链接库同步

## 2026-08-11

### 新开秋招情报广扫 + 优先深挖

- 渠道：牛客 1203/1206/1210、方舟、OfferStar 拉表；官网深挖腾讯/Momenta/快手/vivo
- 新增情报卡：腾讯-Agent开发工程师；Momenta-Data Infra Agent(Mstar)；vivo-蓝极星 Agent（博士观望）
- 更新：快手截止 2026-12-30 热招中；腾讯 WXG 青云改观望；`company_tiers.json` 补 Momenta=中厂
- 日更优先名单与来源日志/候选池同步

## 2026-08-10

### 块链接补全 `#^` 语法

- 根因：跨笔记块引用必须是 `[[题库#^qz-RAG]]`；漏 `#` 的 `[[题库^qz-RAG]]` 会被当成另一条笔记名
- `bank_block_link` 已修正；15 家原稿重同步；Skill/说明沉淀「三易混」踩坑表

### 答案原稿跳转与结构修正

- 根因：题库 `#RAG` 是标签行不是标题，`[[题库#RAG]]` 无法落到分节
- 同步脚本给分节写入稳定 `^qz-…`；原稿链接改为 `[[题库#^qz-RAG]]`，且只挂在 `## 分节` 下一次
- 去掉每题实例中的题干与重复题库链；同节复制块只改 `###` 序号

### 按公司生成答案原稿框架

- 脚本 `qiuzhao/scripts/sync_answer_frameworks.py`：从各公司题库生成原稿（元数据 + 每节一例）与标准答全量进度表
- 15 家公司框架已落地；全局 Templates 收薄；口令 `同步答案框架：全部|<公司>`
- `qiuzhao-answer-clean`：动态节缩写（别名表 + 回退），不再依赖写死全公司题单

### 面经答案清洗流水线（原稿 → 标准答）

- 新建 `秋招/06_知识库/面经答案/` 约定：`{公司}-Agent答案原稿` + `{公司}-Agent面经答案`；题号锚点 `### A-RAG-5`；进度表支持分批
- Skill `qiuzhao-answer-clean`：口令 `清洗答案` / `继续清洗`；题库行尾双向链；不做口述化
- 模板 `秋招-答案原稿` / `秋招-标准答案`；阿里巴巴标准答壳 + 全题进度表骨架

### 口述负担减轻（按需润色 + 必练短名单）

- 明确：口述卡给你练口；不做未整理答案草稿箱、不全库批处理
- `_索引` 增加常驻必练约 13 题；新建 `_答法模版`（结论→边界→证据→勿说）
- `qiuzhao-oral-qa` 默认口令 `润色口述`（一次一题，≤3）；批量仅明确点名

### 口述题答库 + 问题联动 + 公司模拟卷

- 新建 `秋招/09_口述题答/`：主题口述卡（30s/90s、同义问法、related/prereq/followups）；索引复习路径
- Skill `qiuzhao-oral-qa`；主控增加阶段四；模板 `秋招-口述题答卡` / `秋招-模拟面试卷`
- 首批：Agent/RAG/行为面共 22 卡（复用 DORA qa-bank）；字节/阿里/美团三份 `模拟面试卷`（含打印/自测版）
- 导出 `09_口述题答/_导出/doubao_bank_*.json`（不接豆包 API）；脚本 `qiuzhao/scripts/export_oral_qa_doubao.py`

### 情报分级分类 + 职位页四轴筛选

- 公司档次规范为 大厂/中厂/小厂；新增岗位族、招聘状态、投递优先级；查表 `qiuzhao/data/company_tiers.json`
- 存量 21 张情报卡回填；Obsidian `_索引` 按档次 Dataview；模板与日更 checklist 同步
- `/api/intel` 支持 tier/role_family/hiring_status/apply_priority/sort；`PATCH` 可改分类；SPA「练手视图」

### 面经多方挖掘强化 + 手撕按知识点分类

- `qiuzhao-mianshi-search`：来源链接库书签优先、多方校验、入库清洗/补全/分类/去重 SOP
- `qiuzhao-assistant` 面经/手撕对齐；`高频手撕清单` 改为知识点主轴（公司仅薄索引）
- 日更：牛客 1206 + 方舟线索；字节/阿里/美团题库增补；`08_面试准备` 三份汇总；登录墙如实待核实

### 自我介绍 Skill 强制引用 DORA 手册

- `qiuzhao-interview-answers` 仍留在秋招仓落盘；写答前必须读 `docs/interview-manual/`（≡ `DORA面试手册`），遵守覆盖标签；可选核对 DORA 代码
- `qiuzhao-interview-prep` 阶段三验收与事实规则同步；README 注明手册事实源

### 秋招专享面试准备 Skills

- 自 ericadskill 改造并落入 `.cursor/skills/`：`qiuzhao-interview-prep`（主控）、`qiuzhao-job-analysis`、`qiuzhao-mianshi-search`、`qiuzhao-interview-answers`
- 路径对齐 vault：`02_情报库` JD + `00_画像/求职画像` → 产物 `08_面试准备/{公司}-{岗位}/`；复盘回写 `03_面经`
- `qiuzhao-assistant` / README 增加交叉引用；题库仍只列问题，考察点写在 `08_` 汇总

## 2026-08-08

### 壁纸背景 + 毛玻璃半透明

- 启用 `web/public/theme-bg.jpg` 为 SPA 背景；减弱渐变蒙版
- 顶栏/卡片/抽屉/弹层等改为半透明 + backdrop-filter

### 控制台热更新开发模式

- `dev.ps1` / `start-console-dev.bat`：清端口、uvicorn `--reload` + Vite HMR，打开 :5173
- 桌面新增 `Qiuzhao-Console-Dev.lnk`；生产 `start-console.bat` 亦启用 API `--reload`

### 职位分页 + 浅紫蓝主题

- `/api/intel` 支持 `page` / `page_size`，返回 total/pages/stats；职位页分页条与每页条数
- SPA 主题改为浅紫→蓝渐变、字号略收；可选 `public/theme-bg.jpg` + `--bg-image`

### 前端时间字段改用选择器

- 新增 `DateTimeField`（`datetime-local`）；投递详情环节时间与流程编辑器不再手输 `YYYY-MM-DD HH:mm`

### 「我的秋招」可编辑改造（功能优先）

- 进度页改为总览统计 + 目录表 + 详情；修复 JD/详情溢出
- 状态胶囊、分组、环节时间、备注可在网页编辑并写回 Obsidian
- 支持自定义流程（增删改排序），YAML `流程` 存储并兼容旧固定字段
- API：`/api/progress/stats`、新建、归档删除、`PUT .../process`

### DORA 手册桥接：联结非拷贝 + 冻结门禁

- `dora-manual-obsidian-bridge`：明确 Junction=同一目录、MCP 不维护第二份 SSOT；体检≠同步拷贝；回填遵守已提密冻结门禁

### 修复桌面快捷方式端口占用与 404

- `start-console.bat`：启动前释放 8765；uvicorn 就绪（`/api/health`）后再打开 `/jobs`
- 新增 `_ensure-port.ps1` / `_wait-and-open.ps1`，避免旧进程导致 `Errno 10048` 与 `{"detail":"Not Found"}`

### 控制台 SPA 升级（Phase 1）

- 新增 `qiuzhao/web/`：React + Vite 四主界面（职位信息 / 我的秋招 / 面试日历 / 面试复盘）+ 更多（入队/学习）
- 新增 `/api/*` JSON：intel / progress / calendar / review / agent / profile / health
- 扩展 `vault_io.py`：面经读写、公司题库、画像、流程 stages、日历聚合
- 旧 Jinja 迁至 `/legacy`；`run.ps1` / `dev.ps1`；构建产物由 FastAPI 托管

### 情报续挖 + 牛客面经续拆

- 方舟脚本恢复可用；新增情报：阿里应用研发/算法、联想 AI Agent、去哪儿全栈、美团 LongCat 通用 Agent（研究向）
- 跳过京东/携程/影石/追觅/即梦等无实质 Agent JD；百度列表复检
- 牛客四帖可见题 → 百度/智象/蚂蚁/米哈游题库；更新 `source_links.json` / 日更清单 / vault 日志

### DORA 面试手册 ↔ Obsidian 桥接 Skill

- 新增 `.cursor/skills/dora-manual-obsidian-bridge/`：联结体检、研究桩、`资料/` 消化回填
- 与 DORA 仓 `dora-interview-manual-sync` 分工（面经进题库 vs 资料进正文）
- 本机联结：`秋招/06_知识库/DORA面试手册` → DORA `docs/interview-manual/`
- **更新**：研究桩改为**仅用户点名**；禁止批量预建；标题用面试官口吻；最多 1–2 条追问句

## 2026-08-07

### 面经图片清洗入库 + 牛客面经探测

- Vault：7 家公司截图题库 + 拼多多/即梦（牛客）+ 牛客综摘索引；手撕清单追加；inbox 归档
- 来源链接库增加牛客面试经验中心；修改日志/来源日志同步

## 2026-08-06

### 混合模式控制台落地

- 新增 `qiuzhao/console/`：FastAPI + Jinja 本机控制台（今日/投递/情报/入队/学习/冲突·ICS/设置）
- 新增 `qiuzhao/scripts/vault_io.py`：读写进度/情报/学习任务/Agent 队列
- Skill：主意图 `处理控制台任务`；用户侧口令收敛为 3 句
- Vault：`秋招/07_任务/`（agent队列 + 学习）；使用说明/职责说明改混合架构
- 启动：`qiuzhao/console/run.ps1` → http://127.0.0.1:8765

### 修复方舟 Playwright 浏览器路径

- 新增 `qiuzhao/scripts/playwright_env.py`：Cursor 沙箱 `PLAYWRIGHT_BROWSERS_PATH` 为空时回退 `%LOCALAPPDATA%\ms-playwright`
- `fetch_fangzhou.py` / `fetch_offerstar.py` 启动前纠偏；冒烟 `status=ok`

### 每日情报更新口令

- Skill 新增主意图 `每日情报更新`（别名刷新情报/日更情报）
- 对齐 vault：`04_情报/每日刷新清单.md` + 使用说明定时提醒说明

## 2026-08-05

### 手撕只汇总到高频清单

- 删除个体手撕详卡；统一写入/回链 高频手撕清单.md；Skill 禁止单题卡


### 处理美团面经截图与手撕清单

- 入库美团 Agent 题库（问题列表）；高频手撕清单；滑动窗口最大值 / 最长拼接字符串详卡
- 截图归档 `_raw/images/{美团,手撕}/`；溯源 `_已处理`

## 2026-08-04

### 面经题库改为仅问题列表

- 公司题库与 Agent 主题卡改为 `#类型` + 编号问题列表（无答案/来源）；溯源仅 `_已处理.md`
- Skill / 文件夹说明 / 使用说明 / 复盘表同步；后续 `处理面经图片` 不再写参考答块

### 面经截图按公司-技术点入库

- 启用口令 `处理面经图片` / `入库图片`；收件箱 `06_知识库/_inbox_images/{公司}/`
- 阿里两图清洗：公司题库 + 手撕「无重复字符最长子串」+ Multi-Agent/工具主题卡
- Skill / DEV / README / 使用说明同步；原图归档 `_raw/images/`

## 2026-08-03

### 科大讯飞 AI agent 补录

- 按用户提供的牛客企业校招页补录 AI agent开发（杭州/北京）；修正仅查飞凡计划的漏检

### 投递入口可点链接 + 排除实习续挖

- 情报卡「投递入口」统一为 `[标签](url)`；模板与 Skill 同步；不收实习/Intern
- 删除：Unity 实习卡、字节 ByteIntern 卡及对应进度行
- 新增正式批：网易雷火智能NPC、大疆 Agent 智能作业、快手快Star Agent 推荐
- 未过关：科大讯飞（仅飞凡方向岗）、百度（抓取失败）

### 牛客深挖 + 来源链接库 + 画像对齐

- 新增 `秋招/04_情报/来源链接库.md` 与 `qiuzhao/data/source_links.json`；口令 `检查来源链接`
- 新增 `qiuzhao/scripts/fetch_nowcoder_schedule.py`（batch 1203 提前批 / 1206+1210 正式批）
- 官网深挖入库：OPPO AI Agent 研发效能、莉莉丝 LLM/Agent 提前批、智元灵犀 Agent
- 画像重评：腾讯 WXG 匹配分 62；阶跃 64
- Skill/DEV/README 同步牛客与提前批/正式批分卡规则

## 2026-07-31

### 画像代表项目拆分 + 学历同步

- Obsidian：`求职画像.md` 代表项目拆为「知识库+任务」「旅行助手」；秋招降级为 Agent 工具实践
- 学历确认：硕士研究生 / 电子信息、人工智能；待补齐去掉学历占位
- 模板：代表项目改为「项目1 / 项目2 / 工具实践」骨架；来源日志 / 修改日志追加
- **未**批量重算情报匹配分

### 完善求职画像（对照 DORA + JD）

- Obsidian：重写 `秋招/00_画像/求职画像.md`（技能六簇、项目叙事、JD 对齐、待补齐与强化清单）
- 模板：`Templates/秋招-求职画像.md` 增补技能矩阵 / 代表项目 / 待补齐骨架
- 来源日志追加本条；**未**批量重算情报匹配分（待用户确认画像后「按新画像重匹配」）
- 不编造学历 / 城市优先 / 薪资 / 竞赛 / 实习

### 大中厂真实填报 + 爬取去重

- 新增 `qiuzhao/scripts/clean_jd_text.py`：清洗重复标题/元数据/重复 JD 段；阶跃星辰卡已重洗
- 腾讯青云·微信大模型 Agent 课题、字节 ByteIntern·AI Agent 开发（计算）官网实质 JD 入库
- 删除无当期 JD 占位：阿里巴巴（官网 0 岗）、智谱AI（2025 FAQ）、示例中厂；快手未抽出 JD 不建卡
- Skill：强制 JD 去噪 + 大厂占位禁止；候选池/来源日志/进度关联同步

### 清除缺 JD + 方舟第二批深挖

- Obsidian：物理删除 24 条 `信息时效: 缺JD` OfferStar 摘要卡
- 第二批官网深挖：四方股份·智能体开发工程师、聚宽投资·大模型应用工程师（校招）过关入库
- 未过关不入库：深信服 / 天锐星通 / 点点互动 / 同花顺 / 百度 / 腾讯青云等
- 临时脚本：`qiuzhao/tmp/deepen_batch2.py`、`deepen_batch2_retry.py`、`deepen_batch2_extra.py`
- 候选池 / 来源日志 / 修改日志同步

### 求职方舟官网深挖 + 无 JD 不入库

- Skill/DEV：强制质量门（无实质 JD 不入库；弃微信扫码链；汇总表须深挖）
- CLI：`qiuzhao/scripts/fetch_fangzhou.py`（Playwright 读 localStorage；`urlType=官网` + 关键词）
- 试点：拼多多 AI Agent / 阶跃星辰 Code Agent / Unity AI Agent 实习写入有效情报
- `requirements.txt` 增加 playwright；推荐 Python 3.10+
- 使用说明 / 候选池 / 来源日志 / 修改日志同步

### OfferStar 真数入库

- Skill/DEV：页面类型分级；主意图 `导入汇总表`；OfferStar 裸链自动走汇总
- CLI：`qiuzhao/scripts/fetch_offerstar.py`（HTTP `current`/`pageSize` 翻页；可选 Playwright）
- 试点：Agent 页 16 条 + AI 页关键词筛选去重追加 → Obsidian `02_情报库`；拼多多官网壳页抽样；未建进度行
- 使用说明 / 候选池 / 来源日志 / 修改日志同步
- **后续**：按新质量门已降级无 JD 卡

## 2026-07-30

### 入口统一与断链修复

- 文件夹首页：`02_情报库/_索引`、`05_投递进度/_索引`、`03_面经/_索引`；知识库 `06_知识库/00_索引`（避免表格内 `_` 斜体拆链）
- 收件箱改为 URL 表格；主意图收敛为「链接入库 / 收集公司 / 加入投递表」；聊天裸 URL 即任务
- Skill / 使用说明 / 文件夹职责 / DEV（真实信息验收门）/ README 同步

## 2026-07-29

### 知识入库与口令接口

- 正式口令契约：`收集秋招`、`提取岗位 <URL>`、`入库知识 <URL>`、`入库粘贴`、`处理岗位/知识收件箱`、`核实情报`；`入库图片` 二期预留
- Obsidian：`秋招/04_情报/链接收件箱.md`；`秋招/06_知识库/`（Agent/手撕/系统设计/公司面经摘录/博客与长文/_raw + `_索引` + 样例卡）
- 模板：`Templates/秋招-知识卡.md`
- CLI：`qiuzhao/scripts/fetch_url.py`（httpx + trafilatura；JSON：`ok|blocked|empty|error`）；更新 `requirements.txt`
- Skill 双副本、使用说明、文件夹职责、DEV、README、来源日志/修改日志同步

## 2026-07-28

### 情报库与投递进度分层

- 拆分数据层：`秋招/02_情报库`（助手 JD/来源）与 `秋招/05_投递进度`（用户可编辑进度）
- 重写 `秋招投递.base`：过滤进度层；列含招聘计划、测评、多轮面试、内推、结果等；视图含按状态/待办/看板
- 看板 Dataview 改读进度时间字段与情报截止；冲突检测覆盖一面~HR面
- Skill：两阶段入库（搜岗→情报；「加入投递表」→进度）、来源追溯与 14 天陈旧标记
- `export_ics.py` 读进度卡时间 + 情报截止；CSS 扩展状态色条与 Bases 柔和样式
- 新增用户文档 `秋招/文件夹与职责说明.md`；更新 DEV/使用说明/候选池/来源日志

### UX 修复与易用性升级

- 修复 Bases：`groupBy` 改为 object（按「优先级」分组）
- Dataview 时间列统一 `dateformat(..., "yyyy-MM-dd HH:mm")`，消除中文区域错位观感
- 投递/面经/模板属性全面中文化；状态/优先级/紧迫度带图标
- 重排 `秋招总览` 为作战台；日程冲突告警与四象限同步中文键
- 新增 CSS 片段 `qiuzhao-dashboard.css`（闪烁圆点）
- Skill 与 `export_ics.py` 改为读写中文键（兼容旧英文键）
- 新增开发文档 [`qiuzhao/DEV.md`](qiuzhao/DEV.md)

### 秋招智能管理助手 · 初版落地

- Obsidian 库建立 `秋招/` 目录：画像、看板、投递、面经、情报
- 新增模板：`Templates/秋招-求职画像|投递卡|面经复盘|面试轮次.md`
- 默认画像：主攻 Agent / LLM 应用开发
- 看板：秋招总览、四象限矩阵、本周日程与冲突
- Bases：`秋招/01_看板/秋招投递.base`
- 样例投递 5 条 + 面经双向链接
- Skill：`qiuzhao-assistant`；ICS 导出脚本
- 使用说明与 Automation 草稿

## 2026-09-03
- 日更：联友科技×2；华为/海艺核实于；拼多多/招行面经

