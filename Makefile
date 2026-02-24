PY=python3
OUT=out

.PHONY: help sample yaml clean

help:
	@echo "Usage:"
	@echo "  make sample          # quick network test"
	@echo "  make yaml            # build YAML from existing CSV"
	@echo "  ./run_mac.sh /ABS/PATH/TO/rathena/db [delay]"

sample:
	$(PY) fetch_ragnaplace_kr.py --type mob --id-range 1001-1010 --out $(OUT)/sample_mob.csv --delay 0.2

yaml:
	$(PY) csv_to_rathena_import.py --csv $(OUT)/mob_kr.csv --kind mob --out $(OUT)/mob_db_kr.yml --only-ok
	$(PY) csv_to_rathena_import.py --csv $(OUT)/item_kr.csv --kind item --out $(OUT)/item_db_kr.yml --only-ok

clean:
	rm -rf __pycache__ $(OUT)
