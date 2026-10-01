/** Personal mailbox jump helpers for 我的秋招. Stored in localStorage. */

export type MailboxProvider = "gmail" | "qq" | "outlook" | "163" | "custom";

export interface MailboxConfig {
  provider: MailboxProvider;
  /** Inbox / home URL opened by the primary button. */
  inboxUrl: string;
}

const STORAGE_KEY = "qiuzhao.mailbox.v1";

export const MAILBOX_PRESETS: Record<
  Exclude<MailboxProvider, "custom">,
  { label: string; inboxUrl: string }
> = {
  gmail: {
    label: "Gmail",
    inboxUrl: "https://mail.google.com/mail/u/0/#inbox",
  },
  qq: {
    label: "QQ 邮箱",
    inboxUrl: "https://wx.mail.qq.com/",
  },
  outlook: {
    label: "Outlook",
    inboxUrl: "https://outlook.live.com/mail/0/",
  },
  "163": {
    label: "163 邮箱",
    inboxUrl: "https://mail.163.com/",
  },
};

export const DEFAULT_MAILBOX: MailboxConfig = {
  provider: "gmail",
  inboxUrl: MAILBOX_PRESETS.gmail.inboxUrl,
};

export function loadMailboxConfig(): MailboxConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_MAILBOX };
    const parsed = JSON.parse(raw) as Partial<MailboxConfig>;
    const provider = (parsed.provider || "gmail") as MailboxProvider;
    if (provider !== "custom" && MAILBOX_PRESETS[provider]) {
      return {
        provider,
        inboxUrl: String(parsed.inboxUrl || MAILBOX_PRESETS[provider].inboxUrl).trim()
          || MAILBOX_PRESETS[provider].inboxUrl,
      };
    }
    const url = String(parsed.inboxUrl || "").trim();
    if (!url) return { ...DEFAULT_MAILBOX };
    return { provider: "custom", inboxUrl: url };
  } catch {
    return { ...DEFAULT_MAILBOX };
  }
}

export function saveMailboxConfig(cfg: MailboxConfig): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
}

/** Deep-link search when the provider supports it; otherwise null. */
export function companyMailSearchUrl(
  cfg: MailboxConfig,
  company: string,
): string | null {
  const q = company.trim();
  if (!q) return null;
  if (cfg.provider === "gmail" || cfg.inboxUrl.includes("mail.google.com")) {
    return `https://mail.google.com/mail/u/0/#search/${encodeURIComponent(q)}`;
  }
  if (cfg.provider === "outlook" || cfg.inboxUrl.includes("outlook.")) {
    return `https://outlook.live.com/mail/0/search/results/${encodeURIComponent(q)}`;
  }
  return null;
}

export function providerLabel(cfg: MailboxConfig): string {
  if (cfg.provider === "custom") return "自定义邮箱";
  return MAILBOX_PRESETS[cfg.provider]?.label || "邮箱";
}
