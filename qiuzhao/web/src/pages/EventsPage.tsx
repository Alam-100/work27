import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { CampusEventItem, CampusFitLevel } from "../types";

type Bucket = "all" | "today" | "tomorrow" | "week" | "later" | "past";

const BUCKET_LABEL: Record<string, string> = {
  all: "全部",
  today: "今天",
  tomorrow: "明天",
  week: "本周",
  later: "更后",
  past: "已结束",
};

const FIT_RANK: Record<string, number> = { intel: 0, direction: 1, normal: 2 };

function statusPill(status: string) {
  if (status === "进行中") return "green";
  if (status === "未开始") return "blue";
  if (status === "已取消") return "red";
  return "gray";
}

function sessionKey(it: CampusEventItem): string {
  if (it.session_key) return it.session_key;
  const start = (it.start || "").trim();
  const place = (it.place || "").trim();
  if (!start || !place) return `singleton|${it.stem}`;
  return `${start}|${place}|${it.event_type || ""}|${it.form || ""}`;
}

function sortByFit(a: CampusEventItem, b: CampusEventItem): number {
  const fa = FIT_RANK[a.fit_level || "normal"] ?? 9;
  const fb = FIT_RANK[b.fit_level || "normal"] ?? 9;
  if (fa !== fb) return fa - fb;
  return (a.company || a.title).localeCompare(b.company || b.title, "zh");
}

type SessionGroup = {
  key: string;
  items: CampusEventItem[];
  start: string;
  end: string;
  place: string;
  event_type: string;
  form: string;
  status: string;
  source: string;
  intelCount: number;
  directionCount: number;
  highlight: CampusEventItem[];
};

function buildSessions(list: CampusEventItem[]): SessionGroup[] {
  const map = new Map<string, CampusEventItem[]>();
  for (const it of list) {
    const k = sessionKey(it);
    const arr = map.get(k) || [];
    arr.push(it);
    map.set(k, arr);
  }
  const sessions: SessionGroup[] = [];
  for (const [key, raw] of map) {
    const items = [...raw].sort(sortByFit);
    const head = items[0];
    const intelCount = items.filter((x) => x.fit_level === "intel").length;
    const directionCount = items.filter((x) => x.fit_level === "direction").length;
    const highlight = items.filter((x) => x.fit_level === "intel" || x.fit_level === "direction");
    sessions.push({
      key,
      items,
      start: head.start || "",
      end: head.end || "",
      place: head.place || "",
      event_type: head.event_type || "",
      form: head.form || "",
      status: head.status || "",
      source: head.source || "",
      intelCount,
      directionCount,
      highlight,
    });
  }
  sessions.sort((a, b) => {
    const sa = a.start || "";
    const sb = b.start || "";
    if (sa !== sb) return sa < sb ? -1 : 1;
    const bestA = Math.min(...a.items.map((x) => FIT_RANK[x.fit_level || "normal"] ?? 9));
    const bestB = Math.min(...b.items.map((x) => FIT_RANK[x.fit_level || "normal"] ?? 9));
    if (bestA !== bestB) return bestA - bestB;
    return 0;
  });
  return sessions;
}

function FitPill({ level }: { level: CampusFitLevel | string }) {
  if (level === "intel") return <span className="pill green">情报库</span>;
  if (level === "direction") return <span className="pill blue">方向相关</span>;
  return null;
}

function CompanyRow({ item }: { item: CampusEventItem }) {
  const name = item.company || item.title;
  const sourceLabel =
    (item.sources && item.sources.length > 0 ? item.sources.join(" · ") : null) ||
    item.source ||
    "";
  return (
    <div className="session-company">
      <span className="session-company-name">{name}</span>
      <FitPill level={item.fit_level} />
      {sourceLabel ? <span className="pill gray">{sourceLabel}</span> : null}
      {item.source_url ? (
        <a href={item.source_url} target="_blank" rel="noreferrer">
          详情
        </a>
      ) : null}
      {item.intel_linked ? (
        <Link to={`/jobs?q=${encodeURIComponent(item.company)}`}>打开职位</Link>
      ) : null}
    </div>
  );
}

function SessionCard({ session }: { session: SessionGroup }) {
  const [open, setOpen] = useState(false);
  const multi = session.items.length > 1;
  const title =
    multi
      ? `${session.event_type || "活动"} · ${session.items.length} 家公司`
      : session.items[0].title || session.items[0].company;

  const endBit = session.end
    ? ` → ${session.end.length >= 16 ? session.end.slice(11, 16) : session.end}`
    : "";

  const sourceLabel =
    session.items.length === 1
      ? (session.items[0].sources && session.items[0].sources.length
          ? session.items[0].sources.join(" · ")
          : session.items[0].source) || session.source
      : Array.from(
          new Set(
            session.items.flatMap((it) =>
              it.sources && it.sources.length ? it.sources : it.source ? [it.source] : [],
            ),
          ),
        ).join(" · ");

  return (
    <div
      className={`list-item session-card${session.intelCount || session.directionCount ? " fit-hot" : ""}`}
      style={{ cursor: "default" }}
    >
      <div className="title">{title}</div>
      <div className="meta">
        <span className={`pill ${statusPill(session.status)}`}>{session.status || "未知"}</span>{" "}
        <span className="pill purple">{session.event_type || "活动"}</span>{" "}
        {session.form ? <span className="pill gray">{session.form}</span> : null}{" "}
        {session.intelCount > 0 ? <span className="pill green">情报库 {session.intelCount}</span> : null}{" "}
        {session.directionCount > 0 ? (
          <span className="pill blue">方向相关 {session.directionCount}</span>
        ) : null}
      </div>
      <div className="meta" style={{ marginTop: 4 }}>
        {session.start || "时间待定"}
        {endBit}
        {session.place ? ` · ${session.place}` : ""}
        {sourceLabel ? ` · ${sourceLabel}` : ""}
      </div>

      {session.highlight.length > 0 ? (
        <div className="session-highlights">
          {session.highlight.map((it) => (
            <span key={it.stem} className={`fit-chip ${it.fit_level}`}>
              {it.company || it.title}
            </span>
          ))}
        </div>
      ) : null}

      {multi ? (
        <>
          <button type="button" className="btn secondary sm session-toggle" onClick={() => setOpen((v) => !v)}>
            {open ? "收起公司" : `展开全部 ${session.items.length} 家`}
          </button>
          {open ? (
            <div className="session-companies">
              {session.items.map((it) => (
                <CompanyRow key={it.stem} item={it} />
              ))}
            </div>
          ) : null}
        </>
      ) : (
        <div className="session-companies" style={{ marginTop: 8 }}>
          <CompanyRow item={session.items[0]} />
        </div>
      )}
    </div>
  );
}

export function EventsPage() {
  const [items, setItems] = useState<CampusEventItem[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    today: 0,
    tomorrow: 0,
    week: 0,
    later: 0,
    past: 0,
    intel_linked: 0,
    fit_intel: 0,
    fit_direction: 0,
    last_verified: "",
  });
  const [enums, setEnums] = useState<{ types: string[]; forms: string[]; statuses: string[] }>({
    types: [],
    forms: [],
    statuses: [],
  });
  const [bucket, setBucket] = useState<Bucket>("tomorrow");
  const [q, setQ] = useState("");
  const [eventType, setEventType] = useState("");
  const [form, setForm] = useState("");
  const [intelOnly, setIntelOnly] = useState(false);
  const [inboxUrl, setInboxUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.listEvents({
        q,
        type: eventType,
        form,
        intel_only: intelOnly || undefined,
      });
      setItems(res.items);
      setStats({
        total: res.stats.total,
        today: res.stats.today,
        tomorrow: res.stats.tomorrow ?? 0,
        week: res.stats.week,
        later: res.stats.later,
        past: res.stats.past,
        intel_linked: res.stats.intel_linked,
        fit_intel: res.stats.fit_intel ?? res.stats.intel_linked,
        fit_direction: res.stats.fit_direction ?? 0,
        last_verified: res.stats.last_verified,
      });
      setEnums({
        types: res.enums.types,
        forms: res.enums.forms,
        statuses: res.enums.statuses,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventType, form, intelOnly]);

  const filtered = useMemo(() => {
    if (bucket === "all") return items;
    return items.filter((it) => it.bucket === bucket);
  }, [items, bucket]);

  const grouped = useMemo(() => {
    const order: Bucket[] = ["today", "tomorrow", "week", "later", "past"];
    if (bucket !== "all") {
      return [{ key: bucket, label: BUCKET_LABEL[bucket], sessions: buildSessions(filtered) }];
    }
    return order
      .map((key) => ({
        key,
        label: BUCKET_LABEL[key],
        sessions: buildSessions(items.filter((it) => it.bucket === key)),
      }))
      .filter((g) => g.sessions.length > 0);
  }, [bucket, filtered, items]);

  const sessionCount = useMemo(
    () => grouped.reduce((n, g) => n + g.sessions.length, 0),
    [grouped],
  );

  const onRefresh = async () => {
    setRefreshing(true);
    setError("");
    setMsg("");
    try {
      const r = await api.refreshEvents();
      setMsg(`已刷新就业网：库内 ${r.count} 场 · 核实于 ${r.verified_at}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRefreshing(false);
    }
  };

  const onInbox = async () => {
    setError("");
    setMsg("");
    try {
      const r = await api.inboxEvent(inboxUrl.trim());
      setMsg(r.message);
      setInboxUrl("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>校园活动</h1>
          <div className="sub">西电宣讲会 / 双选会 · 同场合并 · 对口公司置顶强调</div>
        </div>
        <button className="btn" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? "刷新中…" : "立即刷新"}
        </button>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="flash">{msg}</div> : null}

      <div className="stats">
        <div className="stat-card">
          <div className="label">今天</div>
          <div className="value">{stats.today}</div>
        </div>
        <div className="stat-card">
          <div className="label">明天</div>
          <div className="value">{stats.tomorrow}</div>
        </div>
        <div className="stat-card">
          <div className="label">本周</div>
          <div className="value">{stats.week}</div>
        </div>
        <div className="stat-card">
          <div className="label">更后</div>
          <div className="value">{stats.later}</div>
        </div>
        <div className="stat-card">
          <div className="label">情报库命中</div>
          <div className="value">{stats.fit_intel || stats.intel_linked}</div>
        </div>
        <div className="stat-card">
          <div className="label">方向相关</div>
          <div className="value">{stats.fit_direction}</div>
        </div>
        <div className="stat-card">
          <div className="label">上次核实</div>
          <div className="value" style={{ fontSize: "1rem" }}>
            {stats.last_verified || "—"}
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="toolbar" style={{ flexWrap: "wrap", gap: 8 }}>
          {(Object.keys(BUCKET_LABEL) as Bucket[]).map((b) => (
            <button
              key={b}
              className={`pill-btn ${bucket === b ? "active" : ""}`}
              onClick={() => setBucket(b)}
            >
              {BUCKET_LABEL[b]}
              {b !== "all" ? ` ${stats[b as keyof typeof stats] ?? ""}` : ` ${stats.total}`}
            </button>
          ))}
        </div>
        <div className="toolbar" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <div className="field">
            <label>搜索</label>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") load();
              }}
              placeholder="公司 / 地点"
            />
          </div>
          <div className="field">
            <label>类型</label>
            <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
              <option value="">全部</option>
              {enums.types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>形式</label>
            <select value={form} onChange={(e) => setForm(e.target.value)}>
              <option value="">全部</option>
              {enums.forms.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <input
              type="checkbox"
              checked={intelOnly}
              onChange={(e) => setIntelOnly(e.target.checked)}
            />
            只看情报库公司
          </label>
          <button className="btn secondary sm" onClick={load}>
            筛选
          </button>
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <h2>
            场次列表 {loading ? "…" : `(${sessionCount} 场 / ${filtered.length} 条)`}
          </h2>
          {loading ? (
            <div className="empty">加载中…</div>
          ) : grouped.length === 0 ? (
            <div className="empty">
              暂无场次。点「立即刷新」拉取西电就业网，或右侧补录公众号周报。
            </div>
          ) : (
            grouped.map((g) => (
              <div key={g.key} style={{ marginBottom: 16 }}>
                {bucket === "all" ? <h3 style={{ margin: "8px 0" }}>{g.label}</h3> : null}
                {g.sessions.map((s) => (
                  <SessionCard key={s.key} session={s} />
                ))}
              </div>
            ))
          )}
        </div>

        <div className="panel">
          <h2>公众号补录</h2>
          <p className="meta" style={{ lineHeight: 1.5 }}>
            微信公众号周报常有验证墙或表格截图，无法稳定自动抓取。把
            <code> mp.weixin.qq.com </code>
            链接贴到下面入队；或把截图放到
            <code> 秋招/03_面经/_inbox_images/宣讲会/ </code>
            （或 <code>04_情报/_inbox_images/宣讲会/</code>），然后在 Cursor 说「处理控制台任务」。
          </p>
          <div className="field">
            <label>公众号链接</label>
            <input
              value={inboxUrl}
              onChange={(e) => setInboxUrl(e.target.value)}
              placeholder="https://mp.weixin.qq.com/s/..."
            />
          </div>
          <button className="btn secondary" onClick={onInbox} disabled={!inboxUrl.trim()}>
            入队补录
          </button>
          <div className="meta" style={{ marginTop: 12 }}>
            权威源：{" "}
            <a href="https://job.xidian.edu.cn/teachin/index" target="_blank" rel="noreferrer">
              宣讲会
            </a>
            {" · "}
            <a href="https://job.xidian.edu.cn/jobfair" target="_blank" rel="noreferrer">
              招聘会
            </a>
            {" · "}
            <Link to="/calendar">面试日历</Link>
            （已叠加校园活动）
          </div>
        </div>
      </div>
    </>
  );
}
