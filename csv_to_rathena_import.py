#!/usr/bin/env python3
"""Convert translated CSV into rAthena import YAML.

Expected CSV columns:
  id,kind,name_kr,source_url,status
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate rAthena import YAML from KR CSV")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--kind", choices=["mob", "item"], required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--only-ok", action="store_true", default=False)
    return p.parse_args()


def yaml_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    args = parse_args()

    rows = []
    with args.csv.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if row.get("kind") != args.kind:
                continue
            name_kr = (row.get("name_kr") or "").strip()
            if not name_kr:
                continue
            if args.only_ok and row.get("status") != "ok":
                continue
            try:
                id_ = int((row.get("id") or "").strip())
            except ValueError:
                continue
            rows.append((id_, name_kr))

    rows.sort(key=lambda x: x[0])

    header_type = "MOB_DB" if args.kind == "mob" else "ITEM_DB"
    body_lines = [
        "Header:",
        f"  Type: {header_type}",
        "  Version: 1",
        "Body:",
    ]

    for id_, name_kr in rows:
        body_lines.append(f"  - Id: {id_}")
        body_lines.append(f"    Name: \"{yaml_escape(name_kr)}\"")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(body_lines) + "\n", encoding="utf-8")

    print(f"[done] wrote {len(rows)} entries -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
