.PHONY: install install-dev lint test test-ci test-quality test-silver test-spark test-iceberg infra-up infra-down upload-sample spark-job iceberg-job query-iceberg worker clean-storage demo-reset demo-prepare demo-run-spark demo-run-iceberg demo-query-iceberg demo-test-quality demo-full

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest tests

test-ci:
	pytest tests/services tests/plugin -q

test-quality:
	pytest tests/quality

test-silver:
	pytest tests/quality -m silver

test-spark:
	pytest tests/spark -q

test-iceberg:
	pytest tests/iceberg -q

infra-up:
	docker compose up -d

infra-down:
	docker compose down

upload-sample:
	python scripts/upload_sample_data.py

spark-job:
	python scripts/run_orders_spark_job.py

iceberg-job:
	python scripts/run_orders_iceberg_job.py

query-iceberg:
	python scripts/query_orders_iceberg_table.py

worker:
	python scripts/run_quality_worker.py --once

clean-storage:
	python scripts/clean_lakehouse_storage.py

demo-reset:
	python scripts/clean_lakehouse_storage.py --demo-reset

demo-prepare:
	python scripts/upload_sample_data.py

demo-run-spark:
	python scripts/run_orders_spark_job.py --run-id demo_spark

demo-run-iceberg:
	python scripts/run_orders_iceberg_job.py --run-id demo_iceberg

demo-query-iceberg:
	python scripts/query_orders_iceberg_table.py

demo-test-quality:
	pytest tests/quality --run-id=demo_quality

demo-full:
	make infra-up
	make demo-reset
	make demo-prepare
	make demo-run-spark
	make demo-run-iceberg
	make demo-query-iceberg
	make demo-test-quality