#!/usr/bin/env python3
"""One-shot ingest: still-open 2027 bank campus tech/AI jobs (2026-10-11)."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from clean_jd_text import clean_jd  # noqa: E402
from jd_edu_gate import is_phd_only  # noqa: E402
from jd_embodied_gate import is_embodied_mismatch  # noqa: E402
from vault_io import (  # noqa: E402
    default_intel_job_body,
    enrich_intel_meta,
    ensure_intel_company,
    intel_company_dir,
    qiuzhao_root,
    today_str,
    upsert_company_apply_channel,
    write_note,
)

TODAY = today_str()

JOBS: list[dict] = [
    {
        "公司": "兴业银行",
        "岗位": "科技专项人才（人工智能方向）",
        "城市": ["福州", "上海"],
        "岗位族": "算法",
        "匹配分": 82,
        "投递截止": "2026-10-25",
        "投递链接": "https://job.cib.com.cn/",
        "门户": "https://job.cib.com.cn/",
        "来源链接": [
            "https://job.cib.com.cn/portal/#/noticeDetails?id=1279829990553391104",
            "https://www.xyyh.com.cn/cn/aboutCIB/about/jobs/2026/20260922_1.html",
        ],
        "信息来源": "兴业银行官网公告+招聘门户",
        "JD": """岗位职责
主要为人工智能技术研发与应用提供人才储备，录用后直接定岗总行相关科技部门。

任职要求
1、硕士及以上学历，主要面向境内外应届毕业生；境内院校毕业生应于2027年8月31日前取得毕业证、学位证；境外院校毕业生应为2026年1月至2027年8月之间毕业，并在报到时取得国家教育部学历学位认证。
2、遵纪守法、诚实守信，无违法、违规、违纪等不良记录。
3、具有良好的学习和研究分析能力、语言与文字表达能力、组织协调能力和团结合作意识，能够承担工作压力。
4、应达到大学英语六级（CET-6）425分及以上（或同等英语考试成绩）。
5、其他应聘条件见官网岗位需求表附件。

报名时间：即日起至2026年10月25日。
投递：https://job.cib.com.cn/""",
    },
    {
        "公司": "兴业银行",
        "岗位": "科技研发中心研发岗（智能体能力建设）",
        "城市": ["福州", "上海"],
        "岗位族": "Agent",
        "匹配分": 88,
        "投递截止": "2026-10-25",
        "投递链接": "https://job.cib.com.cn/",
        "门户": "https://job.cib.com.cn/",
        "来源链接": [
            "https://job.cib.com.cn/portal/#/noticeDetails?id=1279829990553391104",
            "https://www.xyyh.com.cn/cn/aboutCIB/about/jobs/2026/20260922_1.html",
        ],
        "信息来源": "兴业银行官网公告+招聘门户",
        "JD": """岗位职责
主要为软件产品需求分析、系统设计、代码开发、智能体能力建设、研发运维等工作提供人才储备（总行科技研发中心）。

任职要求
1、硕士及以上学历，主要面向境内外应届毕业生；境内院校毕业生应于2027年8月31日前取得毕业证、学位证；境外院校毕业生应为2026年1月至2027年8月之间毕业，并在报到时取得国家教育部学历学位认证。
2、遵纪守法、诚实守信，无违法、违规、违纪等不良记录。
3、具有良好的学习和研究分析能力、语言与文字表达能力、组织协调能力和团结合作意识，能够承担工作压力。
4、应达到大学英语六级（CET-6）425分及以上（或同等英语考试成绩）。
5、其他应聘条件见官网岗位需求表附件。

报名时间：即日起至2026年10月25日。
投递：https://job.cib.com.cn/""",
    },
    {
        "公司": "中国光大银行",
        "岗位": "管理培训生岗（人工智能方向）",
        "城市": ["北京"],
        "岗位族": "算法",
        "匹配分": 86,
        "投递截止": "2026-11-08",
        "投递链接": "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
        "门户": "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
        "来源链接": [
            "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
            "https://yinhangzhaopin.com/guangdayh/2026-10-08/227011.htm",
        ],
        "信息来源": "光大银行招聘门户+银行招聘网转载公告（待与官网岗位页再核）",
        "需再核实": True,
        "JD": """岗位职责
作为总行人工智能相关技术人才储备：
1、根据全行数字化转型需要，进行前沿大模型技术、人工智能算法、图算法、深度学习算法、机器学习算法的研究；
2、负责大模型技术、人工智能算法、图算法、深度学习算法、机器学习算法在银行应用场景的嵌入落地工作。

任职要求
1、大学本科及以上学历（以官网岗位页为准）；境内/境外院校应届毕业生，毕业时间在2026年1月1日至2027年7月31日之间，并按时报到取得相应证书/认证。
2、专业：人工智能、计算机科学、统计学、数学等金融科技类相关专业。
3、应聘者须为最高学历后初次就业，未与其他单位建立劳动关系，未参加社会保险。
截止日期：2026-11-08；工作地点：北京市。""",
    },
    {
        "公司": "中国光大银行",
        "岗位": "金融科技岗（系统开发方向）",
        "城市": ["雄安"],
        "岗位族": "研发应用",
        "匹配分": 72,
        "投递截止": "2026-11-08",
        "投递链接": "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
        "门户": "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
        "来源链接": [
            "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
            "https://yinhangzhaopin.com/guangdayh/2026-10-08/227016.htm",
        ],
        "信息来源": "光大银行招聘门户+银行招聘网转载公告（待与官网岗位页再核）",
        "需再核实": True,
        "JD": """岗位职责（总行科技研发中心）
1、按要求积极参加岗位培训学习和考试，学习并遵守行内、部内各项规章制度；
2、负责银行软件产品研发项目计划及质量目标制定、执行及监督，做好研发管理；
3、负责参与银行软件产品的需求分析、系统设计、编码开发、技术测试、发布部署等研发相关工作；
4、负责为银行软件产品提供技术支持服务；
5、参与新技术调研与研发、系统性能调优及系统重构等工作。

任职要求
1、硕士研究生及以上学历；毕业时间在2026年1月1日至2027年7月31日之间。
2、专业：计算机类、电子信息类、计算机科学与技术类、信息与通信工程类、软件工程类、统计学类、数学类、控制科学与工程类、管理科学与工程类等金融科技类相关专业。
3、应聘者须为最高学历后初次就业，未与其他单位建立劳动关系，未参加社会保险。
截止日期：2026-11-08；工作地点：雄安新区。""",
    },
    {
        "公司": "中国光大银行",
        "岗位": "金融科技岗（数据开发方向）",
        "城市": ["北京"],
        "岗位族": "研发应用",
        "匹配分": 74,
        "投递截止": "2026-11-08",
        "投递链接": "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
        "门户": "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
        "来源链接": [
            "https://eoap.cebbank.com/uiap/wt/CEB/zpzh/campus",
            "https://yinhangzhaopin.com/guangdayh/2026-10-08/227014.htm",
        ],
        "信息来源": "光大银行招聘门户+银行招聘网转载公告（待与官网岗位页再核）",
        "需再核实": True,
        "JD": """岗位职责（总行数据资产管理部）
1、按要求积极参加岗位培训学习和考试，学习并遵守行内、部内各项规章制度；
2、负责数据采集、清洗、加工、应用等数据开发场景的需求分析、系统设计、编码开发、技术测试、发布部署等相关工作；
3、负责使用JAVA、Python等编程语言完成面向银行数据交付领域的开发工作；
4、负责银行基于Hadoop、Spark、Flink等技术的数据产品设计、开发和技术支持；
5、参与大数据领域的技术研究、数据平台建设、数据处理性能调优等工作。

任职要求
1、硕士研究生及以上学历；毕业时间在2026年1月至2027年7月的境内外高校毕业生。
2、专业为金融科技相关理工科方向（以官网岗位页为准）。
截止日期：2026-11-08；工作地点：北京市。""",
    },
    {
        "公司": "上海银行",
        "岗位": "总行金融科技岗位（算法工程）",
        "城市": ["上海", "苏州"],
        "岗位族": "Agent",
        "匹配分": 92,
        "投递截止": "2026-11-22",
        "投递链接": "https://bosc.zhiye.com/campus/detail?jobAdId=61129aaf-5b02-4d2f-93fe-fe98592b7846",
        "门户": "https://bosc.zhiye.com/campus/jobs",
        "来源链接": [
            "https://bosc.zhiye.com/campus/detail?jobAdId=61129aaf-5b02-4d2f-93fe-fe98592b7846",
            "https://bosc.zhiye.com/campus/jobs",
        ],
        "信息来源": "上海银行官网北森校招详情",
        "JD": """岗位职责
1、参与RAG检索增强、文档解析等基础大模型应用模块的开发与迭代，协助搭建应用基础能力底座。
2、负责业务数据清洗、数据集整理、Prompt调优等工作，协助解决大模型幻觉、准确率不足等问题，持续优化模型场景适配效果。
3、参与智能体工具调用、基础任务规划等功能的开发与调试，协助完成智能体基础场景落地与功能迭代。
4、协助完成大模型服务封装、容器化部署、推理性能测试等工程化工作。
5、跟踪学习大模型前沿技术、开源项目与行业方案，参与团队技术预研、试点验证工作。

任职资格
1、大学本科及以上学历应届毕业生，毕业时间为2026年1月1日至2027年7月31日，须在对应时间内取得毕业证（境外院校需取得教育部留学服务中心认证），且为初次就业。
2、理工类专业，包括但不限于计算机、软件工程、数学、统计学。
3、技术能力：熟练掌握Python；了解FastAPI等基础后端框架；掌握深度学习/机器学习基础，理解Transformer；熟悉大模型概念，了解RAG、Prompt工程、模型微调；熟练使用PyTorch/TensorFlow之一；了解Linux与Docker。
4、有大模型相关科研/实习/竞赛/开源贡献者优先。""",
    },
    {
        "公司": "上海银行",
        "岗位": "总行金融科技岗位（应用开发）",
        "城市": ["上海", "苏州"],
        "岗位族": "研发应用",
        "匹配分": 76,
        "投递截止": "2026-11-22",
        "投递链接": "https://bosc.zhiye.com/campus/detail?jobAdId=b04060c2-a61e-4bd1-8197-cb04504abcaa",
        "门户": "https://bosc.zhiye.com/campus/jobs",
        "来源链接": [
            "https://bosc.zhiye.com/campus/detail?jobAdId=b04060c2-a61e-4bd1-8197-cb04504abcaa",
        ],
        "信息来源": "上海银行官网北森校招详情",
        "JD": """岗位职责
1、负责银行经营、管理等各类应用系统的开发、调优工作。
2、负责应用系统的技术资产管理，制定和完善开发规范。
3、负责项目可行性分析、需求分析及设计，并对项目技术工作进行有效管理。
4、关注金融科技架构系统变化趋势，参与应用系统架构设计和优化。

任职资格
1、大学本科及以上学历应届毕业生，毕业时间为2026年1月1日至2027年7月31日，须在对应时间内取得毕业证（境外院校需取得教育部留学服务中心认证），且为初次就业。
2、理工类专业，包括但不限于计算机、软件工程、电子信息工程、通信工程、自动化、控制工程。
3、熟练使用JAVA、C/C++至少一种开发语言，且熟悉至少一种数据库。
4、具备Windows/Linux/Unix、Android或iOS、React Native或HTML5、机器学习等相关能力之一者更佳。""",
    },
    {
        "公司": "上海银行",
        "岗位": "总行金融科技岗位（数据开发）",
        "城市": ["上海"],
        "岗位族": "研发应用",
        "匹配分": 80,
        "投递截止": "2026-11-22",
        "投递链接": "https://bosc.zhiye.com/campus/detail?jobAdId=85ed827a-aca4-4507-8240-193759eaab2a",
        "门户": "https://bosc.zhiye.com/campus/jobs",
        "来源链接": [
            "https://bosc.zhiye.com/campus/detail?jobAdId=85ed827a-aca4-4507-8240-193759eaab2a",
        ],
        "信息来源": "上海银行官网北森校招详情",
        "JD": """岗位职责
1、负责监管报送系统的全流程开发，含业务系统采集数据、加工清洗、校验核对及数据批量报送。
2、建立质量监控体系，及时发现数据异常，排查并解决数据问题。
3、负责数据加工链路的开发与维护，梳理并优化数据处理流程，减少重复计算，节省计算资源。
4、探索大模型在数据研发领域的应用，包括ETL代码自动生成、智能数据质量检测、自然语言数据查询等方向。
5、结合AI大模型参与平台智能模块的开发与优化，提升智能化水平。

任职资格
1、大学本科及以上学历应届毕业生，毕业时间为2026年1月1日至2027年7月31日。
2、理工类专业，包括但不限于计算机、软件工程、电子信息工程、通信工程、自动化、控制工程。
3、具备Hadoop生态技术栈能力，了解Hive/Spark/Flink等大数据计算引擎；具备一定的SQL性能调优与数据链路优化经验。
4、了解大模型技术在数据研发领域的应用者优先。""",
    },
    {
        "公司": "上海银行",
        "岗位": "总行金融科技岗位（数据分析）",
        "城市": ["上海"],
        "岗位族": "算法",
        "匹配分": 78,
        "投递截止": "2026-11-22",
        "投递链接": "https://bosc.zhiye.com/campus/detail?jobAdId=b17750ed-b6e5-429c-89be-95a44179567a",
        "门户": "https://bosc.zhiye.com/campus/jobs",
        "来源链接": [
            "https://bosc.zhiye.com/campus/detail?jobAdId=b17750ed-b6e5-429c-89be-95a44179567a",
        ],
        "信息来源": "上海银行官网北森校招详情",
        "JD": """岗位职责
1、负责数据的清洗和整合，为数据分析提供高质量的数据源。
2、深度参与数据应用系统的规划，推动业务需求转化为可落地的数据应用方案。
3、构建用户分层运营策略体系，设计营销推荐方案，搭建风险监测体系。
4、搭建经营管理指标体系，运用统计分析辅助业务决策。

任职资格
1、大学本科及以上学历应届毕业生，毕业时间为2026年1月1日至2027年7月31日。
2、理工类专业，包括但不限于计算机、软件工程、数学、统计学。
3、熟练掌握Java、SQL、Python中至少两种；熟练传统机器学习算法，熟悉至少一种深度学习框架，掌握BI工具。
4、有营销风控模型、数据应用系统建设等项目经验者优先。""",
    },
    {
        "公司": "北京银行",
        "岗位": "总行科技英才（软件开发含人工智能方向）",
        "城市": ["北京"],
        "岗位族": "研发应用",
        "匹配分": 80,
        "投递截止": "2026-10-15",
        "投递链接": "https://bankofbeijing.zhiye.com/campus/detail?jobAdId=280f1858-4bc3-4e7f-8339-f6ba2e3949e0",
        "门户": "https://bankofbeijing.zhiye.com/campus/jobs",
        "来源链接": [
            "https://bankofbeijing.zhiye.com/campus/detail?jobAdId=280f1858-4bc3-4e7f-8339-f6ba2e3949e0",
            "https://bankofbeijing.zhiye.com/campus/jobs",
        ],
        "信息来源": "北京银行官网北森校招详情",
        "JD": """招聘机构：北京银行总行信息科技部门

招聘岗位
1、软件开发（银行业务系统开发方向，移动应用开发方向，技术平台开发方向，人工智能开发方向，大数据应用开发方向，系统测试方向）；
2、系统运营（信息安全方向，网络规划及管理方向，数据库管理方向，大数据运营方向，运维开发方向）。

招聘对象
1、本科（含）以上学历；境内外高校最高学历毕业时间均为2026年1月至2027年7月；
2、专业范围：计算机、软件工程、电子信息、大数据、信息安全、数学、统计等相关专业。

应聘条件（摘要）
诚实守信，遵纪守法；国内院校毕业生应在2027年7月31日前取得毕业证、学位证；具备良好计算机/软件技术基础与编程能力者优先；熟悉大数据/机器学习基础原理者优先；掌握容器及云计算相关技术者优先。
报名截止：2026-10-15 24:00；每位应聘者最多投递3个岗位。""",
    },
    {
        "公司": "杭州银行",
        "岗位": "总行信息技术部培训生（人工智能方向）",
        "城市": ["杭州"],
        "岗位族": "Agent",
        "匹配分": 90,
        "投递截止": "2026-10-25",
        "投递链接": "https://myjob.hzbank.com.cn/hzzp-apply-web/static/index.html#/employDesc/27158946",
        "门户": "https://myjob.hzbank.com.cn/",
        "来源链接": [
            "https://myjob.hzbank.com.cn/hzzp-apply-web/static/index.html#/employDesc/27158946",
            "https://myjob.hzbank.com.cn/hzzp-apply-web/static/index.html#/employ/school",
        ],
        "信息来源": "杭州银行招聘官网岗位详情",
        "JD": """职位描述
主要从事人工智能、大模型、算法建模等方向的研究和金融场景的创新应用建设，未来培养方向为信息技术领域专业骨干人才。

任职要求
1、境内外院校优秀应届硕士研究生，其中境内院校毕业时间在2027年1月至2027年7月之间，应于2027年7月31日前取得毕业证和学位证；境外院校毕业时间在2026年1月至2027年7月之间，应于2027年7月31日前取得毕业证和教育部学历学位认证；
2、学历要求：硕士及以上；
3、人工智能、计算机科学与技术、智能科学技术、电子信息等相关专业；
4、了解人工智能、大模型、算法、智能体等相关技术并对其中一个方向有深入研究，熟练掌握Java或Python等至少一门开发语言；
5、具备一门及以上外语的听说读写能力，并能够提供相应的能力证明材料；
6、综合素质好，学习能力强，具有较好的沟通能力、服务意识和团队合作精神；
7、遵纪守法，诚实守信，无不良行为记录；
8、身心健康，符合我行亲属回避制度规定。

截止时间：2026-10-25；工作地点：杭州。""",
    },
    {
        "公司": "四川银行",
        "岗位": "总行金融科技类（人工智能与大数据方向）",
        "城市": ["成都"],
        "岗位族": "算法",
        "匹配分": 84,
        "投递截止": "2026-10-31",
        "投递链接": "https://scbank.hotjob.cn/",
        "门户": "https://scbank.hotjob.cn/",
        "来源链接": [
            "https://scbank.hotjob.cn/",
            "https://www.shanganclaw.com/jobs/1266191/",
        ],
        "信息来源": "四川银行招聘门户+公开转载岗位说明（待官网单岗 permalink 再核）",
        "需再核实": True,
        "JD": """岗位职责
具备人工智能与大数据方向的研究与应用能力，根据工作需要，参与人工智能算力/模型/算法研发、大数据平台的数据处理与分析、前沿技术跟踪与金融场景创新应用、科研项目申报与成果转化，推动人工智能和大数据技术与金融领域深度融合。

任职要求
1、全日制硕士研究生及以上学历并取得相应学位（本卡对应硕士可投的金融科技类通道；博士专项另轨，不按博士硬门槛收录）。
2、毕业时间应在2026年1月1日至2027年7月31日期间。
3、专业：计算机科学与技术、人工智能、大数据科学与工程、机器学习、数据挖掘、统计学、数学等相关专业。
4、每人限报1个岗位。
报名截止：2026-10-31 18:00；工作地点：成都（总行）。""",
    },
    {
        "公司": "四川银行",
        "岗位": "总行金融科技类（信息科技方向）",
        "城市": ["成都"],
        "岗位族": "研发应用",
        "匹配分": 70,
        "投递截止": "2026-10-31",
        "投递链接": "https://scbank.hotjob.cn/",
        "门户": "https://scbank.hotjob.cn/",
        "来源链接": [
            "https://scbank.hotjob.cn/",
            "https://yhks.cn/y.php/a/16596",
        ],
        "信息来源": "四川银行招聘门户+公开转载公告（待官网单岗 permalink 再核）",
        "需再核实": True,
        "JD": """岗位职责
总行金融科技类信息科技方向：面向信息科技相关专业背景人才，参与银行信息系统建设、软件研发/运维能力培养与金融科技落地（以官网岗位资格要求为准）。

任职要求
1、全日制硕士研究生及以上学历并取得相应学位。
2、毕业时间应在2026年1月1日至2027年7月31日期间。
3、专业方向含计算机软件（软件工程）、信息安全、大数据、数据分析、数学和统计学等（以官网为准）。
4、每人限报1个岗位。
报名截止：2026-10-31 18:00；工作地点：成都（总行）。""",
    },
]


def _safe_stem(company: str, title: str) -> str:
    bad = '\\/:*?"<>|\n\r\t'
    s = f"{company}-{title}"
    for ch in bad:
        s = s.replace(ch, "-")
    return s.replace("（", "(").replace("）", ")")[:120]


def ingest_one(job: dict) -> Path | None:
    company = job["公司"]
    title = job["岗位"]
    jd = clean_jd(job["JD"], job["岗位"])
    skip_phd, phd_reason = is_phd_only(title, jd)
    if skip_phd:
        print(f"SKIP phd {company}/{title}: {phd_reason}")
        return None
    skip_emb, emb_reason = is_embodied_mismatch(title, jd)
    if skip_emb:
        print(f"SKIP embodied {company}/{title}: {emb_reason}")
        return None

    ensure_intel_company(company, tier="央国企", portal=job.get("门户") or "")
    upsert_company_apply_channel(
        company,
        url=job.get("门户") or job["投递链接"],
        channel_type="官网",
        name="校招门户",
        tier="央国企",
        portal=job.get("门户") or "",
    )

    stem = _safe_stem(company, title)
    path = intel_company_dir(company) / f"{stem}.md"
    meta = {
        "type": "qiuzhao-intel-job",
        "公司": company,
        "岗位": title,
        "公司档次": "央国企",
        "岗位族": job.get("岗位族") or "其他",
        "招聘状态": "热招中",
        "投递优先级": "保底",
        "招聘计划": "校招正式批",
        "城市": job.get("城市") or [],
        "匹配分": int(job.get("匹配分") or 70),
        "投递链接": job["投递链接"],
        "岗位简介": jd,
        "信息来源": job.get("信息来源") or "官网深挖",
        "来源链接": list(job.get("来源链接") or [job["投递链接"]]),
        "要求技能": job.get("要求技能")
        or ["Python", "大模型应用", "金融科技"],
        "已具备": ["Agent", "RAG", "Python"],
        "待补齐": [],
        "开放日": None,
        "投递截止": job.get("投递截止"),
        "核实于": TODAY,
        "信息时效": "已核实" if not job.get("需再核实") else "待核实",
        "需再核实": bool(job.get("需再核实")),
        "tags": ["秋招", "情报", "银行", "央国企"],
        "更新于": TODAY,
    }
    enrich_intel_meta(meta)
    body = default_intel_job_body(
        company=company,
        heading=f"{company} · {title}",
        apply_url=meta["投递链接"],
        portal_url=job.get("门户") or "",
        jd=jd,
        why=job.get("匹配理由") or "银行科技/AI 技术岗，对齐画像央国企保底池",
        gap="银行业务与合规场景需补；部分岗偏传统研发栈",
        extra_checks=[]
        if job.get("投递截止")
        else ["投递截止（官网未给出明确日期，禁止编造）"],
    )
    write_note(path, meta, body)
    print(f"OK {path}")
    return path


def append_source_log(paths: list[Path]) -> None:
    import re

    log_path = qiuzhao_root() / "04_情报" / "来源日志.md"
    text = log_path.read_text(encoding="utf-8")
    lines = [
        f"\n## {TODAY} · 银行秋招仍开放技术/AI 岗收集\n",
        "- 范围：国有大行/股份行/城商行等仍开放报名的校招技术向岗位；跳过已入库饱和银行重复岗、微信墙、纯营销/柜员、具身、博士硬门槛。\n",
        f"- 新入库 {len(paths)} 岗（未加入投递表）。\n",
    ]
    for p in paths:
        rel = p.relative_to(qiuzhao_root().parent).as_posix()
        lines.append(f"- [[{rel}|{p.stem}]]\n")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            end = end + 4
            head = re.sub(r"更新于:.*", f"更新于: '{TODAY}'", text[:end], count=1)
            log_path.write_text(head + "".join(lines) + text[end:], encoding="utf-8")
            return
    log_path.write_text(text + "".join(lines), encoding="utf-8")


def main() -> None:
    written: list[Path] = []
    for job in JOBS:
        p = ingest_one(job)
        if p:
            written.append(p)
    append_source_log(written)
    print("DONE", len(written))


if __name__ == "__main__":
    main()
