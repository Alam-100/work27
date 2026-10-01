import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AgentJob, HealthInfo, NoteCard } from "../types";

export function MorePage() {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [jobs, setJobs] = useState<AgentJob[]>([]);
  const [studyOpen, setStudyOpen] = useState<NoteCard[]>([]);
  const [urls, setUrls] = useState("");
  const [company, setCompany] = useState("");
  const [studyTitle, setStudyTitle] = useState("");
  const [studyType, setStudyType] = useState("手撕");
  const [intent, setIntent] = useState("链接入库");
  const [intentPayload, setIntentPayload] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    const [h, j, s] = await Promise.all([
      api.health(false),
      api.listAgentJobs(),
      api.listStudy(),
    ]);
    setHealth(h);
    setJobs(j.items);
    setStudyOpen(s.open);
  };

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const enqueue = async (intent: string, payload: string) => {
    setError("");
    try {
      await api.createAgentJob(intent, payload);
      setMsg(`已入队：${intent}。请在 Cursor 说：处理控制台任务`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>更多</h1>
          <div className="sub">Agent 入队 · 学习任务 · 健康检查 · 旧版入口</div>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="flash">{msg}</div> : null}

      <div className="stats">
        <div className="stat-card">
          <div className="label">情报卡（含央国企）</div>
          <div className="value">{health?.intel_count ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="label">投递</div>
          <div className="value">{health?.progress_count ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="label">面经</div>
          <div className="value">{health?.mianshi_count ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="label">Agent 待处理</div>
          <div className="value">{health?.pending_jobs ?? "—"}</div>
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <h2>任务入队</h2>
          <div className="toolbar">
            <div className="field">
              <label>意图</label>
              <select value={intent} onChange={(e) => setIntent(e.target.value)}>
                {(health?.enums.agent_intents || ["链接入库", "收集公司", "每日情报更新", "面经图片"]).map(
                  (t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  )
                )}
              </select>
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>载荷</label>
              <input
                value={intentPayload}
                onChange={(e) => setIntentPayload(e.target.value)}
                placeholder="公司名 / 链接 / 核实:公司|stem"
              />
            </div>
            <button className="btn" onClick={() => enqueue(intent, intentPayload.trim())}>
              入队
            </button>
          </div>
          <div className="field">
            <label>批量链接（每行一个）</label>
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} />
          </div>
          <button
            className="btn"
            onClick={() => {
              const lines = urls
                .split(/\n/)
                .map((l) => l.trim())
                .filter((l) => l.startsWith("http"));
              if (!lines.length) {
                setError("未识别到 http(s) 链接");
                return;
              }
              enqueue("链接入库", lines.join(" "));
            }}
          >
            链接入库
          </button>

          <div className="toolbar" style={{ marginTop: 16 }}>
            <div className="field" style={{ flex: 1 }}>
              <label>收集公司</label>
              <input value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
            <button
              className="btn secondary"
              onClick={() => {
                if (!company.trim()) return setError("请填写公司名");
                enqueue("收集公司", company.trim());
              }}
            >
              入队
            </button>
          </div>

          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button className="btn secondary" onClick={() => enqueue("每日情报更新", "")}>
              请求日更
            </button>
            <button
              className="btn secondary"
              onClick={() => enqueue("面经图片", company.trim() || "（见 _inbox_images）")}
            >
              处理面经图片
            </button>
          </div>

          <h3 style={{ marginTop: 20 }}>最近队列</h3>
          {jobs.slice(0, 12).map((j) => (
            <div key={j.id} className="list-item" style={{ cursor: "default" }}>
              <div className="title">
                {j.intent} · {j.id}
              </div>
              <div className="meta">
                <span className="pill">{j.status}</span> {j.created_at} {j.payload.slice(0, 60)}
              </div>
            </div>
          ))}
        </div>

        <div className="panel">
          <h2>学习任务</h2>
          <div className="toolbar">
            <div className="field" style={{ flex: 1 }}>
              <label>标题</label>
              <input value={studyTitle} onChange={(e) => setStudyTitle(e.target.value)} />
            </div>
            <div className="field">
              <label>类型</label>
              <select value={studyType} onChange={(e) => setStudyType(e.target.value)}>
                {(health?.enums.study_types || ["面经", "手撕", "知识"]).map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <button
              className="btn"
              onClick={async () => {
                if (!studyTitle.trim()) return setError("请填写标题");
                await api.createStudy({ title: studyTitle.trim(), study_type: studyType });
                setStudyTitle("");
                setMsg("已安排学习任务");
                await refresh();
              }}
            >
              新建
            </button>
          </div>
          {studyOpen.map((c) => (
            <div key={c.stem} className="list-item" style={{ cursor: "default" }}>
              <div className="title">{String(c.meta["标题"] || c.stem)}</div>
              <div className="meta">
                {String(c.meta["类型"] || "")} · {String(c.meta["状态"] || "")}{" "}
                <button
                  className="btn sm secondary"
                  onClick={async () => {
                    await api.patchStudy(c.stem, "完成");
                    await refresh();
                  }}
                >
                  完成
                </button>
              </div>
            </div>
          ))}

          <h3 style={{ marginTop: 20 }}>系统</h3>
          <p style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
            Vault：{health?.vault || "—"}
            <br />
            {health?.qiuzhao_ok ? "秋招目录正常" : "秋招目录异常"}
          </p>
          <p>
            <a href="/legacy">打开旧版 Jinja 控制台</a>
            {" · "}
            <a href="/api/docs" target="_blank" rel="noreferrer">
              API 文档
            </a>
          </p>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            Agent 口令：在 Cursor 说「处理控制台任务」
          </p>
        </div>
      </div>
    </>
  );
}
