import { useEffect, useState } from "react";
import { DateTimeField } from "./DateTimeField";
import {
  TIME_KINDS,
  defaultTimeKind,
  formatStageWhen,
  resolveTimeKind,
  stageTimeFieldLabel,
} from "../lib/stageTime";
import type { ProcessStage, TimeKind } from "../types";

const STAGE_TYPES = ["投递", "测评", "笔试", "面试", "Offer", "其他"];

function newStage(index: number): ProcessStage {
  return {
    id: `s${Date.now()}-${index}`,
    label: `环节${index + 1}`,
    type: "面试",
    field: null,
    when: null,
    time_kind: defaultTimeKind("面试"),
  };
}

export function ProcessEditor({
  open,
  companyLabel,
  initial,
  onClose,
  onSave,
}: {
  open: boolean;
  companyLabel: string;
  initial: ProcessStage[];
  onClose: () => void;
  onSave: (stages: ProcessStage[]) => Promise<void>;
}) {
  const [stages, setStages] = useState<ProcessStage[]>([]);
  const [selected, setSelected] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setStages(
        initial.length
          ? initial.map((s) => ({ ...s, time_kind: resolveTimeKind(s) }))
          : [newStage(0)]
      );
      setSelected(0);
      setError("");
    }
  }, [open, initial]);

  if (!open) return null;

  const cur = stages[selected];

  const move = (from: number, to: number) => {
    if (to < 0 || to >= stages.length) return;
    const next = [...stages];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    setStages(next);
    setSelected(to);
  };

  const updateCur = (patch: Partial<ProcessStage>) => {
    setStages((prev) =>
      prev.map((s, i) => {
        if (i !== selected) return s;
        const next = { ...s, ...patch };
        // Changing type resets default time_kind unless user explicitly set time_kind in patch
        if (patch.type != null && patch.time_kind == null) {
          next.time_kind = defaultTimeKind(patch.type);
        }
        return next;
      })
    );
  };

  const addStage = () => {
    const s = newStage(stages.length);
    setStages((prev) => [...prev, s]);
    setSelected(stages.length);
  };

  const removeCur = () => {
    if (stages.length <= 1) {
      setError("至少保留一个环节");
      return;
    }
    const next = stages.filter((_, i) => i !== selected);
    setStages(next);
    setSelected(Math.max(0, selected - 1));
  };

  const duplicateCur = () => {
    if (!cur) return;
    const copy: ProcessStage = {
      ...cur,
      id: `s${Date.now()}`,
      label: `${cur.label}（副本）`,
    };
    const next = [...stages];
    next.splice(selected + 1, 0, copy);
    setStages(next);
    setSelected(selected + 1);
  };

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      await onSave(
        stages.map((s) => ({
          ...s,
          time_kind: resolveTimeKind(s),
        }))
      );
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal process-editor" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>编辑招聘流程</h2>
            <div className="sub">{companyLabel}</div>
          </div>
          <div className="toolbar" style={{ marginBottom: 0 }}>
            <button type="button" className="btn secondary" onClick={onClose}>
              取消
            </button>
            <button type="button" className="btn" disabled={saving} onClick={save}>
              {saving ? "保存中…" : "保存流程"}
            </button>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}

        <div className="process-editor-grid">
          <div className="process-list">
            <div className="process-list-head">
              <strong>当前流程</strong>
              <span className="sub">{stages.length} 个环节</span>
              <button type="button" className="btn sm secondary" onClick={addStage}>
                + 新增环节
              </button>
            </div>
            {stages.map((s, i) => (
              <div
                key={s.id}
                className={`process-row ${i === selected ? "active" : ""}`}
                onClick={() => setSelected(i)}
              >
                <span className={`process-idx ${s.when ? "done" : ""}`}>
                  {s.when ? "✓" : i + 1}
                </span>
                <div className="process-row-main">
                  <div className="title">{s.label}</div>
                  <div className="meta">
                    {s.type}
                    {` · ${formatStageWhen(s)}`}
                  </div>
                </div>
                <div className="process-row-actions">
                  <button
                    type="button"
                    className="btn sm secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      move(i, i - 1);
                    }}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="btn sm secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      move(i, i + 1);
                    }}
                  >
                    ↓
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="process-side">
            <h3>环节设置</h3>
            {cur ? (
              <>
                <div className="field">
                  <label>环节名称</label>
                  <input
                    value={cur.label}
                    onChange={(e) => updateCur({ label: e.target.value })}
                  />
                </div>
                <div className="field">
                  <label>环节类型</label>
                  <select
                    value={cur.type}
                    onChange={(e) => updateCur({ type: e.target.value })}
                  >
                    {STAGE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>时间类型</label>
                  <select
                    value={resolveTimeKind(cur)}
                    onChange={(e) =>
                      updateCur({ time_kind: e.target.value as TimeKind })
                    }
                  >
                    {TIME_KINDS.map((k) => (
                      <option key={k} value={k}>
                        {k}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>{stageTimeFieldLabel(cur)}</label>
                  <DateTimeField
                    value={cur.when}
                    onChange={(next) => updateCur({ when: next })}
                  />
                </div>
                <div className="field">
                  <label>同步字段（可选，兼容日历）</label>
                  <input
                    value={cur.field || ""}
                    placeholder="如 一面 / 测评时间"
                    onChange={(e) =>
                      updateCur({ field: e.target.value.trim() || null })
                    }
                  />
                </div>
                <div className="toolbar">
                  <button type="button" className="btn secondary" onClick={duplicateCur}>
                    复制此环节
                  </button>
                  <button type="button" className="btn danger" onClick={removeCur}>
                    删除此环节
                  </button>
                </div>
              </>
            ) : (
              <div className="empty">选择左侧环节</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
