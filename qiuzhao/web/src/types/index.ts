export type NoteMeta = Record<string, unknown>;

export interface NoteCard {
  stem: string;
  rel: string;
  meta: NoteMeta;
  body?: string;
}

export type TimeKind = "开始" | "截止" | "安排";

export interface Stage {
  key: string;
  id?: string;
  label: string;
  type?: string;
  field: string | null;
  when: string | null;
  time_kind?: TimeKind | string;
  state: "done" | "active" | "pending" | string;
}

export interface ProcessStage {
  id: string;
  label: string;
  type: string;
  field: string | null;
  when: string | null;
  time_kind?: TimeKind | string;
}

export interface NextEvent {
  when: string;
  label: string;
  field: string;
}

export interface ApplyChannel {
  类型: string;
  名称: string;
  链接: string;
  内推码: string;
  备注: string;
  更新于: string;
}

export interface ProgressItem extends NoteCard {
  current_stage: string | null;
  next_event: NextEvent | null;
  stages: Stage[];
  process?: ProcessStage[];
  phase?: string;
  bucket?: string;
  intel_stem: string | null;
  mianshi_stem: string | null;
  intel?: NoteCard;
  company_tier?: string;
  role_family?: string;
  apply_priority?: string;
  company_overview?: {
    company: string;
    apply_limit: number | null;
    apply_limit_note: string;
    portal: string;
    apply_channels?: ApplyChannel[];
    referral_url?: string;
    referral_code?: string;
    delivery_record_url?: string;
  } | null;
}

export interface ProgressStats {
  applying: number;
  interviewing: number;
  offer: number;
  stopped: number;
  rejected?: number;
  active?: number;
  apply?: number;
  assessment?: number;
  written?: number;
  interview?: number;
  waiting?: number;
  total: number;
}

export interface IntelItem extends NoteCard {
  followed_by: string | null;
  days_left: number | null;
  deadline_bucket: string;
  company_tier?: string;
  role_family?: string;
  hiring_status?: string;
  archived?: boolean;
  apply_priority?: string;
  company_overview?: {
    company: string;
    apply_limit: number | null;
    apply_limit_note: string;
    portal: string;
    apply_channels?: ApplyChannel[];
    referral_url?: string;
    referral_code?: string;
    delivery_record_url?: string;
    followed_count: number;
    over_limit: boolean;
  } | null;
  question_bank?: {
    stem: string;
    rel: string;
    meta: NoteMeta;
    groups: { type: string; questions: { index: number; text: string }[] }[];
  } | null;
}

export interface IntelCompanyGroup {
  company: string;
  tier: string;
  apply_limit: number | null;
  apply_limit_note: string;
  portal: string;
  apply_channels?: ApplyChannel[];
  referral_url?: string;
  referral_code?: string;
  delivery_record_url?: string;
  job_count: number;
  followed_count: number;
  earliest_deadline: number | null;
  max_score: number | null;
  over_limit: boolean;
  jobs: IntelItem[];
}

export interface IntelListResponse {
  items: IntelItem[];
  companies?: IntelCompanyGroup[];
  group?: string;
  page_unit?: "job" | "company";
  total: number;
  total_jobs?: number;
  total_companies?: number;
  page: number;
  page_size: number;
  pages: number;
  sort?: string;
  scope?: "active" | "closed" | "all" | string;
  stats: {
    hiring: number;
    closed?: number;
    followed: number;
    urgent: number;
    tiers?: { 大厂?: number; 中厂?: number; 小厂?: number; 央国企?: number; 外企?: number; other?: number };
  };
}

export interface CalendarEvent {
  when: string;
  when_fmt: string;
  label: string;
  company: string;
  position: string;
  stem: string;
  kind: string;
  source: string;
  field?: string;
}

export type CampusFitLevel = "intel" | "direction" | "normal";

export interface CampusEventItem {
  stem: string;
  rel: string;
  meta: NoteMeta;
  bucket: "today" | "tomorrow" | "week" | "later" | "past" | string;
  intel_linked: boolean;
  fit_level: CampusFitLevel | string;
  session_key: string;
  identity_key?: string;
  company: string;
  title: string;
  event_type: string;
  form: string;
  place: string;
  start: string;
  end: string;
  status: string;
  source: string;
  sources?: string[];
  source_url: string;
  verified_at: string;
  intel_link: string;
}

export interface CampusEventsResponse {
  items: CampusEventItem[];
  total: number;
  stats: {
    total: number;
    today: number;
    tomorrow?: number;
    week: number;
    later: number;
    past: number;
    intel_linked: number;
    fit_intel?: number;
    fit_direction?: number;
    last_verified: string;
  };
  enums: {
    types: string[];
    forms: string[];
    statuses: string[];
    sources: string[];
    buckets: string[];
  };
}

export interface ReviewQuestion {
  text: string;
  answer: string;
  ref: string;
  mastery: string;
  kind?: "面试" | "手撕" | string;
}

export interface CodingChecklistItem {
  text: string;
  sources: string[];
  done: boolean;
}

export interface CodingChecklistGroup {
  topic: string;
  items: CodingChecklistItem[];
}

export interface CodingListResponse {
  stem: string | null;
  rel?: string;
  groups: CodingChecklistGroup[];
  company?: string;
}

export interface ReviewItem extends NoteCard {
  status: string;
  intel_stem: string | null;
  progress_stem: string | null;
  questions?: ReviewQuestion[];
  reflection?: string;
  next_actions?: string;
}

export interface HealthInfo {
  vault: string;
  qiuzhao_ok: boolean;
  progress_count: number;
  intel_count: number;
  study_count: number;
  mianshi_count: number;
  pending_jobs: number;
  messages: string[];
  enums: {
    statuses: string[];
    priorities: string[];
    results: string[];
    plans: string[];
    company_tiers?: string[];
    role_families?: string[];
    hiring_statuses?: string[];
    apply_priorities?: string[];
    study_types: string[];
    study_statuses: string[];
    agent_intents: string[];
    agent_statuses?: string[];
    campus_event_types?: string[];
    campus_event_forms?: string[];
    campus_event_statuses?: string[];
  };
}

export interface AgentJob {
  id: string;
  created_at: string;
  intent: string;
  payload: string;
  status: string;
  result: string;
}
