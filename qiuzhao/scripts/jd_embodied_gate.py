#!/usr/bin/env python3
"""Embodied-intelligence / robot-control gate for fall-recruitment JDs.

Portrait is Agent / LLM application. Embodied, VLA, robot control, sim/real
manipulation are too low-level and must be skipped. Pure LLM Agent / RAG /
agent-platform jobs stay even if the company also builds robots.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Job title itself is embodied / physical-robot / VLA.
TITLE_SKIP_RE = re.compile(
    r"具身|物理\s*AI|VLA|机器人控制|人形机器人|灵巧手|末端执行|"
    r"Embodied|Sim2Real",
    re.I,
)

DUTY_SPLIT_RE = re.compile(
    r"(?:任职资格|任职要求|职位要求|岗位要求|加分项)\s*[:：]?",
)

# Core duties (not 加分项 / 支撑…等场景) point to embodied work.
DUTY_SKIP_RE = re.compile(
    r"具身智能\s*Agent|具身\s*Agent|Embodied\s*Agent|Agentic\s*OS|"
    r"机器人整身控制|整身控制|末端执行|机械臂|"
    r"真机(?:平台|部署|联调|开发)|Sim2Real|"
    r"Isaac\s*Sim|MuJoCo|"
    r"机器人智能体|物理\s*AI\s*Agent|"
    r"移动机器人场景|机器人本体|"
    r"ROS\s*/?\s*ROS2|ROS2|"
    r"VLA\s*(?:模型|训练|落地|与)|"
    r"实体交互|仿真操作|操作技能学习|"
    r"具身智能(?:算法|研究|控制)",
    re.I,
)

# Keep: chip/HPC "support LLM / 自动驾驶 / 具身智能 scenarios";
# collector notes; camera 加分项 视觉具身智能.
KEEP_CONTEXT_RE = re.compile(
    r"支撑.{0,24}具身|等(?:核心|关键)场景|缺口：.{0,12}具身|"
    r"视觉具身智能|具身/Physical\s*Agent\s*产品经理|"
    r"理解SOTA.{0,40}VLA",
    re.I,
)


def _duty_blob(title: str, jd: str) -> str:
    text = jd or ""
    text = re.split(r"\n\s*备注\s*[：:]", text, maxsplit=1)[0]
    parts = DUTY_SPLIT_RE.split(text, maxsplit=1)
    duty = parts[0] if parts else text
    return f"{title or ''}\n{duty}"


def is_embodied_mismatch(title: str = "", jd: str = "") -> tuple[bool, str]:
    """Return (skip, reason). skip=True means do not ingest as an active job."""
    title = title or ""
    jd = jd or ""
    blob = f"{title}\n{jd}"
    if KEEP_CONTEXT_RE.search(blob) and not TITLE_SKIP_RE.search(title):
        # Still skip if duties independently scream embodied robot work.
        duty = _duty_blob(title, jd)
        if DUTY_SKIP_RE.search(duty) and not KEEP_CONTEXT_RE.search(duty):
            return True, "duty-embodied"
        return False, "keep-context"
    if TITLE_SKIP_RE.search(title):
        return True, "title-embodied"
    duty = _duty_blob(title, jd)
    if DUTY_SKIP_RE.search(duty):
        return True, "duty-embodied"
    return False, "ok"


def skip_embodied(title: str = "", jd: str = "") -> bool:
    skip, _ = is_embodied_mismatch(title, jd)
    return skip


def _self_check() -> None:
    cases = [
        (
            "具身智能 Agent 算法研究员/工程师",
            "主导机器人 Agentic OS 核心算法研发",
            True,
        ),
        (
            "Agentic Self-Improving 算法研究员",
            "设计机器人 Agent 架构。推动算法在机械臂、双臂或人形机器人平台上的验证与部署。熟悉 VLA、Isaac Sim。",
            True,
        ),
        (
            "物理AI Agent算法工程师",
            "面向移动机器人场景的物理 AI Agent 能力建设",
            True,
        ),
        (
            "Agent开发工程师",
            "对接 ROS/ROS2、机器人端侧 Runtime、感知系统、VLA 模型及远程接管系统",
            True,
        ),
        (
            "智能体算法工程师",
            "参与机器人智能体系统研发，构建任务规划。熟悉 ROS2 或机器人软硬件交互者优先。",
            True,
        ),
        (
            "Agent开发工程师",
            "参与 AI Agent 应用的开发和优化，包括任务规划、工具调用、记忆管理。了解 RAG 或 AI Agent。",
            False,
        ),
        (
            "Agent算法工程师（2027届校招）",
            "基于 Agentic 设计并实现高可用的 Agent 系统。说明：具身/Physical Agent 产品经理等非工程主攻，本卡不合并。",
            False,
        ),
        (
            "AI框架软件工程师",
            "对SOTA模型和框架做原理分析。理解SOTA大语言模型、多模态模型、VLA模型的架构与原理。",
            False,
        ),
        (
            "高性能计算加速软件工程师",
            "支撑大语言模型、自动驾驶、具身智能等关键场景的高效推理与训练",
            False,
        ),
        (
            "Camera Agent算法工程师",
            "负责场景分类、主体检测。加分项：接触过智能决策、视觉具身智能、Agent相关技术。",
            False,
        ),
        (
            "Agent开发工程师",
            "负责基于大语言模型的 Agent 应用设计。探索并应用最新 Agent 技术和框架，推动具身智能产品创新。",
            False,
        ),
        (
            "Agent开发工程师",
            "参与 Agent OS 核心能力的研发，包括 Agent 运行时、任务调度、工具调用、MCP/工具协议。",
            False,
        ),
    ]
    failed = 0
    for title, jd, expect in cases:
        got, reason = is_embodied_mismatch(title, jd)
        if got != expect:
            failed += 1
            print("FAIL", title[:24], "got", got, reason, "expect", expect)
        else:
            print("OK", title[:24], reason)
    if failed:
        raise SystemExit(f"self-check failed: {failed}")
    print("self-check passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Embodied-intelligence ingest gate")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--title", default="")
    parser.add_argument("--jd", default="")
    args = parser.parse_args()
    if args.self_check:
        _self_check()
        return
    skip, reason = is_embodied_mismatch(args.title, args.jd)
    print(reason, "skip" if skip else "keep")
    raise SystemExit(1 if skip else 0)


if __name__ == "__main__":
    main()
