/** Build 投递状态 options from the card's process stages (not a fixed global enum). */

import type { ProcessStage, Stage } from "../types";

/** Terminal / coarse statuses always available regardless of process. */
export const TERMINAL_STATUSES = ["等结果", "Offer", "已拒", "弃投"] as const;

const KNOWN_STAGE_STATUS: Record<string, string> = {
  测评: "待测评",
  笔试: "待笔试",
  一面: "待面试-一面",
  二面: "待面试-二面",
  三面: "待面试-三面",
  HR面: "待面试-HR面",
};

type StageLike = Pick<ProcessStage, "label" | "type"> | Pick<Stage, "label" | "type">;

/** Map one process stage → a selectable 投递状态 value; skip apply/Offer anchors. */
export function statusForStage(stage: StageLike): string | null {
  const label = String(stage.label || "").trim();
  const type = String(stage.type || "").trim();
  if (!label) return null;
  if (label === "投递" || type === "投递") return null;
  if (label === "Offer" || type === "Offer") return null;
  if (KNOWN_STAGE_STATUS[label]) return KNOWN_STAGE_STATUS[label];
  if (type === "测评") return `待${label}`;
  if (type === "笔试") return `待${label}`;
  if (type === "面试" || /面|面试|AI|ai/.test(label)) return `待面试-${label}`;
  return `待${label}`;
}

/**
 * Dynamic status list for the detail dropdown:
 * 待投 → statuses for each process stage → 等结果/Offer/已拒/弃投.
 * Always keeps the current saved value if it is not derived from stages.
 */
export function statusOptionsFromStages(
  stages: StageLike[],
  current?: string | null,
  fallbackEnums: string[] = [],
): string[] {
  const seen = new Set<string>();
  const out: string[] = [];

  const push = (s: string) => {
    const v = s.trim();
    if (!v || seen.has(v)) return;
    seen.add(v);
    out.push(v);
  };

  push("待投");
  for (const stage of stages) {
    const s = statusForStage(stage);
    if (s) push(s);
  }
  for (const t of TERMINAL_STATUSES) push(t);

  // Prefer stage-derived list; only use global enums to preserve unknown legacy values.
  const cur = String(current || "").trim();
  if (cur) push(cur);
  for (const s of fallbackEnums) {
    if (s === cur) push(s);
  }

  return out;
}
