/** Convert vault datetime (`YYYY-MM-DD HH:mm` / `YYYY-MM-DD`) ↔ datetime-local. */

import { useEffect, useRef, useState } from "react";

export function toLocalInputValue(vault: string | null | undefined): string {
  if (!vault) return "";
  const s = String(vault).trim();
  if (!s) return "";
  // Already local-ish: 2026-08-02T10:00 or with seconds
  const iso = s.replace(" ", "T");
  const m = iso.match(/^(\d{4}-\d{2}-\d{2})(?:T(\d{2}):(\d{2}))?/);
  if (!m) return "";
  const date = m[1];
  const hh = m[2] ?? "00";
  const mm = m[3] ?? "00";
  return `${date}T${hh}:${mm}`;
}

export function fromLocalInputValue(local: string): string | null {
  const s = (local || "").trim();
  if (!s) return null;
  const m = s.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/);
  if (!m) return null;
  return `${m[1]} ${m[2]}:${m[3]}`;
}

export function DateTimeField({
  value,
  onChange,
  onCommit,
  disabled,
  id,
}: {
  value: string | null | undefined;
  onChange?: (vault: string | null) => void;
  /** Fired when user leaves the control or picks a value (for autosave). */
  onCommit?: (vault: string | null) => void;
  disabled?: boolean;
  id?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [local, setLocal] = useState(() => toLocalInputValue(value));

  useEffect(() => {
    setLocal(toLocalInputValue(value));
  }, [value]);

  const applyLocal = (nextLocal: string, commit: boolean) => {
    setLocal(nextLocal);
    const vault = fromLocalInputValue(nextLocal);
    onChange?.(vault);
    if (commit) onCommit?.(vault);
  };

  const openPicker = () => {
    const el = inputRef.current;
    if (!el || disabled) return;
    try {
      // Chromium / modern Edge: open native picker even if click lands on text area
      (el as HTMLInputElement & { showPicker?: () => void }).showPicker?.();
    } catch {
      /* ignore — older browsers */
    }
  };

  return (
    <div className="datetime-field">
      <input
        ref={inputRef}
        id={id}
        type="datetime-local"
        value={local}
        disabled={disabled}
        onClick={openPicker}
        onChange={(e) => {
          // Commit on pick so detail side-panel autosaves without needing blur
          applyLocal(e.target.value, true);
        }}
        onBlur={(e) => {
          const vault = fromLocalInputValue(e.target.value);
          onCommit?.(vault);
        }}
      />
      <button
        type="button"
        className="btn sm secondary datetime-clear"
        disabled={disabled || !local}
        title="清空时间"
        onClick={() => {
          setLocal("");
          onChange?.(null);
          onCommit?.(null);
        }}
      >
        清空
      </button>
    </div>
  );
}
