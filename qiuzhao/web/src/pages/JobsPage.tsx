import { Fragment, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { Pager } from "../components/Pager";
import { tierPillClass } from "../lib/labels";
import type { HealthInfo, IntelCompanyGroup, IntelItem } from "../types";

type TierStats = { 大厂: number; 中厂: number; 小厂: number; 央国企: number; 外企: number; other: number };
type Scope = "active" | "closed";

const DEFAULT_SORT = "deadline_then_score";
const DEFAULT_PAGE_SIZE_COMPANY = 20;

/** 默认折叠；将截止（剩余 ≤7 天）自动展开。closed 分区默认全折叠。 */
function buildCollapseState(
  list: IntelCompanyGroup[],
  scope: Scope
): Record<string, boolean> {
  const next: Record<string, boolean> = {};
  for (const co of list) {
    if (scope === "closed") {
      next[co.company] = true;
    } else {
      const urgent =
        co.earliest_deadline != null &&
        co.earliest_deadline >= 0 &&
        co.earliest_deadline <= 7;
      next[co.company] = !urgent;
    }
  }
  return next;
}

export function JobsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const urlQ = searchParams.get("q") || "";
  const [items, setItems] = useState<IntelItem[]>([]);
  const [companies, setCompanies] = useState<IntelCompanyGroup[]>([]);
  const [enums, setEnums] = useState<HealthInfo["enums"] | null>(null);
  const [q, setQ] = useState(urlQ);
  const [plan, setPlan] = useState("");
  const [deadline, setDeadline] = useState("all");
  const [tier, setTier] = useState("");
  const [roleFamily, setRoleFamily] = useState("");
  const [hiringStatus, setHiringStatus] = useState("");
  const [applyPriority, setApplyPriority] = useState("");
  const [sort, setSort] = useState(DEFAULT_SORT);
  const [scope, setScope] = useState<Scope>("active");
  const [groupMode, setGroupMode] = useState<"company" | "">("company");
  const [minScore, setMinScore] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE_COMPANY);
  const [pageUnit, setPageUnit] = useState<"job" | "company">("company");
  const [total, setTotal] = useState(0);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [pages, setPages] = useState(1);
  const [stats, setStats] = useState({
    hiring: 0,
    closed: 0,
    followed: 0,
    urgent: 0,
    tiers: { 大厂: 0, 中厂: 0, 小厂: 0, 央国企: 0, 外企: 0, other: 0 } as TierStats,
  });
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<IntelItem | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.enums().then((r) => setEnums(r.enums)).catch(() => undefined);
  }, []);

  const load = async (pageOverride?: number, overrides?: Record<string, string | number | undefined>) => {
    const nextPage = pageOverride ?? page;
    setLoading(true);
    setError("");
    try {
      const params = {
        q: q || urlQ,
        plan,
        deadline: deadline === "all" ? "" : deadline,
        tier,
        role_family: roleFamily,
        hiring_status: hiringStatus,
        apply_priority: applyPriority,
        scope,
        sort,
        group: groupMode,
        min_score: minScore ? Number(minScore) : undefined,
        page: nextPage,
        page_size: pageSize,
        ...overrides,
      };
      const nextScope = (String(params.scope || scope) as Scope) || "active";
      const data = await api.listIntel(params);
      setItems(data.items);
      const nextCompanies = data.companies || [];
      setCompanies(nextCompanies);
      setTotal(data.total_jobs ?? data.total);
      setTotalCompanies(data.total_companies ?? 0);
      setPages(data.pages);
      setPage(data.page);
      setPageUnit(data.page_unit === "company" ? "company" : "job");
      setCollapsed(buildCollapseState(nextCompanies, nextScope));
      setStats({
        hiring: data.stats?.hiring ?? data.total,
        closed: data.stats?.closed ?? 0,
        followed: data.stats?.followed ?? 0,
        urgent: data.stats?.urgent ?? 0,
        tiers: {
          大厂: data.stats?.tiers?.大厂 ?? 0,
          中厂: data.stats?.tiers?.中厂 ?? 0,
          小厂: data.stats?.tiers?.小厂 ?? 0,
          央国企: data.stats?.tiers?.央国企 ?? 0,
          外企: data.stats?.tiers?.外企 ?? 0,
          other: data.stats?.tiers?.other ?? 0,
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (urlQ && urlQ !== q) setQ(urlQ);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlQ]);

  useEffect(() => {
    load(undefined, urlQ ? { q: urlQ } : undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, groupMode, scope, urlQ]);

  const applyFilters = () => {
    if (page !== 1) {
      setPage(1);
    } else {
      load(1);
    }
  };

  const switchScope = (next: Scope) => {
    if (next === scope) return;
    setScope(next);
    setPage(1);
  };

  const practiceView = () => {
    setTier("中厂,小厂");
    setApplyPriority("练手优先");
    setSort(DEFAULT_SORT);
    setHiringStatus("");
    setRoleFamily("");
    setDeadline("all");
    setScope("active");
    setPage(1);
    void load(1, {
      tier: "中厂,小厂",
      apply_priority: "练手优先",
      sort: DEFAULT_SORT,
      hiring_status: "",
      role_family: "",
      deadline: "",
      scope: "active",
    });
  };

  const soeView = () => {
    setTier("央国企");
    setApplyPriority("保底");
    setSort(DEFAULT_SORT);
    setHiringStatus("");
    setRoleFamily("");
    setDeadline("all");
    setScope("active");
    setPage(1);
    void load(1, {
      tier: "央国企",
      apply_priority: "保底",
      sort: DEFAULT_SORT,
      hiring_status: "",
      role_family: "",
      deadline: "",
      scope: "active",
    });
  };

  const clearFilters = () => {
    setQ("");
    setPlan("");
    setDeadline("all");
    setTier("");
    setRoleFamily("");
    setHiringStatus("");
    setApplyPriority("");
    setSort(DEFAULT_SORT);
    setScope("active");
    setMinScore("");
    setPage(1);
    void load(1, {
      q: "",
      plan: "",
      deadline: "",
      tier: "",
      role_family: "",
      hiring_status: "",
      apply_priority: "",
      sort: DEFAULT_SORT,
      scope: "active",
      min_score: undefined,
    });
  };

  const openDetail = async (stem: string) => {
    try {
      const d = await api.getIntel(stem);
      setDetail(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const follow = async (stem: string) => {
    setBusy(stem);
    try {
      const r = await api.followIntel(stem);
      setMsg(
        r.apply_limit_warning
          ? `${r.apply_limit_warning} 已加入：${r.progress_stem}`
          : `已加入投递：${r.progress_stem}`
      );
      await load();
      navigate(`/applications/${encodeURIComponent(r.progress_stem)}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const verify = async (stem: string) => {
    setBusy(stem);
    try {
      const r = await api.verifyIntel(stem);
      setMsg(r.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const toggleCompany = (name: string) => {
    setCollapsed((prev) => {
      const currentlyCollapsed = prev[name] === undefined ? true : prev[name];
      return { ...prev, [name]: !currentlyCollapsed };
    });
  };

  const expandAll = () => {
    setCollapsed((prev) => {
      const next = { ...prev };
      for (const co of companies) next[co.company] = false;
      return next;
    });
  };

  const collapseAll = () => {
    setCollapsed((prev) => {
      const next = { ...prev };
      for (const co of companies) next[co.company] = true;
      return next;
    });
  };

  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to =
    pageUnit === "company"
      ? Math.min(page * pageSize, totalCompanies)
      : Math.min(page * pageSize, total);

  const pagerLabel = useMemo(() => {
    if (pageUnit === "company") {
      return `共 ${totalCompanies} 家公司 · ${total} 岗 · 显示第 ${from}-${to} 家 · 第 ${page}/${pages} 页`;
    }
    return `共 ${total} 岗 · 显示 ${from}-${to} · 第 ${page}/${pages} 页`;
  }, [pageUnit, totalCompanies, total, page, pages, from, to]);

  const renderJobRow = (c: IntelItem, indent = false) => {
    const company = String(c.meta["公司"] || c.stem);
    const position = String(c.meta["岗位"] || "");
    const status = c.hiring_status || String(c.meta["招聘状态"] || "—");
    const urgent = status === "将截止" || (c.days_left != null && c.days_left <= 7 && c.days_left >= 0);
    const closed = status === "已截止" || scope === "closed";
    return (
      <tr key={c.stem} style={closed ? { opacity: 0.72 } : undefined}>
        <td>
          {c.days_left != null ? (
            <span className={`pill ${urgent ? "red" : closed ? "gray" : "gray"}`}>
              {c.days_left >= 0 ? `剩 ${c.days_left} 天` : `已过 ${-c.days_left} 天`}
            </span>
          ) : (
            <span className="pill gray">招满即止</span>
          )}
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: 4 }}>
            {String(c.meta["投递截止"] || "—")}
          </div>
        </td>
        <td>
          <div className="company-cell" style={indent ? { paddingLeft: 18 } : undefined}>
            {!indent ? <span className="avatar">{company.slice(0, 1)}</span> : null}
            <div>
              {!indent ? <div className="name">{company}</div> : null}
              <div className={indent ? "name" : "pos"}>{position}</div>
              {c.followed_by ? (
                <span className="pill green" style={{ marginTop: 4 }}>
                  已在投递
                </span>
              ) : null}
            </div>
          </div>
        </td>
        <td>
          <span className={tierPillClass(c.company_tier || String(c.meta["公司档次"] || ""))}>
            {c.company_tier || String(c.meta["公司档次"] || "—")}
          </span>
        </td>
        <td>{c.role_family || String(c.meta["岗位族"] || "—")}</td>
        <td>
          <span className={`pill ${urgent ? "red" : "gray"}`}>{status}</span>
        </td>
        <td>{c.apply_priority || String(c.meta["投递优先级"] || "—")}</td>
        <td>
          <strong>{String(c.meta["匹配分"] ?? "—")}</strong>
        </td>
        <td style={{ whiteSpace: "nowrap" }}>
          <button className="btn sm secondary" onClick={() => openDetail(c.stem)}>
            详情
          </button>{" "}
          <button
            className={`btn sm ${closed ? "secondary" : ""}`}
            disabled={busy === c.stem || !!c.followed_by}
            onClick={() => follow(c.stem)}
            title={closed ? "岗位已截止，仍可加入投递作记录" : undefined}
          >
            {c.followed_by ? "已跟进" : "加入投递"}
          </button>{" "}
          <button
            className="btn sm secondary"
            disabled={busy === c.stem}
            onClick={() => verify(c.stem)}
          >
            核实
          </button>{" "}
          {c.meta["投递链接"] ? (
            <a
              className="btn sm secondary"
              href={String(c.meta["投递链接"])}
              target="_blank"
              rel="noreferrer"
            >
              官网
            </a>
          ) : null}
        </td>
      </tr>
    );
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>职位信息</h1>
          <div className="sub">
            按公司分页 · 截止优先 · 已截止进 _归档（不删）· 限投 · 先中小厂练手 / 央国企保底
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" className="btn" onClick={practiceView}>
            练手视图
          </button>
          <button type="button" className="btn" onClick={soeView}>
            保底视图
          </button>
          <button type="button" className="btn secondary" onClick={clearFilters}>
            清空筛选
          </button>
        </div>
      </div>

      <div className="stats">
        <div className="stat-card">
          <div className="label">在招岗</div>
          <div className="value">{stats.hiring}</div>
        </div>
        <div className="stat-card">
          <div className="label">已截止</div>
          <div className="value">{stats.closed}</div>
        </div>
        <div className="stat-card">
          <div className="label">大厂</div>
          <div className="value">{stats.tiers.大厂}</div>
        </div>
        <div className="stat-card">
          <div className="label">中厂</div>
          <div className="value">{stats.tiers.中厂}</div>
        </div>
        <div className="stat-card">
          <div className="label">小厂</div>
          <div className="value">{stats.tiers.小厂}</div>
        </div>
        <div className="stat-card">
          <div className="label">央国企</div>
          <div className="value">{stats.tiers.央国企}</div>
        </div>
        <div className="stat-card">
          <div className="label">外企</div>
          <div className="value">{stats.tiers.外企}</div>
        </div>
        {stats.tiers.other > 0 ? (
          <div className="stat-card">
            <div className="label">未分档</div>
            <div className="value">{stats.tiers.other}</div>
          </div>
        ) : null}
        <div className="stat-card">
          <div className="label">本周截止</div>
          <div className="value">{stats.urgent}</div>
        </div>
        <div className="stat-card">
          <div className="label">已跟进</div>
          <div className="value">{stats.followed}</div>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="flash">{msg}</div> : null}

      <div className="panel">
        <div className="tabs">
          <button
            type="button"
            className={scope === "active" ? "active" : ""}
            onClick={() => switchScope("active")}
          >
            在招 {stats.hiring}
          </button>
          <button
            type="button"
            className={scope === "closed" ? "active" : ""}
            onClick={() => switchScope("closed")}
          >
            已截止 {stats.closed}
          </button>
        </div>

        <div className="toolbar">
          <div className="field" style={{ flex: 1, minWidth: 160 }}>
            <label>搜索</label>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") applyFilters();
              }}
              placeholder="公司 / 岗位"
            />
          </div>
          <div className="field">
            <label>展示</label>
            <select
              value={groupMode}
              onChange={(e) => {
                const next = e.target.value as "company" | "";
                setGroupMode(next);
                setPageSize(next === "company" ? DEFAULT_PAGE_SIZE_COMPANY : 20);
                setPage(1);
              }}
            >
              <option value="company">按公司</option>
              <option value="">扁平列表</option>
            </select>
          </div>
          <div className="field">
            <label>公司档次</label>
            <select value={tier} onChange={(e) => setTier(e.target.value)}>
              <option value="">不限</option>
              <option value="中厂,小厂">中厂+小厂</option>
              {(enums?.company_tiers || ["大厂", "中厂", "小厂", "央国企", "外企"]).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>岗位族</label>
            <select value={roleFamily} onChange={(e) => setRoleFamily(e.target.value)}>
              <option value="">不限</option>
              {(enums?.role_families || []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>招聘状态</label>
            <select value={hiringStatus} onChange={(e) => setHiringStatus(e.target.value)}>
              <option value="">不限</option>
              {(enums?.hiring_statuses || []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>投递优先级</label>
            <select value={applyPriority} onChange={(e) => setApplyPriority(e.target.value)}>
              <option value="">不限</option>
              {(enums?.apply_priorities || []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>招聘计划</label>
            <select value={plan} onChange={(e) => setPlan(e.target.value)}>
              <option value="">不限</option>
              {(enums?.plans || []).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>投递截止</label>
            <select value={deadline} onChange={(e) => setDeadline(e.target.value)}>
              <option value="all">全部</option>
              <option value="week">本周内</option>
              <option value="month">本月</option>
              <option value="none">无固定截止</option>
              <option value="past">已过期</option>
            </select>
          </div>
          <div className="field">
            <label>排序</label>
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="deadline_then_score">截止优先（再匹配分）</option>
              <option value="score_desc">匹配分↓</option>
              <option value="deadline_asc">截止升序</option>
            </select>
          </div>
          <div className="field">
            <label>最低匹配分</label>
            <input
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
              placeholder="如 70"
              type="number"
            />
          </div>
          <div className="field">
            <label>{groupMode === "company" ? "每页公司" : "每页岗数"}</label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
          <button className="btn" onClick={applyFilters} disabled={loading}>
            {loading ? "加载中…" : "筛选"}
          </button>
          {groupMode === "company" && companies.length > 0 ? (
            <>
              <button type="button" className="btn secondary" onClick={expandAll}>
                全部展开
              </button>
              <button type="button" className="btn secondary" onClick={collapseAll}>
                全部折叠
              </button>
            </>
          ) : null}
        </div>

        {loading && !items.length && !companies.length ? (
          <div className="empty">加载中…</div>
        ) : groupMode === "company" ? (
          companies.length === 0 ? (
            <div className="empty">
              {scope === "closed"
                ? "当前筛选下暂无已截止岗位。"
                : "无匹配在招岗位。试试「练手视图」或清空筛选。"}
            </div>
          ) : (
            <>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>截止</th>
                      <th>公司与岗位</th>
                      <th>档次</th>
                      <th>岗位族</th>
                      <th>状态</th>
                      <th>优先级</th>
                      <th>匹配</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {companies.map((co) => {
                      // 缺省视为折叠（与 buildCollapseState 一致）；显式 false 才展开
                      const collapsedFlag = collapsed[co.company];
                      const reallyCollapsed =
                        collapsedFlag === undefined ? true : collapsedFlag;
                      const urgent =
                        scope === "active" &&
                        co.earliest_deadline != null &&
                        co.earliest_deadline >= 0 &&
                        co.earliest_deadline <= 7;
                      return (
                        <Fragment key={`co-${co.company}`}>
                          <tr style={{ background: "var(--panel-2, transparent)" }}>
                            <td>
                              {co.earliest_deadline != null ? (
                                <span className={`pill ${urgent ? "red" : "gray"}`}>
                                  {co.earliest_deadline >= 0
                                    ? `最早剩 ${co.earliest_deadline} 天`
                                    : `已过 ${-co.earliest_deadline} 天`}
                                </span>
                              ) : (
                                <span className="pill gray">
                                  {scope === "closed" ? "无截止日" : "无统一截止"}
                                </span>
                              )}
                            </td>
                            <td>
                              <div className="company-cell">
                                <button
                                  type="button"
                                  className="btn sm secondary"
                                  onClick={() => toggleCompany(co.company)}
                                  aria-label="展开或折叠"
                                >
                                  {reallyCollapsed ? "+" : "−"}
                                </button>
                                <span className="avatar">{co.company.slice(0, 1)}</span>
                                <div>
                                  <div className="name">{co.company}</div>
                                  <div className="pos">
                                    {co.job_count} 岗
                                    {co.followed_count
                                      ? ` · 已跟进 ${co.followed_count}`
                                      : ""}
                                    {" · 限投 "}
                                    {co.apply_limit != null ? co.apply_limit : "未知"}
                                    {co.over_limit ? "（已达上限）" : ""}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td>
                              <span className={tierPillClass(co.tier || "")}>{co.tier || "—"}</span>
                            </td>
                            <td>—</td>
                            <td>
                              {co.over_limit ? (
                                <span className="pill red">超限警告</span>
                              ) : scope === "closed" ? (
                                <span className="pill gray">已截止</span>
                              ) : (
                                <span className="pill gray">公司</span>
                              )}
                            </td>
                            <td>—</td>
                            <td>
                              <strong>{co.max_score ?? "—"}</strong>
                            </td>
                            <td style={{ whiteSpace: "nowrap" }}>
                              {co.portal ? (
                                <a
                                  className="btn sm secondary"
                                  href={co.portal}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  门户
                                </a>
                              ) : null}
                              {co.referral_url ? (
                                <a
                                  className="btn sm secondary"
                                  href={co.referral_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  title={
                                    co.referral_code
                                      ? `内推码 ${co.referral_code}`
                                      : "HR内推"
                                  }
                                  style={{ marginLeft: 4 }}
                                >
                                  内推
                                  {co.referral_code ? ` ${co.referral_code}` : ""}
                                </a>
                              ) : null}
                            </td>
                          </tr>
                          {!reallyCollapsed
                            ? co.jobs.map((j) => renderJobRow(j, true))
                            : null}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <Pager
                page={page}
                pages={pages}
                label={pagerLabel}
                loading={loading}
                onPage={setPage}
              />
            </>
          )
        ) : items.length === 0 ? (
          <div className="empty">
            {scope === "closed"
              ? "当前筛选下暂无已截止岗位。"
              : "无匹配在招岗位。试试「练手视图」或清空筛选。"}
          </div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>截止</th>
                    <th>公司与岗位</th>
                    <th>档次</th>
                    <th>岗位族</th>
                    <th>状态</th>
                    <th>优先级</th>
                    <th>匹配</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>{items.map((c) => renderJobRow(c))}</tbody>
              </table>
            </div>
            <Pager
              page={page}
              pages={pages}
              label={pagerLabel}
              loading={loading}
              onPage={setPage}
            />
          </>
        )}
      </div>

      {detail ? (
        <>
          <div className="drawer-backdrop" onClick={() => setDetail(null)} />
          <aside className="drawer">
            <button className="btn secondary sm" onClick={() => setDetail(null)}>
              关闭
            </button>
            <h2>
              {String(detail.meta["公司"])} · {String(detail.meta["岗位"])}
            </h2>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
              <span className="pill">匹配 {String(detail.meta["匹配分"] ?? "—")}</span>
              <span className={tierPillClass(detail.company_tier || String(detail.meta["公司档次"] || ""))}>
                {detail.company_tier || String(detail.meta["公司档次"] || "")}
              </span>
              <span className="pill">{detail.role_family || String(detail.meta["岗位族"] || "")}</span>
              <span className="pill gray">
                {detail.hiring_status || String(detail.meta["招聘状态"] || "")}
              </span>
              <span className="pill">
                {detail.apply_priority || String(detail.meta["投递优先级"] || "")}
              </span>
              <span className="pill blue">{String(detail.meta["招聘计划"] || "")}</span>
            </div>
            {detail.company_overview ? (
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                本公司投递上限：
                {detail.company_overview.apply_limit != null
                  ? detail.company_overview.apply_limit
                  : "未知"}
                {detail.company_overview.apply_limit_note
                  ? `（${detail.company_overview.apply_limit_note.slice(0, 80)}）`
                  : ""}
                {detail.company_overview.over_limit ? " · 已达/超过已核实上限" : ""}
                {detail.company_overview.referral_url ? (
                  <>
                    {" · "}
                    <a
                      href={detail.company_overview.referral_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      HR内推
                    </a>
                    {detail.company_overview.referral_code
                      ? `（码 ${detail.company_overview.referral_code}）`
                      : ""}
                  </>
                ) : null}
              </p>
            ) : null}
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
              投递截止：{String(detail.meta["投递截止"] || "未知")}
              {detail.days_left != null
                ? detail.days_left >= 0
                  ? `（剩 ${detail.days_left} 天）`
                  : `（已过 ${-detail.days_left} 天）`
                : ""}
            </p>
            <h3>岗位 JD</h3>
            <div className="jd">
              {String(detail.meta["岗位简介"] || "")}
              {"\n\n"}
              {detail.body || ""}
            </div>
            <h3>技能差距</h3>
            <p>
              <strong>要求：</strong>
              {Array.isArray(detail.meta["要求技能"])
                ? (detail.meta["要求技能"] as string[]).join("、")
                : String(detail.meta["要求技能"] || "—")}
            </p>
            <p>
              <strong>已具备：</strong>
              {Array.isArray(detail.meta["已具备"])
                ? (detail.meta["已具备"] as string[]).join("、")
                : String(detail.meta["已具备"] || "—")}
            </p>
            <p>
              <strong>待补齐：</strong>
              {Array.isArray(detail.meta["待补齐"])
                ? (detail.meta["待补齐"] as string[]).join("、")
                : String(detail.meta["待补齐"] || "—")}
            </p>
            {detail.question_bank ? (
              <div className="bank-group">
                <h3>关联题库</h3>
                <p className="sub">{detail.question_bank.stem}</p>
                {(detail.question_bank.groups || []).length ? (
                  <ul>
                    {detail.question_bank.groups.map((g) => (
                      <li key={g.type}>
                        <span className={`pill ${g.type.includes("手撕") ? "green" : "gray"}`}>
                          {g.type}
                        </span>{" "}
                        {g.questions.length} 题
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: "var(--muted)" }}>题库暂无分组</p>
                )}
              </div>
            ) : (
              <p style={{ color: "var(--muted)" }}>暂无公司题库</p>
            )}
            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button
                className="btn"
                disabled={!!detail.followed_by}
                onClick={() => follow(detail.stem)}
              >
                加入投递流程
              </button>
              {detail.meta["投递链接"] ? (
                <a
                  className="btn secondary"
                  href={String(detail.meta["投递链接"])}
                  target="_blank"
                  rel="noreferrer"
                >
                  打开投递页
                </a>
              ) : null}
            </div>
          </aside>
        </>
      ) : null}
    </>
  );
}
