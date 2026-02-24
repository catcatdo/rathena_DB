#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FETCH="$ROOT_DIR/fetch_ragnaplace_kr.py"
CONVERT="$ROOT_DIR/csv_to_rathena_import.py"
OUT_DIR="$ROOT_DIR/out"

if [[ $# -lt 1 ]]; then
  echo "Usage: ./run_mac.sh /ABS/PATH/TO/rathena/db [delay_seconds]"
  exit 1
fi

RATHENA_DB="$1"
DELAY="${2:-0.8}"

if [[ ! -d "$RATHENA_DB" ]]; then
  echo "[fatal] rAthena db path not found: $RATHENA_DB"
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[fatal] python3 not found"
  exit 2
fi

mkdir -p "$OUT_DIR"

echo "[step] Fetch mob KR names"
python3 "$FETCH" --type mob --rathena-db "$RATHENA_DB" --out "$OUT_DIR/mob_kr.csv" --delay "$DELAY"

echo "[step] Fetch item KR names"
python3 "$FETCH" --type item --rathena-db "$RATHENA_DB" --out "$OUT_DIR/item_kr.csv" --delay "$DELAY"

echo "[step] Build import YAML"
python3 "$CONVERT" --csv "$OUT_DIR/mob_kr.csv" --kind mob --out "$OUT_DIR/mob_db_kr.yml" --only-ok
python3 "$CONVERT" --csv "$OUT_DIR/item_kr.csv" --kind item --out "$OUT_DIR/item_db_kr.yml" --only-ok

echo "[done] Generated files:"
ls -1 "$OUT_DIR"
