# rAthena Korean DB Fetcher (macOS)

`rAthena` DB ID 목록을 기준으로 `RagnaPlace(kRO)`에서 한글명을 수집하고 CSV/YAML로 변환합니다.

## Quick Start on Mac

```bash
git clone https://github.com/catcatdo/rathena_DB.git
cd rathena_DB
./run_mac.sh /ABS/PATH/TO/rathena/db
```

생성 결과:
- `out/mob_kr.csv`
- `out/item_kr.csv`
- `out/mob_db_kr.yml`
- `out/item_db_kr.yml`

## rAthena 적용

```bash
cp out/mob_db_kr.yml /ABS/PATH/TO/rathena/db/import/
cp out/item_db_kr.yml /ABS/PATH/TO/rathena/db/import/
```

서버 재시작 후 반영됩니다.

## Manual Commands

```bash
python3 fetch_ragnaplace_kr.py --type mob --rathena-db /ABS/PATH/TO/rathena/db --out out/mob_kr.csv
python3 fetch_ragnaplace_kr.py --type item --rathena-db /ABS/PATH/TO/rathena/db --out out/item_kr.csv
python3 csv_to_rathena_import.py --csv out/mob_kr.csv --kind mob --out out/mob_db_kr.yml --only-ok
python3 csv_to_rathena_import.py --csv out/item_kr.csv --kind item --out out/item_db_kr.yml --only-ok
```

옵션:
- `--delay 0.8`: 요청 간 딜레이(서버 부하 방지)
- `--start-at 10000`: 특정 ID부터 재개
- `--limit 500`: 테스트용 일부만 처리
- `--id-range 1001-2000`: rAthena DB 없이 범위 지정

## 검증

```bash
make sample
```

## 주의

- 사이트 정책/robots/약관을 준수하세요.
- 너무 짧은 딜레이로 대량 요청하지 마세요.
