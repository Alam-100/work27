async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || JSON.stringify(j);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: (light = true) =>
    request<import("../types").HealthInfo>(`/api/health?light=${light ? "true" : "false"}`),
  enums: () =>
    request<{ enums: import("../types").HealthInfo["enums"] }>("/api/enums"),
  profile: () => request<{ summary: Record<string, string> }>("/api/profile"),

  listIntel: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    return request<import("../types").IntelListResponse>(`/api/intel?${q}`);
  },
  getIntel: (stem: string) =>
    request<import("../types").IntelItem>(`/api/intel/${encodeURIComponent(stem)}`),
  followIntel: (stem: string) =>
    request<{
      ok: boolean;
      progress_stem: string;
      apply_limit_warning?: string | null;
      apply_limit?: number | null;
      followed_before?: number;
    }>(`/api/intel/${encodeURIComponent(stem)}/follow`, { method: "POST" }),
  verifyIntel: (stem: string) =>
    request<{ ok: boolean; job_id: string; message: string }>(
      `/api/intel/${encodeURIComponent(stem)}/verify`,
      { method: "POST" }
    ),
  patchIntel: (stem: string, updates: Record<string, unknown>) =>
    request<import("../types").IntelItem>(`/api/intel/${encodeURIComponent(stem)}`, {
      method: "PATCH",
      body: JSON.stringify({ updates }),
    }),

  listProgress: (tab = "all") =>
    request<{ items: import("../types").ProgressItem[]; total: number }>(
      `/api/progress?tab=${encodeURIComponent(tab)}`
    ),
  progressStats: () =>
    request<import("../types").ProgressStats>("/api/progress/stats"),
  getProgress: (stem: string) =>
    request<import("../types").ProgressItem>(
      `/api/progress/${encodeURIComponent(stem)}`
    ),
  patchProgress: (stem: string, updates: Record<string, unknown>) =>
    request<import("../types").ProgressItem>(
      `/api/progress/${encodeURIComponent(stem)}`,
      { method: "PATCH", body: JSON.stringify({ updates }) }
    ),
  putProcess: (stem: string, stages: import("../types").ProcessStage[]) =>
    request<import("../types").ProgressItem>(
      `/api/progress/${encodeURIComponent(stem)}/process`,
      { method: "PUT", body: JSON.stringify({ stages }) }
    ),
  createProgress: (body: {
    company: string;
    position: string;
    plan?: string;
    base?: string;
    link?: string;
    priority?: string;
  }) =>
    request<import("../types").ProgressItem>("/api/progress", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteProgress: (stem: string) =>
    request<{ ok: boolean; archived_to: string }>(
      `/api/progress/${encodeURIComponent(stem)}`,
      { method: "DELETE" }
    ),

  calendarEvents: (start?: string, end?: string) => {
    const q = new URLSearchParams();
    if (start) q.set("start", start);
    if (end) q.set("end", end);
    return request<{ events: import("../types").CalendarEvent[]; total: number }>(
      `/api/calendar/events?${q}`
    );
  },
  calendarConflicts: () =>
    request<{ conflicts: unknown[]; total: number }>("/api/calendar/conflicts"),
  calendarStats: () =>
    request<{
      month: number;
      week: number;
      upcoming: number;
      completed_this_month: number;
      conflicts: number;
    }>("/api/calendar/stats"),
  exportIcs: () =>
    request<{ ok: boolean; count: number; path: string }>(
      "/api/calendar/export-ics",
      { method: "POST" }
    ),

  listEvents: (params: Record<string, string | boolean | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v === undefined || v === "") return;
      q.set(k, String(v));
    });
    return request<import("../types").CampusEventsResponse>(`/api/events?${q}`);
  },
  refreshEvents: () =>
    request<{ ok: boolean; count: number; summary: string; verified_at: string }>(
      "/api/events/refresh",
      { method: "POST" }
    ),
  inboxEvent: (url: string, note = "") =>
    request<{ ok: boolean; message: string; job: import("../types").AgentJob }>(
      "/api/events/inbox",
      { method: "POST", body: JSON.stringify({ url, note }) }
    ),

  listReviews: (q = "") =>
    request<{ items: import("../types").ReviewItem[]; total: number }>(
      `/api/review?q=${encodeURIComponent(q)}`
    ),
  getReview: (stem: string) =>
    request<import("../types").ReviewItem>(
      `/api/review/${encodeURIComponent(stem)}`
    ),
  getReviewBank: (stem: string) =>
    request<{
      stem: string | null;
      groups: { type: string; questions: { index: number; text: string }[] }[];
    }>(`/api/review/${encodeURIComponent(stem)}/bank`),
  getCodingList: (company = "") => {
    const q = new URLSearchParams();
    if (company) q.set("company", company);
    const suffix = q.toString() ? `?${q}` : "";
    return request<import("../types").CodingListResponse>(`/api/review/coding-list${suffix}`);
  },
  patchReview: (
    stem: string,
    payload: {
      questions?: import("../types").ReviewQuestion[];
      reflection?: string;
      next_actions?: string;
      body?: string;
    }
  ) =>
    request<import("../types").ReviewItem>(
      `/api/review/${encodeURIComponent(stem)}`,
      { method: "PATCH", body: JSON.stringify(payload) }
    ),

  listAgentJobs: () =>
    request<{ items: import("../types").AgentJob[]; pending: number }>(
      "/api/agent/jobs"
    ),
  createAgentJob: (intent: string, payload = "") =>
    request<{ ok: boolean }>("/api/agent/jobs", {
      method: "POST",
      body: JSON.stringify({ intent, payload }),
    }),
  listStudy: () =>
    request<{
      open: import("../types").NoteCard[];
      done: import("../types").NoteCard[];
    }>("/api/agent/study"),
  createStudy: (body: {
    title: string;
    study_type: string;
    company?: string;
    due?: string;
    note?: string;
  }) =>
    request<{ ok: boolean }>("/api/agent/study", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchStudy: (stem: string, status: string) =>
    request<{ ok: boolean }>(`/api/agent/study/${encodeURIComponent(stem)}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};
