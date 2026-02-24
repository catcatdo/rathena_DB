# rAthena Korean DB Fetcher

`rAthena` DB ID 목록을 기준으로 `RagnaPlace(kRO)`에서 한글명을 수집하고 CSV/YAML로 변환합니다.

## 1) 몹/아이템 한글명 수집

```bash
cd /Users/wabisabi/MyGitHub/rathena-kr-data
python3 fetch_ragnaplace_kr.py --type mob --rathena-db /ABS/PATH/TO/rathena/db --out out/mob_kr.csv
python3 fetch_ragnaplace_kr.py --type item --rathena-db /ABS/PATH/TO/rathena/db --out out/item_kr.csv
```

옵션:
- `--delay 0.8`: 요청 간 딜레이(서버 부하 방지)
- `--start-at 10000`: 특정 ID부터 재개
- `--limit 500`: 테스트용 일부만 처리
- `--id-range 1001-2000`: rAthena DB 없이 범위 지정

출력 CSV 컬럼:
- `id,kind,name_kr,source_url,status`

## 2) rAthena import YAML 생성

```bash
python3 csv_to_rathena_import.py --csv out/mob_kr.csv --kind mob --out out/mob_db_kr.yml --only-ok
python3 csv_to_rathena_import.py --csv out/item_kr.csv --kind item --out out/item_db_kr.yml --only-ok
```

## 3) rAthena 적용

생성된 파일을 rAthena import 경로에 복사:

```bash
cp out/mob_db_kr.yml /ABS/PATH/TO/rathena/db/import/
cp out/item_db_kr.yml /ABS/PATH/TO/rathena/db/import/
```

이후 서버 재시작.

## 커버리지 팁

- 1차: `mob + item` 수집
- 2차: 누락(`status != ok`)만 재시도
- 3차: 스킬/맵은 별도 소스(클라이언트 Lua/공식 가이드) 병합 권장

## 주의

- 사이트 정책/robots/약관을 준수하세요.
- 너무 짧은 딜레이로 대량 요청하지 마세요.
