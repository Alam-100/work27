#!/usr/bin/env python3
"""Harvest Huawei campus JD via official position-intention API.

华为校招详情页点击后新开 `job-details?advertisementId=…`。列表页 JD 仅为
「详见岗位意向」；实质职责/要求由 `getPositionIntentionList(jobId)` 按意向返回。

入库口径（大厂严筛，默认）：只收意向名属于 Agent / 智能体 / 大模型应用 / AI应用安全
的意向。算子、训推、数据系统、空间智能、后训练、评测等跳过。同名岗保留
advertisementId 较大的一条（去重旧广告）。

用户点名昇腾/AI Infra 时加 `--include-infra`（见 INFRA_INTENT_NAMES）。
博士硬门槛（硕士不可投）走 `jd_edu_gate.is_phd_only`，不入库。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import requests

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from jd_edu_gate import is_phd_only  # noqa: E402

API = "https://apigw-dgg-b0.huawei.com/api/apig/channelhw/recruitmentPosition/pub"
CAMPUS_LIST = (
    "https://career.huawei.com/cn/campus-recruitment-job-list"
    "?recruitmentType=FRESH_GRADUATE"
)
HEADERS = {
    "X-HW-ID": "app_000000035886",
    "Content-Type": "application/json",
    "x-jalor-tenantalias": "hcm",
    "x-language": "zh_CN",
    "x-referer": "https://career.huawei.com/cn",
    "Referer": "https://career.huawei.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Broad mention flag (logging only).
MENTION_RE = re.compile(
    r"Agent|智能体|大模型|RAG|微调|向量|LLM|推理引擎|模型服务|对话系统|MindSpore|pytorch",
    re.I,
)

# Intent names that pass 互联网大厂 Agent/智能体/大模型应用 口径.
INGEST_INTENT_NAMES = {
    "Agent技术",
    "AI技术应用",
    "AI应用安全",
}

# Infra / 训练主责 / 具身 / 评测：即使正文出现 Agent 也不入库.
# 昇腾/AI Infra 本轮可由 --include-infra 打开（见 INFRA_INTENT_NAMES）。
SKIP_INTENT_NAMES = {
    "建模仿真",
    "AI系统软件",
    "AI模型与Infra安全",
    "端侧大模型",
    "搜索推荐",
    "多模态大模型",
    "大模型数据技术",
    "空间智能",
    "AI算法",
    "AI算子技术",
    "AI训推系统",
    "AI数据系统",
    "后训练与强化学习",
    "AI模型评测",
}

# 华为昇腾/计算产品线常见 AI Infra 意向；默认仍跳过，--include-infra 才收。
INFRA_INTENT_NAMES = {
    "AI训推系统",
    "AI算子技术",
    "AI系统软件",
    "AI数据系统",
    "端侧大模型",
}

NEW_INTENT_RE = re.compile(
    r"Agent|智能体|Agentic|多智能体|大模型应用",
    re.I,
)


def post(endpoint: str, payload: dict) -> dict:
    r = requests.post(
        f"{API}/{endpoint}?X-HW-ID=app_000000035886",
        json=payload,
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("status") != "SUCCESS":
        raise RuntimeError(body)
    return body


def html_to_text(s: str) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def ingest_intent(name: str, *, include_infra: bool = False) -> tuple[bool, str]:
    """Return (keep, reason)."""
    if include_infra and name in INFRA_INTENT_NAMES:
        return True, "infra-intent"
    if name in SKIP_INTENT_NAMES:
        return False, "skip-taxonomy"
    if name in INGEST_INTENT_NAMES:
        return True, "named-intent"
    if NEW_INTENT_RE.search(name or ""):
        return True, "new-intent-name"
    return False, "not-agent-app"


def list_campus_jobs() -> list[dict]:
    jobs: list[dict] = []
    page = 1
    while True:
        body = post(
            "getJobPage",
            {
                "curPage": page,
                "pageSize": 50,
                "channelType": "2",
                "jobType": "0",
                "recruitScenarioId": "06",
                "recruitSubScenarioId": "001",
            },
        )
        jobs.extend(body["data"]["result"])
        pv = body["data"]["pageVO"]
        if page >= pv["totalPages"]:
            break
        page += 1
    return [j for j in jobs if str(j.get("jobType")) == "0" and j.get("jobName")]


def dedup_latest(rows: list[dict]) -> list[dict]:
    """Keep the highest advertisementId per jobName."""
    best: dict[str, dict] = {}
    for row in rows:
        name = row.get("jobName") or ""
        aid = int(row.get("advertisementId") or 0)
        prev = best.get(name)
        if prev is None or aid > int(prev.get("advertisementId") or 0):
            best[name] = row
    return list(best.values())


def harvest_job(row: dict, *, include_infra: bool = False) -> dict:
    job_id = row["jobId"]
    advertisement_id = row["advertisementId"]
    detail = post("getRecruitmentPositionDetail", {"advertisementId": str(advertisement_id)})
    intents_raw = post("getPositionIntentionList", {"jobId": job_id})

    intents: dict[str, dict] = {}
    for item in intents_raw.get("data") or []:
        name = item.get("positionIntention") or "?"
        blob = (item.get("jobResponsibilities") or "") + (item.get("jobDemand") or "")
        keep, reason = ingest_intent(name, include_infra=include_infra)
        resp_txt = html_to_text(item.get("jobResponsibilities", ""))
        demand_txt = html_to_text(item.get("jobDemand", ""))
        if keep:
            phd, phd_reason = is_phd_only(name, f"{resp_txt}\n{demand_txt}")
            if phd:
                keep, reason = False, f"phd-only:{phd_reason}"
        intents[name] = {
            "positionIntentionId": item.get("positionIntentionId"),
            "jobResponsibilities": resp_txt,
            "jobDemand": demand_txt,
            "jobPlaceName": item.get("jobPlaceName", ""),
            "mention": bool(MENTION_RE.search(blob) or MENTION_RE.search(name)),
            "ingest": keep,
            "ingest_reason": reason,
        }

    d = detail["data"]
    cities_raw = d.get("jobCity") or row.get("workPlace") or ""
    return {
        "advertisementId": advertisement_id,
        "jobName": row.get("jobName") or d.get("jobname") or d.get("jobName"),
        "jobId": job_id,
        "url": f"https://career.huawei.com/cn/job-details?advertisementId={advertisement_id}",
        "cities": [c.strip() for c in cities_raw.split("/") if c.strip()],
        "intents": intents,
    }


def flatten_ingest(job: dict) -> list[dict]:
    rows: list[dict] = []
    for name, it in (job.get("intents") or {}).items():
        if not it.get("ingest"):
            continue
        place = it.get("jobPlaceName") or ""
        cities = [c.strip() for c in place.split("/") if c.strip()] or job.get("cities") or []
        rows.append(
            {
                "advertisementId": job["advertisementId"],
                "jobId": job["jobId"],
                "jobName": job["jobName"],
                "intent": name,
                "positionIntentionId": it.get("positionIntentionId"),
                "url": job["url"],
                "cities": cities,
                "jobResponsibilities": it.get("jobResponsibilities") or "",
                "jobDemand": it.get("jobDemand") or "",
                "campus_list": CAMPUS_LIST,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Harvest Huawei campus AI job JDs")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tmp/harvest_huawei_api.json",
    )
    parser.add_argument("--job-name-prefix", default="AI", help="Filter job names, default AI")
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Do not drop older advertisementId of the same jobName",
    )
    parser.add_argument(
        "--include-infra",
        action="store_true",
        help="Also ingest 昇腾/AI Infra intents (训推/算子/系统软件/数据系统/端侧大模型)",
    )
    args = parser.parse_args()

    prefix = args.job_name_prefix
    jobs = [j for j in list_campus_jobs() if (j.get("jobName") or "").startswith(prefix)]
    if not args.keep_duplicates:
        jobs = dedup_latest(jobs)

    out: dict = {
        "campus_list": CAMPUS_LIST,
        "include_infra": args.include_infra,
        "harvested": [],
        "ingest": [],
        "skipped": [],
        "skipped_intents": [],
    }

    for row in jobs:
        name = row.get("jobName") or "?"
        try:
            data = harvest_job(row, include_infra=args.include_infra)
            ingest_names = [k for k, v in data["intents"].items() if v.get("ingest")]
            skip_names = [k for k, v in data["intents"].items() if not v.get("ingest")]
            data["ingest_intents"] = ingest_names
            out["harvested"].append(data)
            out["ingest"].extend(flatten_ingest(data))
            for k in skip_names:
                out["skipped_intents"].append(
                    {
                        "job": name,
                        "intent": k,
                        "reason": data["intents"][k].get("ingest_reason"),
                    }
                )
            print("OK", name, "aid=", data["advertisementId"], "ingest=", ingest_names)
        except Exception as e:
            out["skipped"].append({"job": name, "error": str(e)})
            print("ERR", name, e)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", args.out, "jobs=", len(out["harvested"]), "ingest=", len(out["ingest"]))


if __name__ == "__main__":
    main()
