#!/usr/bin/env python3
"""One-shot ingest: funded startups with shipped products and open campus JDs.

Company gate (all three required before a job is written):
  multi-round public funding, market validation, delivered product
  (software: paying or in-production customers, not a lab demo).

Job gate: campus / 应届, substantive JD, permalink or official apply form,
master-eligible, not embodied / intern-only / WeChat wall.
Does not create 投递进度.
"""

from __future__ import annotations

import re
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
    get_intel_company,
    intel_company_dir,
    qiuzhao_root,
    today_str,
    upsert_company_apply_channel,
    write_note,
)

TODAY = today_str()

COMPANIES: dict[str, dict] = {
    "月之暗面": {
        "档次": "大厂",
        "门户": "https://app.mokahr.com/campus-recruitment/moonshot/148507#/jobs",
        "核实": """- 融资（只记已有公开报道的轮次）：2023-06 天使轮超 2 亿美元，真格基金、红杉中国等；2024-02 A+ 轮超 10 亿美元，红杉中国、小红书、阿里及美团等老股东，投后估值约 25 亿美元。来源：每经网 2024-02-26 https://www.nbd.com.cn/articles/2024-02-26/3256121.html 。2024-08 约 3 亿美元股权融资，腾讯、阿里、高榕创投、今日资本，估值约 33 亿美元。来源：新浪科技 2024-08-15 https://finance.sina.com.cn/tech/roll/2024-08-15/doc-incisvuq3642020.shtml 。此后更大额轮次若报道写「即将完成」或口径互相打架，不写入已交割。
- 市场验证：2023-10 推出并对公众开放的 Kimi 智能助手（每经网同上）。校招官网写每月有数千万专业用户：https://app.mokahr.com/campus-recruitment/moonshot/148507 。
- 生产/交付：Kimi 已作为软件产品对外提供，按「已交付且被实际使用」理解小批量生产，不是实验室 demo。""",
    },
    "语核科技": {
        "档次": "小厂",
        "门户": "https://langcore.cn/join",
        "核实": """- 融资：2023-10 种子轮数百万元，奇绩创坛（官网历程 https://langcore.cn/zh/about ）。2025-08 Pre-A 数千万元，投资方包括奇绩创坛。来源：上海证券报 2026-03-28 https://paper.cnstock.com/html/2026-03/28/content_2193075.htm 。至少两轮公开融资。
- 市场验证：证券报称 2025 年营收突破千万元，服务约二三十家客户，点名上海仪电集团、中远海运集团、唯捷创芯；与中远海运合作中报价周期从 5 个工作日压到半小时。
- 生产/交付：售前数字员工 / LangHub 已在客户业务流程里使用（证券报与官网历程 https://langcore.cn/zh/about ）。软件按已对外交付理解，不是实验室 demo。""",
    },
}

JOBS: list[dict] = [
    {
        "公司": "月之暗面",
        "岗位": "强化学习-大模型算法工程师(RL方向校招)",
        "城市": [],
        "岗位族": "算法",
        "匹配分": 80,
        "投递链接": "https://app.mokahr.com/campus-recruitment/moonshot/148507#/job/8bb1d380-465f-4e21-8d9f-4cd37617d3a3",
        "信息来源": "月之暗面校招官网",
        "要求技能": ["强化学习", "大模型", "Agent", "Python"],
        "匹配理由": "校招全职算法岗，职责含智能体 Agent 与长链推理强化学习，硕士/研究生可投",
        "缺口": "工作城市官网显示为「-」，需再核实；RL 训练经验是加分不是硬门槛",
        "JD": """职位描述
研究基于 Long CoT 的大模型强化学习相关技术，包括算法或系统，实现技术突破，涉及：
方向一：推理能力 Reasoning
方向二：智能体 Agent
同时研究其他通往 AGI/ASI 的前沿技术

任职要求
985/211 高校研究生以上学历或优秀本科生，计算机科学、人工智能、机器学习等相关专业；
熟悉强化学习和大模型相关技术，具有相关实践和研究经验的同学为佳。
有大模型 infra 相关研发经验者优先。
有大模型+Agent 相关研发经验者优先。
有一定的相关研究经历，发表过顶级会议论文者优先，如 ICLR, NeurIPS, CoRL, ICML, CVPR 等；
具备扎实的 Python 编程基础，有优秀的工程能力，具有 ACM 等编程竞赛获奖者优先。
具备良好的团队协作能力和沟通能力。

招聘性质：全职，算法类/AI，校招。发布于 2025-12-23。工作地点官网未给出。投递截止官网未写。""",
    },
    {
        "公司": "月之暗面",
        "岗位": "Post-Training算法研究员(Code)",
        "城市": [],
        "岗位族": "算法",
        "匹配分": 82,
        "投递链接": "https://app.mokahr.com/campus-recruitment/moonshot/148507#/job/8bcd1241-2e42-4f70-8b9c-3ab197119d61",
        "信息来源": "月之暗面校招官网",
        "要求技能": ["后训练", "SFT", "强化学习", "Code Agent", "Python"],
        "匹配理由": "校招全职，职责含 Coding/SWE Agent 的 SFT、RL 与工具环境",
        "缺口": "工作城市官网显示为「-」；英文 JD，偏好已有大模型对齐经验",
        "JD": """Job Description
1. Deeply participate in data processing, cleaning, and optimization for CodeLLM; scientifically improve, filter, and balance the data quality used in LLM pre-training and alignment to enhance the model’s code and agent capabilities during the Pretrain and SFT stages.
2. Actively engage in improving Coding/SWE Agent capabilities through SFT, RL, and building/scaling tools, Docker environments, and tasks; personally gain know-how on how to effectively train an agentic model.
3. Deeply explore methods to enhance the model’s problem-solving ability, aiming for nearly 100% accuracy on simple and medium-level algorithm problems, and maximizing the solving rate of difficult algorithm problems (IOI/ICPC level).
4. Improve user problem-solving rates and satisfaction on Code/SWE-related questions.

Job Requirements
1. Bachelor’s degree or above, preferably in Computer Science, Artificial Intelligence, Automation, Mathematics, or related fields.
2. Solid programming foundation; proficient in Python and/or C++; skilled in PyTorch, TensorFlow, and Hugging Face.
3. Rich hands-on experience in large model pre-training and alignment training, or experience in Code/SWE optimization is preferred.
4. Publication in top-tier conferences or outstanding achievements in machine learning are preferred.
5. Algorithm competition awards (ACM, IOI, NOI, TopCoder) are a plus.
6. Strong sense of responsibility and teamwork.

招聘性质：全职，算法类/AI。岗位名 Kimi Post-Training Algorithm Researcher/Engineer (Code)。发布于 2025-12-23。工作地点与投递截止官网未写。""",
    },
    {
        "公司": "月之暗面",
        "岗位": "大模型算法研究员(预训练校招)",
        "城市": ["北京"],
        "岗位族": "算法",
        "匹配分": 74,
        "投递链接": "https://app.mokahr.com/campus-recruitment/moonshot/148507#/job/e3a6bf00-f9bd-4daa-a03a-f965220c6bf1",
        "信息来源": "月之暗面校招官网",
        "要求技能": ["预训练", "Transformer", "PyTorch", "数据合成"],
        "匹配理由": "27 届可对口的大模型算法校招全职；偏预训练架构与数据，不是应用开发主线",
        "缺口": "职责在模型架构、并行和预训练数据，Agent 应用工程不是主责",
        "JD": """职位描述
深度参与 LLM 的创新模型架构设计与改进，包括 MLP 和 Attention 模块；优化模型并行策略、优化算法、目标函数等方向，提升模型训练效率和推理效果，力争在上下文长度、参数规模和前沿性能上取得 SOTA 级领先水平。
与 Infra 团队紧密合作，优化训练框架，提高 GPU 使用效率和训练任务的稳定性。
高效获取、清洗、构造和合成高质量的预训练数据，持续探索可规模化的数据合成方法。
参与模型训练任务的监控，设计关键评测指标，确保模型健康成长并取得预期效果。

职位要求
985/211/海外高校研究生学历以上或优秀本科生，专业为 CS/AI/ML/CV/NLP/Math 或相关专业。
熟悉 Transformer 架构及相关大模型技术，并有相应的研究或实践经验，具有真实的预训练或模型 Scaling 经验者优先。
扎实的编程能力，精通数据结构与算法设计，熟练使用深度学习框架（PyTorch, JAX 等）。
有高性能计算经验者优先，熟悉 Triton、CUDA 等 GPU 编程与优化者优先。
在顶级学术会议（如 ICLR、NeurIPS、ICML、CVPR、ACL 等）上发表过论文者优先。
具备 ACM/IOI/NOI/TopCoder 等算法竞赛获奖经历者优先。

招聘性质：全职校招，算法类/AI，工作地点北京市。发布于 2026-08-14。投递截止官网未写。""",
    },
    {
        "公司": "语核科技",
        "岗位": "Agent全栈工程师",
        "城市": ["上海"],
        "岗位族": "Agent",
        "匹配分": 90,
        "投递链接": "https://langcore.feishu.cn/share/base/form/shrcnnmzFDd6XUBAcaRjh08kvxf",
        "信息来源": "语核科技官网加入我们",
        "要求技能": ["Agent", "Python", "TypeScript", "工具调用"],
        "匹配理由": "官网在招且标注校招，职责是 Agent 工作台、工具调用和多 Agent 协同的工程落地",
        "缺口": "同一卡片也标了实习；投递是全公司共用飞书表单，须在表单写明岗位名。截止日官网未写",
        "extra_checks": ["投递表单须填写岗位名「Agent 全栈工程师」"],
        "JD": """岗位职责
负责 Agent 产品的工程化落地，承担前后端全链路实现，包括 Agent 工作台、任务看板、会话界面、API 服务等核心模块。
为 Agent 运行时构建高质量的工程基础设施：工具调用封装、文件系统管理、结构化上下文维护、多 Agent 协同通信机制，确保模型能力在生产环境中稳定发挥。
参与建设 Agent 的测试与评估体系，设计 E2E 测试用例，构建运行日志与行为追踪机制，在非确定性环境下持续提升产品稳定性。
在团队中实践 AI 驱动的研发流程，用 Agent 完成绝大部分 Coding 工作，核心价值在于系统设计、任务拆解、验收与迭代。

任职要求
计算机科学、软件工程或相关专业应届毕业生（本科/硕士均可）。
有独立完成过完整 Agent 应用的经历：能描述工具调用链路、上下文管理策略，以及遇到的具体工程问题和解法。
熟练掌握 Python 或 TypeScript，有前后端开发经验，能独立搭建可部署的服务（不只是跑通 demo）。
日常深度使用 Claude Code、Cursor 等 AI 编程工具，能讲清楚自己用 Agent 完成真实任务的具体 workflow。
有 GitHub 项目且有实际 commit 记录（AI/Agent 相关优先）。
具备强学习能力与抗压能力。

页面标签：产研 / 校招 / 实习 / 社招。按应届要求收录校招。工作地点上海徐汇。投递截止官网未写。JD 摘自 https://langcore.cn/join 岗位弹层，核实日见卡片。""",
    },
    {
        "公司": "语核科技",
        "岗位": "Harness工程师",
        "城市": ["上海"],
        "岗位族": "Agent",
        "匹配分": 86,
        "投递链接": "https://langcore.feishu.cn/share/base/form/shrcnnmzFDd6XUBAcaRjh08kvxf",
        "信息来源": "语核科技官网加入我们",
        "要求技能": ["Agent", "运行时", "上下文", "评测"],
        "匹配理由": "校招应届岗，做 Agent 调度、运行时脚手架和多 Agent 上下文，属于智能体工程",
        "缺口": "卡片同时标实习；与 Agent 全栈共用一个飞书表单。截止日官网未写",
        "extra_checks": ["投递表单须填写岗位名「Harness 工程师」"],
        "JD": """岗位职责
参与 Agent 调度与推理模块的研发，协助优化 Agent 启发式推理链路的逻辑准确性。
负责编写高度 Agent 可用的运行时脚手架，提升 Agent 对外部环境的感知和操作能力。
参与维护 Agent 评估系统，编写测试脚本与场景评估用例，帮助团队捕获大模型在非确定性输出下的边界问题。
维护 Agent 系统的结构化 Context 和文件系统记忆信息，确保多 Agent 协同过程中的信息不丢失。

任职要求
计算机科学、人工智能或相关专业的应届毕业生（本科/硕士/博士均可，欢迎有极客精神的优秀应届生）。
对 Agent 有较深刻洞察与应用经验。拥有极强的系统拆解能力，能清晰描述复杂流程中的输入、输出与边界条件并使用 Agent 自动化。
编程基础扎实，熟练掌握至少一门主流开发语言。
对前沿 AI Agent 技术充满热情，有开发大模型相关应用的经历（拥有高星 AI 相关开源项目贡献者优先）。
具备极强的学习能力、抗压能力与跨团队沟通能力。

页面标签：产研 / 校招 / 实习。任职要求写应届毕业生，按校招收录，不单开实习卡。博士不是硬门槛。工作地点上海徐汇。投递截止官网未写。JD 摘自 https://langcore.cn/join 岗位弹层。""",
    },
]


def _safe_stem(company: str, title: str) -> str:
    bad = '\\/:*?"<>|\n\r\t'
    s = f"{company}-{title}"
    for ch in bad:
        s = s.replace(ch, "-")
    return s.replace("（", "(").replace("）", ")")[:120]


def _attach_company_evidence(company: str) -> None:
    spec = COMPANIES[company]
    card = get_intel_company(company)
    if card is None:
        return
    snippet = spec["核实"].strip()
    if "生产/交付" in (card.body or ""):
        return
    if "## 备注" not in (card.body or ""):
        body = (card.body or "").rstrip() + "\n\n## 备注\n\n" + snippet + "\n"
    else:
        body = (card.body or "").rstrip() + "\n" + snippet + "\n"
    card.meta["更新于"] = TODAY
    write_note(card.path, card.meta, body)


def ingest_one(job: dict) -> Path | None:
    company = job["公司"]
    title = job["岗位"]
    jd = clean_jd(job["JD"], title)
    skip_phd, phd_reason = is_phd_only(title, jd)
    if skip_phd:
        print(f"SKIP phd {company}/{title}: {phd_reason}")
        return None
    skip_body, body_reason = is_embodied_mismatch(title, jd)
    if skip_body:
        print(f"SKIP embodied {company}/{title}: {body_reason}")
        return None
    spec = COMPANIES[company]
    ensure_intel_company(company, tier=spec["档次"], portal=spec["门户"])
    upsert_company_apply_channel(
        company,
        url=spec["门户"],
        channel_type="官网",
        name="校招门户",
        tier=spec["档次"],
        portal=spec["门户"],
    )
    _attach_company_evidence(company)
    stem = _safe_stem(company, title)
    path = intel_company_dir(company) / f"{stem}.md"
    if path.exists():
        print(f"SKIP exists {path}")
        return None
    meta = {
        "type": "qiuzhao-intel-job",
        "公司": company,
        "岗位": title,
        "公司档次": spec["档次"],
        "岗位族": job["岗位族"],
        "招聘状态": "待核实",
        "投递优先级": "冲刺" if spec["档次"] == "大厂" else "练手优先",
        "招聘计划": "校招正式批",
        "城市": job.get("城市") or [],
        "匹配分": int(job["匹配分"]),
        "投递链接": job["投递链接"],
        "岗位简介": jd,
        "信息来源": job["信息来源"],
        "来源链接": [job["投递链接"], spec["门户"]],
        "要求技能": job["要求技能"],
        "已具备": ["Agent", "RAG", "Python"],
        "待补齐": [],
        "开放日": None,
        "投递截止": None,
        "核实于": TODAY,
        "信息时效": "待核实",
        "需再核实": True,
        "tags": ["秋招", "情报", "初创"],
        "更新于": TODAY,
    }
    enrich_intel_meta(meta)
    body = default_intel_job_body(
        company=company,
        heading=f"{company} · {title}",
        apply_url=meta["投递链接"],
        portal_url=spec["门户"],
        jd=jd,
        why=job["匹配理由"],
        gap=job["缺口"],
        extra_checks=job.get("extra_checks") or [],
    )
    write_note(path, meta, body)
    print(f"OK {path}")
    return path


def append_source_log(paths: list[Path]) -> None:
    log_path = qiuzhao_root() / "04_情报" / "来源日志.md"
    text = log_path.read_text(encoding="utf-8")
    lines = [
        f"\n## {TODAY} · 初创（多轮融资且已交付）校招对口岗\n",
        "- 公司门槛：至少两轮公开融资、有付费/使用证据、产品已对外交付。不满足的不入库。\n",
        "- 岗位门槛：官网单岗 JD；滤掉实习包装、具身、博士硬门槛、微信墙、纯训练框架/推理 Infra。未加入投递表。\n",
        "- 通过公司门槛但本轮没有可入库对口正式岗：深势科技（校园招聘入口里 Agent/大模型命中均为实习）、面壁智能（公开校招多为实习或邮箱人才计划）、实在智能（高校就业网只有方向清单，无单岗职责+要求）、零一万物（飞书「智能体专家」在社招站点且职称为专家）。\n",
        f"- 新入库 {len(paths)} 岗。\n",
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
        path = ingest_one(job)
        if path:
            written.append(path)
    if written:
        append_source_log(written)
    print("DONE", len(written))


if __name__ == "__main__":
    main()
