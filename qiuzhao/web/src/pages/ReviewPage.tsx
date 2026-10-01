import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { CodingChecklistGroup, ReviewItem, ReviewQuestion } from "../types";

type Tab = "questions" | "coding" | "bank" | "summary";

const MASTERY = ["", "未掌握", "模糊", "可口述", "熟练"];

function emptyQuestion(kind: ReviewQuestion["kind"] = "面试", text = ""): ReviewQuestion {
  return { kind, text, answer: "", ref: "", mastery: "" };
}

function isCoding(q: ReviewQuestion) {
  return (q.kind || "面试") === "手撕";
}

export function ReviewPage() {
  const { stem: routeStem } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [selected, setSelected] = useState<ReviewItem | null>(null);
  const [q, setQ] = useState("");
  const [tab, setTab] = useState<Tab>("questions");
  const [questions, setQuestions] = useState<ReviewQuestion[]>([]);
  const [reflection, setReflection] = useState("");
  const [nextActions, setNextActions] = useState("");
  const [bankGroups, setBankGroups] = useState<
    { type: string; questions: { index: number; text: string }[] }[]
  >([]);
  const [codingGroups, setCodingGroups] = useState<CodingChecklistGroup[]>([]);
  const [codingFilter, setCodingFilter] = useState<"company" | "all">("company");
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  const companyName = selected ? String(selected.meta["公司"] || "") : "";

  const loadList = async () => {
    const data = await api.listReviews(q);
    setItems(data.items);
    return data.items;
  };

  const loadCoding = async (company: string, mode: "company" | "all") => {
    const data = await api.getCodingList(mode === "company" ? company : "");
    setCodingGroups(data.groups || []);
  };

  const open = async (stem: string) => {
    navigate(`/review/${encodeURIComponent(stem)}`);
    const detail = await api.getReview(stem);
    setSelected(detail);
    setQuestions(
      (detail.questions || []).map((qq) => ({
        kind: qq.kind || "面试",
        text: qq.text,
        answer: qq.answer || "",
        ref: qq.ref || "",
        mastery: qq.mastery || "",
      }))
    );
    setReflection(detail.reflection || "");
    setNextActions(detail.next_actions || "");
    const company = String(detail.meta["公司"] || "");
    const [bank, coding] = await Promise.all([
      api.getReviewBank(stem),
      api.getCodingList(company),
    ]);
    const groups = [...(bank.groups || [])];
    groups.sort((a, b) => Number(b.type.includes("手撕")) - Number(a.type.includes("手撕")));
    setBankGroups(groups);
    setCodingGroups(coding.groups || []);
    setCodingFilter("company");
  };

  useEffect(() => {
    (async () => {
      setError("");
      try {
        const list = await loadList();
        const target = routeStem || list[0]?.stem;
        if (target) await open(target);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeStem]);

  const save = async () => {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      const detail = await api.patchReview(selected.stem, {
        questions,
        reflection,
        next_actions: nextActions,
      });
      setSelected(detail);
      setQuestions(detail.questions || []);
      setMsg("复盘已写回 Obsidian");
      await loadList();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const interviewQs = useMemo(() => questions.filter((qq) => !isCoding(qq)), [questions]);
  const codingQs = useMemo(() => questions.filter(isCoding), [questions]);

  const updateQuestion = (globalIndex: number, patch: Partial<ReviewQuestion>) => {
    setQuestions((prev) => prev.map((row, i) => (i === globalIndex ? { ...row, ...patch } : row)));
  };

  const addQuestion = (kind: ReviewQuestion["kind"] = "面试", text = "") => {
    setQuestions((prev) => [...prev, emptyQuestion(kind, text)]);
  };

  const addFromSource = (text: string, kind: ReviewQuestion["kind"]) => {
    if (questions.some((row) => row.text === text && (row.kind || "面试") === kind)) {
      setMsg("题目已在本轮列表中");
      return;
    }
    addQuestion(kind, text);
    setTab(kind === "手撕" ? "coding" : "questions");
    setMsg(`已加入：${text.slice(0, 40)}`);
  };

  const renderQuestionCard = (qq: ReviewQuestion, globalIndex: number, displayNo: number) => (
    <div key={globalIndex} className="question-card">
      <div className="question-card-head">
        <span className="pill gray">{displayNo}</span>
        <span className={`pill ${isCoding(qq) ? "green" : "blue"}`}>{qq.kind || "面试"}</span>
        <input
          type="text"
          value={qq.text}
          placeholder={isCoding(qq) ? "手撕题名，如 LRU 缓存" : "题干"}
          onChange={(e) => updateQuestion(globalIndex, { text: e.target.value })}
        />
        <button
          className="btn sm secondary"
          onClick={() => setQuestions(questions.filter((_, i) => i !== globalIndex))}
        >
          删
        </button>
      </div>
      <div className="question-card-grid">
        <div className="field">
          <label>我的回答要点</label>
          <textarea
            value={qq.answer}
            placeholder={isCoding(qq) ? "思路 / 复杂度 / 卡点" : "口述要点"}
            onChange={(e) => updateQuestion(globalIndex, { answer: e.target.value })}
          />
        </div>
        <div className="field">
          <label>参考 / 标准答</label>
          <textarea
            value={qq.ref}
            onChange={(e) => updateQuestion(globalIndex, { ref: e.target.value })}
          />
        </div>
        <div className="field">
          <label>掌握度</label>
          <select
            value={qq.mastery}
            onChange={(e) => updateQuestion(globalIndex, { mastery: e.target.value })}
          >
            {MASTERY.map((m) => (
              <option key={m || "empty"} value={m}>
                {m || "未标"}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div>
          <h1>面试复盘</h1>
          <div className="sub">题目 + 手撕写回 03_面经 · 公司题库与高频清单只读引用</div>
        </div>
        {selected ? (
          <button className="btn" onClick={save} disabled={saving}>
            {saving ? "保存中…" : "完成本轮复盘保存"}
          </button>
        ) : null}
      </div>

      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="flash">{msg}</div> : null}

      <div className="split">
        <div className="panel">
          <div className="toolbar">
            <div className="field" style={{ flex: 1 }}>
              <label>搜索公司</label>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="腾讯 / 百度…"
              />
            </div>
            <button
              className="btn secondary"
              onClick={async () => {
                const list = await loadList();
                if (list[0]) await open(list[0].stem);
              }}
            >
              筛选
            </button>
          </div>
          {items.map((c) => (
            <div
              key={c.stem}
              className={`list-item ${selected?.stem === c.stem ? "active" : ""}`}
              onClick={() => open(c.stem)}
            >
              <div className="title">{String(c.meta["公司"] || c.stem)}</div>
              <div className="meta">
                <span className="pill">{c.status}</span>{" "}
                {String(c.meta["轮次"] || "")} {String(c.meta["面试日期"] || "")}
              </div>
            </div>
          ))}
          {items.length === 0 ? <div className="empty">暂无面经复盘笔记</div> : null}
        </div>

        <div className="panel">
          {!selected ? (
            <div className="empty">选择左侧公司开始复盘</div>
          ) : (
            <>
              <h2>
                {String(selected.meta["公司"])} · 当前复盘
              </h2>
              <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
                {selected.progress_stem ? (
                  <Link
                    className="btn sm secondary"
                    to={`/applications/${encodeURIComponent(selected.progress_stem)}`}
                  >
                    打开投递
                  </Link>
                ) : null}
                {selected.intel_stem ? (
                  <Link
                    className="btn sm secondary"
                    to={`/jobs?q=${encodeURIComponent(companyName)}`}
                  >
                    关联情报
                  </Link>
                ) : null}
                <span className="pill gray">面试 {interviewQs.length}</span>
                <span className="pill green">手撕 {codingQs.length}</span>
              </div>

              <div className="tabs">
                <button
                  className={tab === "questions" ? "active" : ""}
                  onClick={() => setTab("questions")}
                >
                  题目回顾
                </button>
                <button className={tab === "coding" ? "active" : ""} onClick={() => setTab("coding")}>
                  手撕题
                </button>
                <button className={tab === "bank" ? "active" : ""} onClick={() => setTab("bank")}>
                  公司题库
                </button>
                <button
                  className={tab === "summary" ? "active" : ""}
                  onClick={() => setTab("summary")}
                >
                  复盘总结
                </button>
              </div>

              {tab === "questions" ? (
                <>
                  <div style={{ marginBottom: 8, color: "var(--muted)" }}>
                    本轮面试题 {interviewQs.length} 道（不含手撕）
                  </div>
                  {interviewQs.map((qq) => {
                    const globalIndex = questions.indexOf(qq);
                    const displayNo = interviewQs.indexOf(qq) + 1;
                    return renderQuestionCard(qq, globalIndex, displayNo);
                  })}
                  <button
                    className="btn secondary"
                    style={{ marginTop: 8 }}
                    onClick={() => addQuestion("面试")}
                  >
                    + 添加面试题
                  </button>
                </>
              ) : null}

              {tab === "coding" ? (
                <>
                  <div style={{ marginBottom: 8, color: "var(--muted)" }}>
                    本轮手撕 {codingQs.length} 道 · 从高频清单或公司题库加入，勾选不回写清单
                  </div>
                  {codingQs.map((qq) => {
                    const globalIndex = questions.indexOf(qq);
                    const displayNo = codingQs.indexOf(qq) + 1;
                    return renderQuestionCard(qq, globalIndex, displayNo);
                  })}
                  <button
                    className="btn secondary"
                    style={{ marginTop: 8, marginBottom: 16 }}
                    onClick={() => addQuestion("手撕")}
                  >
                    + 添加手撕
                  </button>
                  <h3>高频手撕清单</h3>
                  <div className="toolbar">
                    <div className="field">
                      <label>范围</label>
                      <select
                        value={codingFilter}
                        onChange={async (e) => {
                          const mode = e.target.value as "company" | "all";
                          setCodingFilter(mode);
                          await loadCoding(companyName, mode);
                        }}
                      >
                        <option value="company">本公司来源</option>
                        <option value="all">全部知识点</option>
                      </select>
                    </div>
                  </div>
                  {codingGroups.length === 0 ? (
                    <div className="empty">
                      {codingFilter === "company"
                        ? "清单里没有标注该公司来源的题，可切到「全部知识点」。"
                        : "暂无高频手撕清单。"}
                    </div>
                  ) : (
                    codingGroups.map((g) => (
                      <div key={g.topic} className="bank-group">
                        <h4>#{g.topic}</h4>
                        <ol>
                          {g.items.map((it) => (
                            <li key={it.text}>
                              {it.done ? <span className="pill green">已练</span> : null} {it.text}
                              {it.sources.length ? (
                                <span className="sub"> · {it.sources.join("、")}</span>
                              ) : null}{" "}
                              <button
                                className="btn sm secondary"
                                onClick={() => addFromSource(it.text, "手撕")}
                              >
                                本轮考到
                              </button>
                            </li>
                          ))}
                        </ol>
                      </div>
                    ))
                  )}
                </>
              ) : null}

              {tab === "bank" ? (
                bankGroups.length === 0 ? (
                  <div className="empty">暂无该公司题库。可用 Agent 处理面经图片或牛客帖。</div>
                ) : (
                  bankGroups.map((g) => {
                    const codingGroup = g.type.includes("手撕");
                    return (
                      <div key={g.type} className={`bank-group ${codingGroup ? "coding" : ""}`}>
                        <h4>
                          #{g.type}{" "}
                          {codingGroup ? <span className="pill green">手撕</span> : null}
                        </h4>
                        <ol>
                          {g.questions.map((qq) => (
                            <li key={qq.index}>
                              {qq.text}{" "}
                              <button
                                className="btn sm secondary"
                                onClick={() =>
                                  addFromSource(qq.text, codingGroup ? "手撕" : "面试")
                                }
                              >
                                本轮考到
                              </button>
                            </li>
                          ))}
                        </ol>
                      </div>
                    );
                  })
                )
              ) : null}

              {tab === "summary" ? (
                <>
                  <div className="field">
                    <label>反思</label>
                    <textarea
                      value={reflection}
                      onChange={(e) => setReflection(e.target.value)}
                      style={{ minHeight: 120 }}
                    />
                  </div>
                  <div className="field">
                    <label>下次改进</label>
                    <textarea
                      value={nextActions}
                      onChange={(e) => setNextActions(e.target.value)}
                      style={{ minHeight: 100 }}
                    />
                  </div>
                </>
              ) : null}
            </>
          )}
        </div>
      </div>
    </>
  );
}
