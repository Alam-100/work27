import { pageNumbers } from "../lib/labels";

export function Pager({
  page,
  pages,
  label,
  loading,
  onPage,
}: {
  page: number;
  pages: number;
  label: string;
  loading?: boolean;
  onPage: (next: number) => void;
}) {
  const nums = pageNumbers(page, pages);
  return (
    <div className="pager">
      <span className="pager-info">{label}</span>
      <div className="pager-actions">
        <button
          type="button"
          className="btn sm secondary"
          disabled={page <= 1 || loading}
          onClick={() => onPage(Math.max(1, page - 1))}
        >
          上一页
        </button>
        {nums.map((n, i) =>
          n === "…" ? (
            <span key={`e-${i}`} className="pager-ellipsis">
              …
            </span>
          ) : (
            <button
              key={n}
              type="button"
              className={`btn sm ${n === page ? "" : "secondary"} pager-num`}
              disabled={loading}
              onClick={() => onPage(n)}
            >
              {n}
            </button>
          )
        )}
        <button
          type="button"
          className="btn sm secondary"
          disabled={page >= pages || loading}
          onClick={() => onPage(Math.min(pages, page + 1))}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
