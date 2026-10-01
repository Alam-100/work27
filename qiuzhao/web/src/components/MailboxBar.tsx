import { useEffect, useState } from "react";
import {
  MAILBOX_PRESETS,
  companyMailSearchUrl,
  loadMailboxConfig,
  providerLabel,
  saveMailboxConfig,
  type MailboxConfig,
  type MailboxProvider,
} from "../lib/mailbox";

type Props = {
  /** When set, show “搜该公司邮件” if the provider supports search. */
  company?: string;
  compact?: boolean;
};

export function MailboxBar({ company, compact }: Props) {
  const [cfg, setCfg] = useState<MailboxConfig>(() => loadMailboxConfig());
  const [open, setOpen] = useState(false);
  const [draftProvider, setDraftProvider] = useState<MailboxProvider>(cfg.provider);
  const [draftUrl, setDraftUrl] = useState(cfg.inboxUrl);

  useEffect(() => {
    setCfg(loadMailboxConfig());
  }, []);

  const searchUrl = company ? companyMailSearchUrl(cfg, company) : null;

  const applyPreset = (provider: MailboxProvider) => {
    setDraftProvider(provider);
    if (provider !== "custom" && MAILBOX_PRESETS[provider]) {
      setDraftUrl(MAILBOX_PRESETS[provider].inboxUrl);
    }
  };

  const save = () => {
    const next: MailboxConfig = {
      provider: draftProvider,
      inboxUrl: draftUrl.trim() || cfg.inboxUrl,
    };
    if (next.provider !== "custom" && MAILBOX_PRESETS[next.provider] && !draftUrl.trim()) {
      next.inboxUrl = MAILBOX_PRESETS[next.provider].inboxUrl;
    }
    saveMailboxConfig(next);
    setCfg(next);
    setOpen(false);
  };

  return (
    <div className={compact ? "mailbox-bar compact" : "mailbox-bar"}>
      <div className="mailbox-bar-main">
        <div className="mailbox-bar-copy">
          <div className="mailbox-bar-title">邮箱通知</div>
          {!compact ? (
            <div className="sub">
              测评 / 笔试 / 面试邀约多从邮件来 · 当前 {providerLabel(cfg)}
            </div>
          ) : (
            <div className="sub">{providerLabel(cfg)}</div>
          )}
        </div>
        <div className="mailbox-bar-actions">
          <a
            className="btn sm"
            href={cfg.inboxUrl}
            target="_blank"
            rel="noreferrer"
          >
            打开邮箱
          </a>
          {searchUrl ? (
            <a
              className="btn sm secondary"
              href={searchUrl}
              target="_blank"
              rel="noreferrer"
              title={`在邮箱中搜索「${company}」`}
            >
              搜「{company}」
            </a>
          ) : null}
          <button
            type="button"
            className="btn sm secondary"
            onClick={() => {
              setDraftProvider(cfg.provider);
              setDraftUrl(cfg.inboxUrl);
              setOpen((v) => !v);
            }}
          >
            {open ? "收起" : "设置"}
          </button>
        </div>
      </div>

      {open ? (
        <div className="mailbox-bar-settings">
          <div className="field">
            <label>邮箱服务</label>
            <select
              value={draftProvider}
              onChange={(e) => applyPreset(e.target.value as MailboxProvider)}
            >
              {(Object.keys(MAILBOX_PRESETS) as Exclude<MailboxProvider, "custom">[]).map(
                (k) => (
                  <option key={k} value={k}>
                    {MAILBOX_PRESETS[k].label}
                  </option>
                ),
              )}
              <option value="custom">自定义链接</option>
            </select>
          </div>
          <div className="field grow">
            <label>收件箱地址</label>
            <input
              value={draftUrl}
              placeholder="https://mail.google.com/mail/u/0/#inbox"
              onChange={(e) => {
                setDraftUrl(e.target.value);
                setDraftProvider("custom");
              }}
            />
          </div>
          <button type="button" className="btn sm" onClick={save}>
            保存
          </button>
        </div>
      ) : null}
    </div>
  );
}
