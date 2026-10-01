#!/usr/bin/env python3
"""Copy frontmatter 岗位简介 into Obsidian-visible `## 岗位简介`.

Reading view hides YAML properties, so cards that only stored JD in
frontmatter looked like link-only notes. This keeps original YAML bytes
and only rewrites the markdown body.

Usage:
  py -3.12 qiuzhao/scripts/sync_intel_body_jd.py --dry-run
  py -3.12 qiuzhao/scripts/sync_intel_body_jd.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from vault_io import (  # noqa: E402
    extract_h2_section,
    list_intel,
    replace_note_body,
    sync_intel_job_body_jd,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync intel JD into markdown body")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cards = list_intel()
    missing = 0
    empty_jd = 0
    already = 0
    changed = 0
    samples: list[str] = []

    for card in cards:
        jd = str(card.meta.get("岗位简介") or "").strip()
        if not jd:
            empty_jd += 1
            continue
        existing = extract_h2_section(card.body, "岗位简介")
        new_body, did = sync_intel_job_body_jd(card.body, jd)
        if not did:
            already += 1
            continue
        if existing is None:
            missing += 1
        changed += 1
        if len(samples) < 12:
            samples.append(f"{card.meta.get('公司')} / {card.stem}")
        if not args.dry_run:
            replace_note_body(card.path, new_body)

    print(f"intel_jobs={len(cards)}")
    print(f"empty_frontmatter_jd={empty_jd}")
    print(f"body_already_synced={already}")
    print(f"missing_h2={missing}")
    print(f"changed={changed} dry_run={args.dry_run}")
    for s in samples:
        print("  sample", s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
