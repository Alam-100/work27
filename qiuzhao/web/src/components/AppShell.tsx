import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { api } from "../api/client";

const TABS = [
  { to: "/jobs", label: "职位信息" },
  { to: "/applications", label: "我的秋招" },
  { to: "/events", label: "校园活动" },
  { to: "/calendar", label: "面试日历" },
  { to: "/review", label: "面试复盘" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const [pending, setPending] = useState(0);

  useEffect(() => {
    api.health().then((h) => setPending(h.pending_jobs)).catch(() => undefined);
  }, []);

  return (
    <div className="app-shell">
      <header className="topnav">
        <Link to="/jobs" className="brand">
          <span className="brand-mark" />
          秋招控制台
        </Link>
        <nav className="nav-tabs">
          {TABS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              {t.label}
            </NavLink>
          ))}
          <NavLink to="/more" className={({ isActive }) => (isActive ? "active" : undefined)}>
            更多{pending ? ` (${pending})` : ""}
          </NavLink>
        </nav>
        <div className="nav-right">
          <a href="/legacy" title="旧版 Jinja 控制台">
            旧版
          </a>
          <span>Obsidian 真相源</span>
        </div>
      </header>
      <main className="page">{children}</main>
    </div>
  );
}
