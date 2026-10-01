export function tierPillClass(tier: string): string {
  switch (tier) {
    case "大厂":
      return "pill blue";
    case "中厂":
      return "pill";
    case "小厂":
      return "pill gray";
    case "央国企":
      return "pill green";
    case "外企":
      return "pill purple";
    default:
      return "pill gray";
  }
}

export function pageNumbers(page: number, pages: number): Array<number | "…"> {
  if (pages <= 1) return pages === 1 ? [1] : [];
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);
  const marks = new Set([1, pages, page, page - 1, page + 1, page - 2, page + 2]);
  const sorted = [...marks].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
  const out: Array<number | "…"> = [];
  let prev = 0;
  for (const n of sorted) {
    if (prev && n - prev > 1) out.push("…");
    out.push(n);
    prev = n;
  }
  return out;
}
