import type { ProcessStage, Stage, TimeKind } from "../types";

export const TIME_KINDS: TimeKind[] = ["开始", "截止", "安排"];

export function defaultTimeKind(type: string | null | undefined): TimeKind {
  const t = String(type || "").trim();
  if (t === "笔试" || t === "测评") return "截止";
  if (t === "面试") return "开始";
  return "安排";
}

export function resolveTimeKind(
  stage: Pick<ProcessStage | Stage, "time_kind" | "type">
): TimeKind {
  const raw = String(stage.time_kind || "").trim();
  if (raw === "开始" || raw === "截止" || raw === "安排") return raw;
  return defaultTimeKind(stage.type);
}

/** Field label for the datetime control, e.g. 笔试截止时间 / 面试开始时间 */
export function stageTimeFieldLabel(
  stage: Pick<ProcessStage | Stage, "label" | "type" | "time_kind">
): string {
  const kind = resolveTimeKind(stage);
  const base = String(stage.label || stage.type || "环节").trim() || "环节";
  if (kind === "截止") return `${base}截止时间`;
  if (kind === "开始") return `${base}开始时间`;
  return `${base}时间`;
}

/** Compact display: 截止 2026-09-15 18:00 */
export function formatStageWhen(
  stage: Pick<ProcessStage | Stage, "when" | "type" | "time_kind">
): string {
  const when = stage.when ? String(stage.when) : "";
  if (!when) return "待安排";
  const kind = resolveTimeKind(stage);
  return `${kind} ${when}`;
}
