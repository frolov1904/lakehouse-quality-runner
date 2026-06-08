# Lakehouse Quality Runner

Учебный проект для практики backend/data engineering/DLH-направления.

Проект показывает полный mini lakehouse pipeline:

```text
FastAPI
  ↓
MinIO / S3 raw layer
  ↓
Kafka file_uploaded event
  ↓
Kafka consumer worker
  ↓
Spark raw → silver
  ↓
Iceberg table
  ↓
pytest data quality checks
  ↓
quality report
  ↓
MinIO / S3 quality-reports
  ↓
GitLab CI/CD
```

Основная цель проекта — показать практические навыки работы с:

* Python;
* FastAPI;
* pytest hooks и pytest-плагинами;
* MinIO/S3;
* boto3;
* Kafka;
* Spark / PySpark;
* Parquet;
* Iceberg;
* Docker Compose;
* GitLab CI/CD;
* data quality checks;
* ETL/pipeline orchestration.

---

## 1. Идея проекта

`lakehouse-quality-runner` — это учебный сервис для проверки качества данных в lakehouse-пайплайне.

Проект имитирует реальный процесс:

1. Пользователь загружает CSV-файл через FastAPI.
2. Файл сохраняется в raw-слой S3-compatible хранилища MinIO.
3. После загрузки публикуется Kafka-событие `file_uploaded`.
4. Worker читает Kafka-событие.
5. Worker запускает Spark job.
6. Spark job преобразует raw CSV в silver Parquet.
7. Silver-данные могут быть использованы для создания Iceberg-таблицы.
8. pytest-плагин запускает data quality checks.
9. По результатам проверок формируется `report.json`.
10. Отчет сохраняется локально и загружается в MinIO/S3.

---

## 2. Архитектура

```text
                    ┌────────────────────┐
                    │      FastAPI        │
                    │ file upload API     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     MinIO / S3      │
                    │   raw/orders.csv    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │       Kafka         │
                    │ etl.file_uploaded   │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  Quality Worker     │
                    │ consumer + runner   │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │       Spark         │
                    │ raw CSV → silver    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   Silver Parquet    │
                    │  silver/orders/     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │      Iceberg        │
                    │ analytics.orders    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   pytest plugin     │
                    │ data quality checks │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  quality report     │
                    │ S3 quality-reports  │
                    └────────────────────┘
```

---

## 3. Стек технологий

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic/FastAPI request handling

### Тестирование

* pytest
* custom pytest plugin
* pytest hooks:

  * `pytest_addoption`
  * `pytest_configure`
  * `pytest_runtest_makereport`
  * `pytest_sessionfinish`
* pytest fixtures
* pytest markers
* pytester

### Хранилище

* MinIO
* S3-compatible API
* boto3

### Data Engineering

* Spark / PySpark
* Parquet
* Iceberg
* Raw/Silver слои

### Messaging

* Kafka
* confluent-kafka Producer
* confluent-kafka Consumer

### DevOps

* Docker Compose
* GitLab CI/CD
* Makefile
* Ruff

---

## 4. Основные возможности

В проекте реализовано:

* собственный pytest-плагин для ETL/data quality проверок;
* передача параметров запуска через CLI;
* конфигурация запуска через `etl_guard.local.json`;
* автоматическая генерация `run_id`;
* генерация `quality report`;
* загрузка `report.json` в MinIO/S3;
* локальный S3 через MinIO;
* FastAPI endpoint для загрузки raw-файлов;
* Kafka-событие после загрузки файла;
* Kafka consumer worker;
* Spark job `raw → silver`;
* проверки raw-слоя;
* проверки silver-слоя;
* Iceberg table поверх silver-данных;
* Makefile-команды для удобного запуска;
* GitLab CI/CD pipeline.

---

## 5. Структура проекта

```text
lakehouse-quality-runner/
│
├── app/
│   ├── api/
│   │   └── datasets.py
│   │
│   ├── core/
│   │   └── settings.py
│   │
│   ├── services/
│   │   ├── kafka_events.py
│   │   ├── orders_iceberg_job.py
│   │   ├── orders_spark_job.py
│   │   ├── pipeline_runner.py
│   │   ├── quality_runner.py
│   │   └── s3_storage.py
│   │
│   ├── workers/
│   │   └── quality_worker.py
│   │
│   └── main.py
│
├── pytest_etl_guard/
│   ├── config.py
│   ├── plugin.py
│   ├── reporting.py
│   └── s3.py
│
├── tests/
│   ├── api/
│   ├── iceberg/
│   ├── plugin/
│   ├── quality/
│   ├── services/
│   └── spark/
│
├── scripts/
│   ├── run_orders_iceberg_job.py
│   ├── run_orders_spark_job.py
│   ├── run_quality_worker.py
│   └── upload_sample_data.py
│
├── data/
│   └── orders.csv
│
├── docker-compose.yml
├── etl_guard.local.json
├── pyproject.toml
├── Makefile
├── .gitlab-ci.yml
├── CHANGELOG.md
└── README.md
```

---

## 6. Требования

Для локального запуска нужны:

* Python 3.10+ рекомендуется;
* Docker;
* Docker Compose;
* Java 17 для Spark;
* Git.

Проект может запускаться на Python 3.9, но лучше использовать Python 3.10 или выше, потому что часть библиотек постепенно прекращает поддержку Python 3.9.

Проверить Java:

```bash
java -version
```

Ожидается Java 17 или совместимая версия.

---

## 7. Установка

Создать виртуальное окружение:

```bash
python3 -m venv .venv
```

Активировать окружение:

```bash
source .venv/bin/activate
```

Обновить базовые инструменты:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Установить проект:

```bash
pip install -e .
```

Установить проект с dev-зависимостями:

```bash
pip install -e ".[dev]"
```

---

## 8. Конфигурация

Основной локальный конфиг находится в файле:

```text
etl_guard.local.json
```

Пример:

```json
{
  "etl_env": "local",
  "dataset": "orders",
  "s3": {
    "endpoint": "http://localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "bucket": "data-lake"
  },
  "quality_report": {
    "local_dir": "quality-reports",
    "upload_to_s3": true,
    "s3_prefix": "quality-reports"
  },
  "kafka": {
    "enabled": true,
    "bootstrap_servers": "localhost:9092",
    "topic_file_uploaded": "etl.file_uploaded",
    "quality_worker_group": "lqr-quality-worker",
    "auto_offset_reset": "earliest"
  },
  "lakehouse": {
    "raw_prefix": "raw",
    "silver_prefix": "silver",
    "local_tmp_dir": ".tmp/lakehouse",
    "iceberg_warehouse": ".tmp/iceberg/warehouse",
    "iceberg_catalog": "local",
    "iceberg_namespace": "analytics"
  }
}
```

CLI-флаги pytest-плагина могут переопределять значения из конфига.

Например:

```bash
pytest tests --dataset=orders
```

или:

```bash
pytest tests --run-id=my_manual_run
```

Если `run_id` не передан вручную, он генерируется автоматически.

Пример:

```text
orders_20260608_120000
```

---

## 9. Запуск инфраструктуры

Поднять MinIO и Kafka:

```bash
docker compose up -d
```

Проверить контейнеры:

```bash
docker ps
```

Ожидаемые контейнеры:

```text
lqr-minio
lqr-kafka
```

MinIO console:

```text
http://localhost:9001
```

Логин:

```text
minioadmin
```

Пароль:

```text
minioadmin
```

Bucket:

```text
data-lake
```

Остановить инфраструктуру:

```bash
docker compose down
```

---

## 10. FastAPI

Запустить приложение:

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

Healthcheck:

```text
GET /health
```

Пример ответа:

```json
{
  "status": "ok",
  "service": "lakehouse-quality-runner"
}
```

---

## 11. Загрузка raw-файла через API

Endpoint:

```text
POST /datasets/{dataset}/upload
```

Пример через curl:

```bash
curl -X POST "http://localhost:8000/datasets/orders/upload" \
  -F "file=@data/orders.csv"
```

Пример ответа:

```json
{
  "dataset": "orders",
  "bucket": "data-lake",
  "key": "raw/orders/orders.csv",
  "status": "uploaded",
  "event": {
    "published": true,
    "topic": "etl.file_uploaded",
    "event_id": "..."
  }
}
```

После загрузки файл появляется в MinIO:

```text
s3://data-lake/raw/orders/orders.csv
```

---

## 12. Просмотр объектов dataset

Endpoint:

```text
GET /datasets/{dataset}/objects
```

Пример:

```bash
curl "http://localhost:8000/datasets/orders/objects"
```

Пример ответа:

```json
{
  "dataset": "orders",
  "bucket": "data-lake",
  "prefix": "raw/orders/",
  "objects": [
    {
      "key": "raw/orders/orders.csv",
      "size": 100,
      "last_modified": "..."
    }
  ]
}
```

---

## 13. Kafka-событие после загрузки файла

После загрузки файла FastAPI публикует событие в Kafka topic:

```text
etl.file_uploaded
```

Пример события:

```json
{
  "event_id": "...",
  "event_type": "file_uploaded",
  "dataset": "orders",
  "bucket": "data-lake",
  "key": "raw/orders/orders.csv",
  "filename": "orders.csv",
  "content_type": "text/csv",
  "occurred_at": "..."
}
```

Идея:

```text
API не запускает ETL напрямую.
API только сообщает: файл загружен.
Worker читает Kafka-событие и запускает обработку.
```

---

## 14. Kafka worker

Запустить worker в режиме обработки одного сообщения:

```bash
python scripts/run_quality_worker.py --once
```

Worker делает:

```text
1. Подписывается на Kafka topic etl.file_uploaded.
2. Читает событие file_uploaded.
3. Формирует run_id на основе event_id.
4. Запускает Spark job raw → silver.
5. Запускает pytest quality checks.
6. После обработки коммитит Kafka offset.
```

Пример ожидаемого вывода:

```text
Quality worker subscribed to topic: etl.file_uploaded
Received file_uploaded event: dataset=orders, key=raw/orders/orders.csv, event_id=...
Starting pipeline: dataset=orders, run_id=orders_71c6b017, raw_key=raw/orders/orders.csv
Pipeline finished: dataset=orders, run_id=orders_71c6b017, status=success, spark_rows_read=4, spark_rows_written=4, quality_exit_code=0
Quality worker processed one message and stopped
```

---

## 15. Spark job: raw → silver

Spark job преобразует raw CSV в silver Parquet.

Запуск:

```bash
python scripts/run_orders_spark_job.py
```

Что делает job:

```text
1. Скачивает raw/orders/orders.csv из S3/MinIO.
2. Читает CSV через Spark.
3. Применяет явную схему.
4. Фильтрует невалидные строки.
5. Приводит created_at к date.
6. Записывает результат в Parquet.
7. Загружает Parquet-файлы обратно в S3.
```

Результат:

```text
s3://data-lake/silver/orders/
```

Внутри будут файлы:

```text
_SUCCESS
part-....snappy.parquet
```

`_SUCCESS` — это служебный marker-файл Spark, который показывает, что запись завершилась успешно.

---

## 16. Iceberg job

Iceberg job создает таблицу поверх silver Parquet.

Запуск:

```bash
python scripts/run_orders_iceberg_job.py
```

Что делает job:

```text
1. Берет silver/orders/*.parquet.
2. Скачивает Parquet-файлы локально.
3. Создает SparkSession с Iceberg runtime.
4. Создает namespace analytics.
5. Создает таблицу local.analytics.orders.
6. Проверяет, что таблица читается через Spark SQL.
```

Результат:

```text
local.analytics.orders
```

Локальный Iceberg warehouse:

```text
.tmp/iceberg/warehouse
```

Пример структуры:

```text
.tmp/iceberg/warehouse/analytics/orders/
├── data/
└── metadata/
```

---

## 17. pytest-плагин ETL Guard

В проекте реализован собственный pytest-плагин:

```text
pytest_etl_guard
```

Он подключается через entry point:

```toml
[project.entry-points.pytest11]
etl_guard = "pytest_etl_guard.plugin"
```

Плагин реализует:

* CLI-опции запуска;
* загрузку конфигурации из `etl_guard.local.json`;
* автоматическую генерацию `run_id`;
* fixtures:

  * `etl_context`;
  * `s3_client`;
  * `s3_bucket`;
* markers:

  * `etl`;
  * `quality`;
  * `s3`;
  * `spark`;
  * `silver`;
  * `iceberg`;
* сбор результатов тестов;
* генерацию `report.json`;
* загрузку отчета в S3.

Основные hooks:

```text
pytest_addoption
pytest_configure
pytest_runtest_makereport
pytest_sessionfinish
```

---

## 18. Data quality checks

### Raw checks

Файл:

```text
tests/quality/test_orders_s3.py
```

Проверки:

```text
raw/orders/orders.csv существует;
файл не пустой;
CSV содержит обязательные колонки.
```

Обязательные колонки:

```text
order_id
user_id
amount
status
created_at
```

### Silver checks

Файл:

```text
tests/quality/test_orders_silver.py
```

Проверки:

```text
silver/orders/ содержит _SUCCESS;
silver/orders/ содержит .parquet файлы;
Parquet читается через Spark;
данные не пустые;
схема корректная;
order_id не null;
user_id не null;
amount не null;
amount >= 0;
status входит в допустимый список.
```

Ожидаемая схема:

```text
order_id: int
user_id: int
amount: double
status: string
created_at: date
```

Допустимые значения `status`:

```text
new
paid
cancelled
```

---

## 19. Quality report

После запуска pytest-проверок плагин формирует отчет:

```text
quality-reports/<run_id>/report.json
```

Пример структуры:

```json
{
  "run_id": "orders_20260608_120000",
  "dataset": "orders",
  "env": "local",
  "started_at": "...",
  "finished_at": "...",
  "exitstatus": 0,
  "s3": {
    "endpoint": "http://localhost:9000",
    "bucket": "data-lake"
  },
  "quality_report": {
    "local_path": "quality-reports/orders_20260608_120000/report.json",
    "upload_to_s3": true,
    "s3_key": "quality-reports/orders_20260608_120000/report.json"
  },
  "summary": {
    "total": 10,
    "passed": 10,
    "failed": 0,
    "skipped": 0
  },
  "tests": []
}
```

Если включена загрузка в S3, отчет также сохраняется в MinIO:

```text
s3://data-lake/quality-reports/<run_id>/report.json
```

---

## 20. Тесты

### Быстрые тесты

```bash
pytest tests/services tests/plugin -q
```

или:

```bash
make test-ci
```

### Все тесты

```bash
pytest tests
```

или:

```bash
make test
```

### Только quality checks

```bash
pytest tests/quality
```

или:

```bash
make test-quality
```

### Только silver checks

```bash
pytest tests/quality -m silver
```

или:

```bash
make test-silver
```

### Только Spark tests

```bash
pytest tests/spark -q
```

или:

```bash
make test-spark
```

### Только Iceberg tests

```bash
pytest tests/iceberg -q
```

или:

```bash
make test-iceberg
```

---

## 21. Makefile-команды

В проекте есть `Makefile`.

Основные команды:

```bash
make install
```

Установить проект.

```bash
make install-dev
```

Установить проект с dev-зависимостями.

```bash
make lint
```

Запустить `ruff`.

```bash
make test
```

Запустить все тесты.

```bash
make test-ci
```

Запустить быстрые CI-тесты.

```bash
make test-quality
```

Запустить data quality checks.

```bash
make test-silver
```

Запустить проверки silver-слоя.

```bash
make test-spark
```

Запустить Spark-тесты.

```bash
make test-iceberg
```

Запустить Iceberg-тесты.

```bash
make infra-up
```

Поднять MinIO и Kafka.

```bash
make infra-down
```

Остановить инфраструктуру.

```bash
make upload-sample
```

Загрузить sample CSV в raw-слой.

```bash
make spark-job
```

Запустить Spark job.

```bash
make iceberg-job
```

Запустить Iceberg job.

```bash
make worker
```

Запустить Kafka worker в режиме `--once`.

---

## 22. Полный локальный сценарий запуска

Поднять инфраструктуру:

```bash
make infra-up
```

Загрузить sample raw-файл:

```bash
make upload-sample
```

Запустить Spark job:

```bash
make spark-job
```

Запустить Iceberg job:

```bash
make iceberg-job
```

Запустить тесты:

```bash
make test
```

Запустить FastAPI:

```bash
uvicorn app.main:app --reload
```

Открыть Swagger:

```text
http://localhost:8000/docs
```

Запустить worker:

```bash
make worker
```

---

## 23. GitLab CI/CD

В проект добавлен файл:

```text
.gitlab-ci.yml
```

Pipeline содержит stages:

```text
lint
test
quality
```

### lint

Проверяет код через:

```bash
ruff check .
```

### test

Запускает быстрые unit/service/plugin тесты:

```bash
pytest tests/services tests/plugin -q
```

### quality

Запускает smoke-проверку pytest-плагина и сохраняет `quality-reports/` как artifact.

Artifacts:

```text
quality-reports/
```

Тяжелые integration-тесты со Spark, Iceberg, Kafka и MinIO требуют локальной инфраструктуры, поэтому они вынесены в локальный запуск.

