.PHONY: install install-dev lint test test-ci test-quality test-silver test-spark test-iceberg infra-up infra-down upload-sample spark-job iceberg-job worker

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

worker:
	python scripts/run_quality_worker.py --once