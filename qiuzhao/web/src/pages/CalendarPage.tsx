import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { CalendarEvent } from "../types";

function startOfMonth(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function addMonths(d: Date, n: number) {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export function CalendarPage() {
  const [cursor, setCursor] = useState(() => startOfMonth(new Date()));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [stats, setStats] = useState({
    month: 0,
    week: 0,
    upcoming: 0,
    completed_this_month: 0,
    conflicts: 0,
  });
  const [conflicts, setConflicts] = useState<
    { a: CalendarEvent & { stem: string }; b: CalendarEvent & { stem: string } }[]
  >([]);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const load = async () => {
    setError("");
    try {
      const start = startOfMonth(cursor);
      const end = addMonths(cursor, 2);
      const fmt = (d: Date) =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
      const [ev, st, cf] = await Promise.all([
        api.calendarEvents(fmt(start), fmt(end)),
        api.calendarStats(),
        api.calendarConflicts(),
      ]);
      setEvents(ev.events);
      setStats(st);
      setConflicts(cf.conflicts as typeof conflicts);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursor]);

  const cells = useMemo(() => {
    const first = startOfMonth(cursor);
    const startWeekday = (first.getDay() + 6) % 7; // Mon=0
    const daysInMonth = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0).getDate();
    const result: { date: Date; inMonth: boolean }[] = [];
    for (let i = 0; i < startWeekday; i++) {
      const d = new Date(first);
      d.setDate(d.getDate() - (startWeekday - i));
      result.push({ date: d, inMonth: false });
    }
    for (let day = 1; day <= daysInMonth; day++) {
      result.push({
        date: new Date(cursor.getFullYear(), cursor.getMonth(), day),
        inMonth: true,
      });
    }
    while (result.length % 7 !== 0) {
      const last = result[result.length - 1].date;
      const d = new Date(last);
      d.setDate(d.getDate() + 1);
      result.push({ date: d, inMonth: false });
    }
    return result;
  }, [cursor]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const e of events) {
      const key = e.when.slice(0, 10);
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(e);
    }
    return map;
  }, [events]);

  const upcoming = useMemo(() => {
    const now = new Date().toISOString();
    return events
      .filter((e) => e.when >= now.slice(0, 16))
      .slice(0, 12);
  }, [events]);

  const monthDeadlines = useMemo(() => {
    const y = cursor.getFullYear();
    const m = cursor.getMonth();
    return events.filter((e) => {
      if (e.kind !== "deadline") return false;
      const d = new Date(e.when.replace(" ", "T"));
      return d.getFullYear() === y && d.getMonth() === m;
    }).length;
  }, [events, cursor]);

  const exportIcs = async () => {
    try {
      const r = await api.exportIcs();
      setMsg(`已导出 ${r.count} 个事件`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const today = new Date();
  const title = `${cursor.getFullYear()} 年 ${cursor.getMonth() + 1} 月`;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>面试日历</h1>
          <div className="sub">把下一场放在眼前，其余按日子排开</div>
        </div>
        <button className="btn secondary" onClick={exportIcs}>
          导出 ICS
        </button>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {msg ? <div className="flash">{msg}</div> : null}

      <div className="stats">
        <div className="stat-card">
          <div className="label">本月面试</div>
          <div className="value">{stats.month} 场</div>
        </div>
        <div className="stat-card">
          <div className="label">本周面试</div>
          <div className="value">{stats.week} 场</div>
        </div>
        <div className="stat-card">
          <div className="label">待进行</div>
          <div className="value">{stats.upcoming} 场</div>
        </div>
        <div className="stat-card">
          <div className="label">冲突</div>
          <div className="value" style={{ color: stats.conflicts ? "var(--danger)" : undefined }}>
            {stats.conflicts}
          </div>
        </div>
        <div className="stat-card">
          <div className="label">本月截止</div>
          <div className="value">{monthDeadlines}</div>
        </div>
      </div>

      {conflicts.length > 0 ? (
        <div className="panel" style={{ borderColor: "#f0b4b4" }}>
          <h2>时间冲突（间隔 ≤ 2 小时）</h2>
          {conflicts.map((c, i) => (
            <div key={i} style={{ marginBottom: 6, fontSize: "0.9rem" }}>
              <Link to={`/applications/${encodeURIComponent(c.a.stem)}`}>
                {c.a.company} {c.a.label}
              </Link>{" "}
              {c.a.when_fmt} ↔{" "}
              <Link to={`/applications/${encodeURIComponent(c.b.stem)}`}>
                {c.b.company} {c.b.label}
              </Link>{" "}
              {c.b.when_fmt}
            </div>
          ))}
        </div>
      ) : null}

      <div className="split">
        <div className="panel">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ margin: 0 }}>{title}</h2>
            <div style={{ display: "flex", gap: 6 }}>
              <button className="btn sm secondary" onClick={() => setCursor(addMonths(cursor, -1))}>
                上月
              </button>
              <button
                className="btn sm secondary"
                onClick={() => setCursor(startOfMonth(new Date()))}
              >
                本月
              </button>
              <button className="btn sm secondary" onClick={() => setCursor(addMonths(cursor, 1))}>
                下月
              </button>
            </div>
          </div>
          <div className="calendar-grid" style={{ marginTop: 12 }}>
            {["一", "二", "三", "四", "五", "六", "日"].map((d) => (
              <div key={d} className="cal-head">
                {d}
              </div>
            ))}
            {cells.map(({ date, inMonth }, idx) => {
              const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
              const dayEvents = eventsByDay.get(key) || [];
              return (
                <div
                  key={idx}
                  className={`cal-cell ${inMonth ? "" : "muted"} ${sameDay(date, today) ? "today" : ""}`}
                >
                  <div className="cal-day">{date.getDate()}</div>
                  {dayEvents.slice(0, 3).map((e, i) => (
                    <Link
                      key={i}
                      className={`cal-event ${
                        e.kind === "deadline" ? "deadline" : e.kind === "campus" ? "campus" : ""
                      }`}
                      to={
                        e.source === "progress"
                          ? `/applications/${encodeURIComponent(e.stem)}`
                          : e.source === "campus"
                            ? `/events`
                            : `/jobs?q=${encodeURIComponent(e.company)}`
                      }
                      title={`${e.company} ${e.label}`}
                    >
                      {e.company.slice(0, 4)}·{e.label}
                    </Link>
                  ))}
                  {dayEvents.length > 3 ? (
                    <div style={{ fontSize: "0.65rem", color: "var(--muted)" }}>
                      +{dayEvents.length - 3}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>

        <div className="panel">
          <h2>近期日程</h2>
          {upcoming.length === 0 ? (
            <div className="empty">近期无排期。在「我的秋招」填写一面/笔试时间。</div>
          ) : (
            upcoming.map((e, i) => (
              <div key={i} className="list-item" style={{ cursor: "default" }}>
                <div className="title">
                  {e.company}
                  {e.position ? ` · ${e.position}` : ""}
                </div>
                <div className="meta">
                  <span
                    className={`pill ${
                      e.kind === "deadline" ? "red" : e.kind === "campus" ? "purple" : "blue"
                    }`}
                  >
                    {e.label}
                  </span>{" "}
                  {e.when_fmt}
                  {e.source === "progress" ? (
                    <>
                      {" · "}
                      <Link to={`/applications/${encodeURIComponent(e.stem)}`}>打开投递</Link>
                    </>
                  ) : e.source === "campus" ? (
                    <>
                      {" · "}
                      <Link to="/events">校园活动</Link>
                    </>
                  ) : (
                    <>
                      {" · "}
                      <Link to={`/jobs?q=${encodeURIComponent(e.company)}`}>打开职位</Link>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
