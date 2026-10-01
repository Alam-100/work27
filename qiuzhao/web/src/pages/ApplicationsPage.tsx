import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { DateTimeField } from "../components/DateTimeField";
import { MailboxBar } from "../components/MailboxBar";
import { ProcessEditor } from "../components/ProcessEditor";
import { ProcessStepper } from "../components/ProcessStepper";
import { tierPillClass } from "../lib/labels";
import {
  TIME_KINDS,
  defaultTimeKind,
  formatStageWhen,
  resolveTimeKind,
  stageTimeFieldLabel,
} from "../lib/stageTime";
import { statusOptionsFromStages } from "../lib/statusOptions";
import type {
  HealthInfo,
  ProcessStage,
  ProgressItem,
  ProgressStats,
  Stage,
  TimeKind,
} from "../types";

const WORK_TABS = [
  { id: "active", label: "流程中" },
  { id: "apply", label: "待投" },
  { id: "assessment", label: "测评" },
  { id: "written", label: "笔试" },
  { id: "interview", label: "面试" },
  { id: "waiting", label: "等结果" },
] as const;

const HISTORY_TABS = [
  { id: "offer", label: "已 Offer" },
  { id: "rejected", label: "未通过" },
  { id: "stopped", label: "不再跟进" },
  { id: "all", label: "全部" },
] as const;

type TabId =
  | (typeof WORK_TABS)[number]["id"]
  | (typeof HISTORY_TABS)[number]["id"];

function tabCount(tabId: TabId, stats: ProgressStats | null): number | null {
  if (!stats) return null;
  const map: Record<TabId, number> = {
    active: stats.active ?? stats.applying + stats.interviewing,
    apply: stats.apply ?? stats.applying,
    assessment: stats.assessment ?? 0,
    written: stats.written ?? 0,
    interview: stats.interview ?? 0,
    waiting: stats.waiting ?? 0,
    offer: stats.offer,
    rejected: stats.rejected ?? 0,
    stopped: stats.stopped,
    all: stats.total,
  };
  return map[tabId] ?? null;
}

function coarseStatus(item: ProgressItem): "active" | "pass" | "fail" {
  const result = String(item.meta["结果"] || "");
  const status = String(item.meta["投递状态"] || "");
  if (result === "Offer" || status === "Offer") return "pass";
  if (result === "已拒" || status === "已拒" || status === "弃投") return "fail";
  return "active";
}

function toProcessStages(item: ProgressItem): ProcessStage[] {
  if (item.process?.length) {
    return item.process.map((s) => ({
      ...s,
      time_kind: resolveTimeKind(s),
    }));
  }
  return item.stages.map((s) => ({
    id: s.id || s.key,
    label: s.label,
    type: s.type || "面试",
    field: s.field,
    when: s.when,
    time_kind: resolveTimeKind(s),
  }));
}

export function ApplicationsPage() {
  const { stem: routeStem } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState<TabId>("active");
  const [items, setItems] = useState<ProgressItem[]>([]);
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [selected, setSelected] = useState<ProgressItem | null>(null);
  const [enums, setEnums] = useState<HealthInfo["enums"] | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [activeStage, setActiveStage] = useState<Stage | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [q, setQ] = useState("");
  const [createForm, setCreateForm] = useState({
    company: "",
    position: "",
    base: "",
    link: "",
    plan: "校招正式批",
    priority: "⚪ 观察池",
  });

  const isDetail = Boolean(routeStem);

  useEffect(() => {
    api.enums().then((r) => setEnums(r.enums)).catch(() => undefined);
  }, []);

  const loadList = async () => {
    const [data, st] = await Promise.all([
      api.listProgress(tab),
      api.progressStats(),
    ]);
    setItems(data.items);
    setStats(st);
  };

  const loadDetail = async (stem: string) => {
    const detail = await api.getProgress(stem);
    setSelected(detail);
    const cur =
      detail.stages.find((s) => s.state === "active") ||
      detail.stages.find((s) => s.when) ||
      detail.stages[0] ||
      null;
    setActiveStage(cur);
    return detail;
  };

  const load = async () => {
    setError("");
    try {
      await loadList();
      if (routeStem) {
        await loadDetail(routeStem);
      } else {
        setSelected(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, routeStem]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((c) => {
      const blob = `${c.meta["公司"]} ${c.meta["岗位"]} ${c.meta["优先级"]} ${c.stem}`.toLowerCase();
      return blob.includes(needle);
    });
  }, [items, q]);

  const saveField = async (updates: Record<string, unknown>) => {
    if (!selected && !routeStem) return;
    const stem = selected?.stem || routeStem!;
    setSaving(true);
    setError("");
    try {
      const detail = await api.patchProgress(stem, updates);
      setSelected(detail);
      setMsg("已保存到 Obsidian");
      await loadList();
      const cur =
        detail.stages.find((s) => (s.id || s.key) === (activeStage?.id || activeStage?.key)) ||
        detail.stages.find((s) => s.state === "active") ||
        detail.stages[0] ||
        null;
      setActiveStage(cur);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const setCoarse = async (kind: "active" | "pass" | "fail") => {
    if (kind === "active") {
      const status = String(selected?.meta["投递状态"] || "");
      const updates: Record<string, unknown> = { 结果: "进行中" };
      if (["Offer", "已拒", "弃投"].includes(status)) {
        updates["投递状态"] = "待投";
      }
      await saveField(updates);
    } else if (kind === "pass") {
      await saveField({ 结果: "Offer", 投递状态: "Offer" });
    } else {
      await saveField({ 结果: "已拒", 投递状态: "已拒" });
    }
  };

  const softArchive = async (
    stem: string,
    mode: "rejected" | "stopped" = "rejected",
  ) => {
    setSaving(true);
    setError("");
    try {
      if (mode === "stopped") {
        await api.patchProgress(stem, { 投递状态: "弃投", 结果: "进行中" });
        setMsg("已移入「不再跟进」");
      } else {
        await api.patchProgress(stem, { 结果: "已拒", 投递状态: "已拒" });
        setMsg("已归档到「未通过」");
      }
      if (selected?.stem === stem) {
        await loadDetail(stem);
      }
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const restoreFollow = async (stem: string) => {
    setSaving(true);
    setError("");
    try {
      await api.patchProgress(stem, { 结果: "进行中", 投递状态: "待投" });
      setMsg("已恢复跟进，回到流程中");
      if (selected?.stem === stem) {
        await loadDetail(stem);
      }
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const physicalArchive = async () => {
    if (!selected) return;
    if (
      !confirm(
        `确认物理归档「${selected.meta["公司"]} · ${selected.meta["岗位"]}」？\n文件会移到 05_投递进度/_归档，列表中不再出现。`,
      )
    ) {
      return;
    }
    setSaving(true);
    try {
      await api.deleteProgress(selected.stem);
      setMsg("已物理归档到 05_投递进度/_归档");
      navigate("/applications");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const saveStageWhen = async (when: string) => {
    if (!selected || !activeStage) return;
    const process = toProcessStages(selected);
    const key = activeStage.id || activeStage.key;
    const next = process.map((s) =>
      s.id === key
        ? {
            ...s,
            when: when.trim() || null,
            time_kind: resolveTimeKind(activeStage),
          }
        : s
    );
    setSaving(true);
    setError("");
    try {
      const detail = await api.putProcess(selected.stem, next);
      setSelected(detail);
      setMsg("环节时间已保存");
      await loadList();
      setActiveStage(
        detail.stages.find((s) => (s.id || s.key) === key) || detail.stages[0] || null
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const saveStageTimeKind = async (kind: TimeKind) => {
    if (!selected || !activeStage) return;
    const process = toProcessStages(selected);
    const key = activeStage.id || activeStage.key;
    const next = process.map((s) =>
      s.id === key ? { ...s, time_kind: kind } : s
    );
    setSaving(true);
    setError("");
    try {
      const detail = await api.putProcess(selected.stem, next);
      setSelected(detail);
      setMsg("时间类型已保存");
      await loadList();
      setActiveStage(
        detail.stages.find((s) => (s.id || s.key) === key) || detail.stages[0] || null
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const saveProcess = async (stages: ProcessStage[]) => {
    if (!selected) return;
    const detail = await api.putProcess(selected.stem, stages);
    setSelected(detail);
    setMsg("流程已保存到 Obsidian");
    await loadList();
    setActiveStage(detail.stages[0] || null);
  };

  const addStageQuick = async () => {
    if (!selected) return;
    const process = toProcessStages(selected);
    process.push({
      id: `s${Date.now()}`,
      label: `环节${process.length + 1}`,
      type: "面试",
      field: null,
      when: null,
      time_kind: defaultTimeKind("面试"),
    });
    await saveProcess(process);
    setEditorOpen(true);
  };

  const createRecord = async () => {
    setSaving(true);
    setError("");
    try {
      const detail = await api.createProgress(createForm);
      setCreateOpen(false);
      setMsg("已新建投递记录");
      navigate(`/applications/${encodeURIComponent(detail.stem)}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const formMeta = selected?.meta || {};
  const statusKind = selected ? coarseStatus(selected) : "active";
  const statusOptions = useMemo(() => {
    if (!selected) return enums?.statuses || [];
    return statusOptionsFromStages(
      selected.stages,
      String(selected.meta["投递状态"] || ""),
      enums?.statuses || [],
    );
  }, [selected, enums?.statuses]);

  // ---------- Detail view ----------
  if (isDetail && selected) {
    const jdText = selected.intel
      ? String(selected.intel.meta?.["岗位简介"] || selected.intel.body || "—")
      : "暂无关联情报 JD（可在职位信息页跟进生成，或手动填备注）";

    return (
      <div className="apps-page apps-detail-page">
        <div className="page-header">
          <div>
            <Link className="sub" to="/applications">
              ← 返回投递目录
            </Link>
            <h1 style={{ marginTop: 4 }}>
              {String(formMeta["公司"])} · {String(formMeta["岗位"])}
            </h1>
            <div className="sub" style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <span className={tierPillClass(selected.company_tier || "")}>
                {selected.company_tier || "未分档"}
              </span>
              {selected.role_family ? <span className="pill">{selected.role_family}</span> : null}
              {selected.apply_priority ? (
                <span className="pill gray">{selected.apply_priority}</span>
              ) : null}
              <span>
                投递日期 {String(formMeta["投递时间"] || "—")} · 写入 Obsidian
              </span>
              {selected.company_overview ? (
                <span>
                  · 限投{" "}
                  {selected.company_overview.apply_limit != null
                    ? selected.company_overview.apply_limit
                    : "未知"}
                </span>
              ) : null}
              {formMeta["投递记录查询"] ? (
                <a
                  className="btn sm"
                  href={String(formMeta["投递记录查询"])}
                  target="_blank"
                  rel="noreferrer"
                >
                  查官网进度
                </a>
              ) : selected.company_overview?.delivery_record_url ? (
                <a
                  className="btn sm secondary"
                  href={selected.company_overview.delivery_record_url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() =>
                    saveField({
                      投递记录查询: selected.company_overview!.delivery_record_url,
                    })
                  }
                >
                  用公司查询链
                </a>
              ) : null}
            </div>
          </div>
          <div className="field" style={{ minWidth: 140 }}>
            <label>Base 地</label>
            <input
              key={`base-${selected.stem}`}
              defaultValue={String(formMeta["Base地"] || "")}
              onBlur={(e) => {
                if (e.target.value !== String(formMeta["Base地"] || "")) {
                  saveField({ Base地: e.target.value });
                }
              }}
            />
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
        {msg ? <div className="flash">{msg}</div> : null}

        <MailboxBar company={String(formMeta["公司"] || "")} compact />

        <div className="detail-layout">
          <div className="detail-main">
            <div className="panel detail-card">
              <div className="detail-actions">
                <div className="status-pills">
                  <button
                    type="button"
                    className={statusKind === "active" ? "pill-btn active" : "pill-btn"}
                    onClick={() => setCoarse("active")}
                  >
                    流程中
                  </button>
                  <button
                    type="button"
                    className={statusKind === "pass" ? "pill-btn active good" : "pill-btn"}
                    onClick={() => setCoarse("pass")}
                  >
                    通过
                  </button>
                  <button
                    type="button"
                    className={statusKind === "fail" ? "pill-btn active danger" : "pill-btn"}
                    onClick={() => setCoarse("fail")}
                  >
                    未通过
                  </button>
                </div>
                <div className="detail-actions-right">
                  {selected.mianshi_stem ? (
                    <Link
                      className="btn sm secondary"
                      to={`/review/${encodeURIComponent(selected.mianshi_stem)}`}
                    >
                      面试复盘
                    </Link>
                  ) : null}
                  <button
                    type="button"
                    className="btn sm secondary"
                    onClick={() => setEditorOpen(true)}
                  >
                    编辑流程
                  </button>
                  <button type="button" className="btn sm secondary" onClick={addStageQuick}>
                    + 新增环节
                  </button>
                  {statusKind === "fail" ? (
                    <button
                      type="button"
                      className="btn sm"
                      onClick={() => restoreFollow(selected.stem)}
                      disabled={saving}
                    >
                      恢复跟进
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="btn sm secondary"
                      onClick={() => softArchive(selected.stem, "rejected")}
                      disabled={saving}
                    >
                      归档未通过
                    </button>
                  )}
                  <button type="button" className="btn sm danger" onClick={physicalArchive}>
                    物理删除
                  </button>
                </div>
              </div>

              <ProcessStepper
                stages={selected.stages}
                selectedKey={activeStage?.id || activeStage?.key}
                onSelect={setActiveStage}
              />

              <div className="toolbar">
                <div className="field">
                  <label>投递状态</label>
                  <select
                    value={String(formMeta["投递状态"] || "")}
                    onChange={(e) => saveField({ 投递状态: e.target.value })}
                    title="随本流程环节动态生成；新增环节后会出现「待面试-xxx」等选项"
                  >
                    {statusOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>优先级（分组）</label>
                  <select
                    value={String(formMeta["优先级"] || "")}
                    onChange={(e) => saveField({ 优先级: e.target.value })}
                  >
                    {(enums?.priorities || []).map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>结果</label>
                  <select
                    value={String(formMeta["结果"] || "")}
                    onChange={(e) => saveField({ 结果: e.target.value })}
                  >
                    {(enums?.results || []).map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field grow">
                  <label>投递链接</label>
                  <div className="link-field">
                    <input
                      key={`link-${selected.stem}`}
                      defaultValue={String(formMeta["投递链接"] || "")}
                      onBlur={(e) => {
                        if (e.target.value !== String(formMeta["投递链接"] || "")) {
                          saveField({ 投递链接: e.target.value });
                        }
                      }}
                    />
                    {formMeta["投递链接"] ? (
                      <a
                        className="btn sm secondary"
                        href={String(formMeta["投递链接"])}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        打开
                      </a>
                    ) : null}
                  </div>
                </div>
                <div className="field grow">
                  <label>投递记录查询</label>
                  <div className="link-field">
                    <input
                      key={`record-${selected.stem}`}
                      placeholder="官网个人中心·投递/申请进度"
                      defaultValue={String(formMeta["投递记录查询"] || "")}
                      onBlur={(e) => {
                        if (e.target.value !== String(formMeta["投递记录查询"] || "")) {
                          saveField({ 投递记录查询: e.target.value });
                        }
                      }}
                    />
                    {formMeta["投递记录查询"] ? (
                      <a
                        className="btn sm"
                        href={String(formMeta["投递记录查询"])}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        查进度
                      </a>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="jd-block">
                <h3>岗位 JD</h3>
                <div className="jd">{jdText}</div>
              </div>
            </div>
          </div>

          <aside className="detail-side panel">
            <h2>当前环节 · {activeStage?.label || "—"}</h2>
            {activeStage ? (
              <>
                <div className="field">
                  <label>时间类型</label>
                  <select
                    value={resolveTimeKind(activeStage)}
                    onChange={(e) => saveStageTimeKind(e.target.value as TimeKind)}
                  >
                    {TIME_KINDS.map((k) => (
                      <option key={k} value={k}>
                        {k}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>{stageTimeFieldLabel(activeStage)}</label>
                  <DateTimeField
                    key={`${selected.stem}-${activeStage.id || activeStage.key}-when`}
                    value={activeStage.when}
                    onCommit={(next) => {
                      const prev = activeStage.when || null;
                      if (next !== prev) {
                        saveStageWhen(next || "");
                      }
                    }}
                  />
                </div>
                <div className="field">
                  <label>状态提示</label>
                  <div className="pill">
                    {activeStage.state === "done"
                      ? "已完成"
                      : activeStage.state === "active"
                        ? "进行中"
                        : "待安排"}
                  </div>
                </div>
              </>
            ) : (
              <div className="empty">点击上方流程节点选择环节</div>
            )}

            <div className="field">
              <label>备注</label>
              <textarea
                key={`note-${selected.stem}`}
                defaultValue={String(formMeta["备注"] || "")}
                onBlur={(e) => {
                  if (e.target.value !== String(formMeta["备注"] || "")) {
                    saveField({ 备注: e.target.value });
                  }
                }}
              />
            </div>
            <div className="field">
              <label>内推人</label>
              <input
                key={`ref-${selected.stem}`}
                defaultValue={String(formMeta["内推人"] || "")}
                onBlur={(e) => {
                  if (e.target.value !== String(formMeta["内推人"] || "")) {
                    saveField({ 内推人: e.target.value });
                  }
                }}
              />
            </div>
            <div className="field">
              <label>内推码</label>
              <input
                key={`code-${selected.stem}`}
                defaultValue={String(formMeta["内推码"] || "")}
                onBlur={(e) => {
                  if (e.target.value !== String(formMeta["内推码"] || "")) {
                    saveField({ 内推码: e.target.value });
                  }
                }}
              />
            </div>

            <div className="stage-history">
              <h3>流程摘要</h3>
              <ul>
                {selected.stages.map((s) => (
                  <li key={s.id || s.key}>
                    <button
                      type="button"
                      className="linkish"
                      onClick={() => setActiveStage(s)}
                    >
                      {s.label}
                    </button>
                    <span className="sub">{formatStageWhen(s)}</span>
                  </li>
                ))}
              </ul>
            </div>
            {saving ? <div className="sub">保存中…</div> : null}
          </aside>
        </div>

        <ProcessEditor
          open={editorOpen}
          companyLabel={`${formMeta["公司"]} · ${formMeta["岗位"]}`}
          initial={toProcessStages(selected)}
          onClose={() => setEditorOpen(false)}
          onSave={saveProcess}
        />
      </div>
    );
  }

  if (isDetail && !selected && !error) {
    return <div className="empty">加载中…</div>;
  }

  // ---------- Directory / overview ----------
  return (
    <div className="apps-page">
      <div className="page-header">
        <div>
          <h1>我的秋招</h1>
          <div className="sub">一眼看到每条投递走到哪了 · 写入 Obsidian</div>
        </div>
        <button type="button" className="btn" onClick={() => setCreateOpen(true)}>
          + 手动新增记录
        </button>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="flash">{msg}</div> : null}

      <MailboxBar />

      <div className="stats">
        <div className="stat-card">
          <div className="label">流程中</div>
          <div className="value">{stats?.active ?? stats?.applying ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="label">测评 / 笔试 / 面试</div>
          <div className="value">
            {stats
              ? `${stats.assessment ?? 0}/${stats.written ?? 0}/${stats.interview ?? 0}`
              : "—"}
          </div>
        </div>
        <div className="stat-card">
          <div className="label">Offer</div>
          <div className="value">{stats?.offer ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="label">未通过 / 弃投</div>
          <div className="value">
            {stats ? `${stats.rejected ?? 0}/${stats.stopped}` : "—"}
          </div>
        </div>
      </div>

      <div className="panel apps-directory">
        <div className="toolbar">
          <div className="field grow">
            <label>搜索</label>
            <input
              value={q}
              placeholder="搜索公司、岗位或分组"
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
        </div>

        <div className="apps-tab-groups">
          <div className="apps-tab-group">
            <div className="apps-tab-group-label">推进中</div>
            <div className="tabs">
              {WORK_TABS.map((t) => {
                const count = tabCount(t.id, stats);
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={tab === t.id ? "active" : ""}
                    onClick={() => setTab(t.id)}
                  >
                    {t.label}
                    {count != null ? ` ${count}` : ""}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="apps-tab-group history">
            <div className="apps-tab-group-label">结果 / 归档</div>
            <div className="tabs">
              {HISTORY_TABS.map((t) => {
                const count = tabCount(t.id, stats);
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={tab === t.id ? "active" : ""}
                    onClick={() => setTab(t.id)}
                  >
                    {t.label}
                    {count != null ? ` ${count}` : ""}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="table-wrap">
          <table className="apps-table">
            <thead>
              <tr>
                <th>公司 / 岗位</th>
                <th>档次</th>
                <th>当前进度</th>
                <th>我的分组</th>
                <th>下一场</th>
                <th>投递链接</th>
                <th>查进度</th>
                <th>备注</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                    <td colSpan={9}>
                    <div className="empty">
                      暂无进度。去 <Link to="/jobs">职位信息</Link> 加入投递，或手动新增。
                    </div>
                  </td>
                </tr>
              ) : (
                filtered.map((c) => (
                  <tr
                    key={c.stem}
                    className="clickable"
                    onClick={() => navigate(`/applications/${encodeURIComponent(c.stem)}`)}
                  >
                    <td>
                      <div className="company-cell">
                        <div className="name">{String(c.meta["公司"])}</div>
                        <div className="pos">{String(c.meta["岗位"])}</div>
                      </div>
                    </td>
                    <td>
                      <span className={tierPillClass(c.company_tier || "")}>
                        {c.company_tier || "—"}
                      </span>
                      {c.role_family ? (
                        <div className="sub" style={{ marginTop: 4 }}>
                          {c.role_family}
                        </div>
                      ) : null}
                    </td>
                    <td>
                      <div className="mini-progress">
                        <ProcessStepper stages={c.stages} compact />
                        <div className="sub">
                          {c.current_stage || "—"} ·{" "}
                          {c.stages.filter((s) => s.state === "done").length}/{c.stages.length}
                        </div>
                      </div>
                    </td>
                    <td
                      onClick={(e) => e.stopPropagation()}
                    >
                      <select
                        value={String(c.meta["优先级"] || "")}
                        onChange={async (e) => {
                          await api.patchProgress(c.stem, { 优先级: e.target.value });
                          await loadList();
                        }}
                      >
                        {(enums?.priorities || []).map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      {c.next_event
                        ? `${c.next_event.label} ${c.next_event.when}`
                        : "—"}
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {c.meta["投递链接"] ? (
                        <a
                          href={String(c.meta["投递链接"])}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          打开
                        </a>
                      ) : (
                        <span className="sub">—</span>
                      )}
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {c.meta["投递记录查询"] ? (
                        <a
                          className="btn sm secondary"
                          href={String(c.meta["投递记录查询"])}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          查进度
                        </a>
                      ) : (
                        <span className="sub">—</span>
                      )}
                    </td>
                    <td>
                      <div className="clamp">{String(c.meta["备注"] || "—")}</div>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {c.phase === "rejected" ||
                      c.phase === "stopped" ||
                      coarseStatus(c) === "fail" ? (
                        <button
                          type="button"
                          className="btn sm"
                          disabled={saving}
                          onClick={async () => {
                            await restoreFollow(c.stem);
                          }}
                        >
                          恢复
                        </button>
                      ) : c.phase === "offer" || coarseStatus(c) === "pass" ? (
                        <span className="sub">—</span>
                      ) : (
                        <button
                          type="button"
                          className="btn sm secondary"
                          disabled={saving}
                          onClick={async () => {
                            if (
                              !confirm(
                                `将「${c.meta["公司"]} · ${c.meta["岗位"]}」归档为未通过？\n可随时在「未通过」页恢复跟进。`,
                              )
                            ) {
                              return;
                            }
                            await softArchive(c.stem, "rejected");
                          }}
                        >
                          归档
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {createOpen ? (
        <div className="modal-backdrop" onClick={() => setCreateOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>手动新增投递</h2>
              <button
                type="button"
                className="btn secondary sm"
                onClick={() => setCreateOpen(false)}
              >
                关闭
              </button>
            </div>
            <div className="toolbar">
              <div className="field">
                <label>公司</label>
                <input
                  value={createForm.company}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, company: e.target.value }))
                  }
                />
              </div>
              <div className="field">
                <label>岗位</label>
                <input
                  value={createForm.position}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, position: e.target.value }))
                  }
                />
              </div>
              <div className="field">
                <label>Base</label>
                <input
                  value={createForm.base}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, base: e.target.value }))
                  }
                />
              </div>
              <div className="field grow">
                <label>投递链接</label>
                <input
                  value={createForm.link}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, link: e.target.value }))
                  }
                />
              </div>
              <div className="field">
                <label>招聘计划</label>
                <select
                  value={createForm.plan}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, plan: e.target.value }))
                  }
                >
                  {(enums?.plans || ["校招正式批", "校招提前批", "人才计划"]).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>分组优先级</label>
                <select
                  value={createForm.priority}
                  onChange={(e) =>
                    setCreateForm((f) => ({ ...f, priority: e.target.value }))
                  }
                >
                  {(enums?.priorities || []).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="toolbar">
              <button
                type="button"
                className="btn"
                disabled={saving || !createForm.company || !createForm.position}
                onClick={createRecord}
              >
                创建并打开
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
