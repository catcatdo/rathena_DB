#!/usr/bin/env python3
"""Fetch Korean names for rAthena IDs from RagnaPlace and export CSV.

Usage examples:
  python3 fetch_ragnaplace_kr.py --type mob --rathena-db /path/to/rathena/db --out mob_kr.csv
  python3 fetch_ragnaplace_kr.py --type item --rathena-db /path/to/rathena/db --out item_kr.csv
  python3 fetch_ragnaplace_kr.py --type mob --id-range 1001-1100 --out mob_kr.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://ragnaplace.com/ko/kro"
HANGUL_RE = re.compile(r"[가-힣]")
ID_RE = re.compile(r"^\s*Id:\s*(\d+)\s*$")
NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    flags=re.DOTALL | re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch KR names from RagnaPlace")
    p.add_argument("--type", choices=["mob", "item"], required=True)
    p.add_argument("--out", default=None, help="Output CSV path")
    p.add_argument("--rathena-db", type=Path, default=None, help="Path to rAthena db directory")
    p.add_argument("--id-range", default=None, help="Range like 1001-1100")
    p.add_argument("--delay", type=float, default=0.8, help="Delay between requests in seconds")
    p.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--start-at", type=int, default=None, help="Skip IDs lower than this")
    p.add_argument("--limit", type=int, default=None, help="Process first N IDs only")
    return p.parse_args()


def collect_ids_from_rathena(db_root: Path, kind: str) -> list[int]:
    if not db_root.exists():
        raise FileNotFoundError(f"DB path not found: {db_root}")

    if kind == "mob":
        patterns = ["**/mob_db*.yml"]
    else:
        patterns = ["**/item_db*.yml"]

    ids: set[int] = set()
    for pattern in patterns:
        for fp in db_root.glob(pattern):
            if not fp.is_file():
                continue
            try:
                for line in fp.read_text(encoding="utf-8", errors="ignore").splitlines():
                    m = ID_RE.match(line)
                    if m:
                        ids.add(int(m.group(1)))
            except OSError:
                continue

    return sorted(ids)


def parse_range(text: str) -> list[int]:
    m = re.fullmatch(r"(\d+)-(\d+)", text.strip())
    if not m:
        raise ValueError("--id-range must look like 1001-1100")
    a, b = int(m.group(1)), int(m.group(2))
    if a > b:
        a, b = b, a
    return list(range(a, b + 1))


def walk_strings(node, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, path + (str(k),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, path + (str(i),))
    elif isinstance(node, str):
        yield path, node


def score_candidate(path: tuple[str, ...], value: str) -> int:
    p = ".".join(path).lower()
    last = path[-1].lower() if path else ""
    score = 0
    if "name" in last:
        score += 10
    if "name" in p:
        score += 4
    if any(token in p for token in ["korean", "korea", "ko", "kor"]):
        score += 8
    if "title" in p:
        score += 2
    if len(value) > 60:
        score -= 6
    elif len(value) > 30:
        score -= 3
    if value.count(" ") > 2:
        score -= 2
    return score


def pick_korean_name(next_data: dict) -> str | None:
    candidates: list[tuple[int, str]] = []
    for path, value in walk_strings(next_data):
        if not HANGUL_RE.search(value):
            continue
        value = value.strip()
        if not value:
            continue
        score = score_candidate(path, value)
        candidates.append((score, value))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], -len(x[1])), reverse=True)
    return candidates[0][1]


def fetch_html(url: str, timeout: float, max_retries: int) -> tuple[str | None, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; rathena-kr-data/1.0)",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
    }
    for attempt in range(1, max_retries + 1):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout) as resp:
                code = getattr(resp, "status", 200)
                if code >= 400:
                    return None, f"http_{code}"
                body = resp.read().decode("utf-8", errors="ignore")
                return body, "ok"
        except HTTPError as e:
            if e.code == 404:
                return None, "not_found"
            if attempt == max_retries:
                return None, f"http_{e.code}"
        except URLError:
            if attempt == max_retries:
                return None, "url_error"
        except TimeoutError:
            if attempt == max_retries:
                return None, "timeout"
        except Exception:
            if attempt == max_retries:
                return None, "error"
        time.sleep(0.5 * attempt)
    return None, "error"


def extract_next_data(html: str) -> dict | None:
    m = NEXT_DATA_RE.search(html)
    if not m:
        return None
    raw = m.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def build_ids(args: argparse.Namespace) -> list[int]:
    if args.rathena_db is None and args.id_range is None:
        raise ValueError("Provide --rathena-db or --id-range")

    ids: list[int] = []
    if args.rathena_db is not None:
        ids.extend(collect_ids_from_rathena(args.rathena_db, args.type))
    if args.id_range is not None:
        ids.extend(parse_range(args.id_range))

    ids = sorted(set(ids))
    if args.start_at is not None:
        ids = [x for x in ids if x >= args.start_at]
    if args.limit is not None:
        ids = ids[: args.limit]
    return ids


def main() -> int:
    args = parse_args()
    out = Path(args.out or f"{args.type}_kr_from_ragnaplace.csv")

    try:
        ids = build_ids(args)
    except Exception as e:
        print(f"[fatal] {e}", file=sys.stderr)
        return 2

    if not ids:
        print("[fatal] no IDs found", file=sys.stderr)
        return 2

    print(f"[info] type={args.type}, ids={len(ids)}, out={out}")

    rows = []
    ok_count = 0
    for i, id_ in enumerate(ids, 1):
        url = f"{BASE}/{args.type}/{id_}"
        html, status = fetch_html(url, timeout=args.timeout, max_retries=args.max_retries)
        name_kr = ""

        if status == "ok" and html:
            next_data = extract_next_data(html)
            if next_data is not None:
                picked = pick_korean_name(next_data)
                if picked:
                    name_kr = picked
                    ok_count += 1
                else:
                    status = "no_kr_found"
            else:
                status = "no_next_data"

        rows.append(
            {
                "id": id_,
                "kind": args.type,
                "name_kr": name_kr,
                "source_url": url,
                "status": status,
            }
        )

        if i % 50 == 0 or i == len(ids):
            print(f"[progress] {i}/{len(ids)} (ok={ok_count})")
        time.sleep(args.delay)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "kind", "name_kr", "source_url", "status"])
        w.writeheader()
        w.writerows(rows)

    print(f"[done] wrote {len(rows)} rows, translated={ok_count}, file={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
