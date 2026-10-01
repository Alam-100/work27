import { formatStageWhen } from "../lib/stageTime";
import type { Stage } from "../types";

export function ProcessStepper({
  stages,
  selectedKey,
  onSelect,
  compact,
}: {
  stages: Stage[];
  selectedKey?: string | null;
  onSelect?: (stage: Stage) => void;
  compact?: boolean;
}) {
  return (
    <div className={`stepper ${compact ? "compact" : ""}`}>
      {stages.map((s) => {
        const key = s.id || s.key;
        const selected = selectedKey && selectedKey === key;
        const whenText = formatStageWhen(s);
        return (
          <div
            key={key}
            className={`step ${s.state}${selected ? " selected" : ""}`}
            onClick={() => onSelect?.(s)}
            role={onSelect ? "button" : undefined}
            title={whenText !== "待安排" ? whenText : s.label}
          >
            <div className="dot">
              {s.state === "done" ? "✓" : s.state === "active" ? "●" : ""}
            </div>
            {!compact ? (
              <>
                <div className="lbl">{s.label}</div>
                <div className="when">{whenText}</div>
              </>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
