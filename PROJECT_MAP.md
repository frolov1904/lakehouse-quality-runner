# Project Map

Короткая карта проекта `lakehouse-quality-runner`.

Этот файл нужен, чтобы быстро ориентироваться в проекте: где находится API, где pytest-плагин, где Spark, Kafka, Iceberg, тесты и основные команды запуска.

---

## 1. Главная идея проекта

Проект показывает учебный mini lakehouse pipeline:

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
```

Основная цель проекта — показать практические навыки:

* разработки backend API;
* работы с S3-compatible хранилищем;
* написания собственного pytest-плагина;
* использования pytest hooks, fixtures и markers;
* публикации и чтения Kafka-событий;
* запуска Spark job;
* работы с raw/silver слоями;
* создания Iceberg-таблицы;
* генерации data quality report;
* настройки CI/CD.

---

## 2. Где находится FastAPI

Главные файлы:

```text
app/main.py
app/api/datasets.py
```

`app/main.py` создает FastAPI-приложение и подключает роуты.

`app/api/datasets.py` содержит endpoint'ы для работы с dataset-файлами.

Основные endpoint'ы:

```text
GET /health
POST /datasets/{dataset}/upload
GET /datasets/{dataset}/objects
```

Что делает API:

```text
POST /datasets/orders/upload
  ↓
принимает CSV-файл
  ↓
загружает файл в MinIO/S3 по key raw/orders/<filename>
  ↓
публикует Kafka-событие file_uploaded
```

---

## 3. Где находится работа с S3 / MinIO

Основные файлы:

```text
app/services/s3_storage.py
pytest_etl_guard/s3.py
scripts/upload_sample_data.py
scripts/clean_lakehouse_storage.py
```

`app/services/s3_storage.py` — основной сервис для работы с S3 в приложении и ETL job'ах.

Он умеет:

```text
upload_fileobj
download_file
upload_file
upload_directory
delete_prefix
list_objects
```

`pytest_etl_guard/s3.py` — S3-логика внутри pytest-плагина.

`upload_sample_data.py` — загружает `data/orders.csv` в raw-слой.

`clean_lakehouse_storage.py` — очищает MinIO/S3 от временных и demo-артефактов.

Основные S3 prefix'ы:

```text
raw/                  входные raw-данные
silver/               результат Spark-обработки
quality-reports/      отчеты pytest-плагина
test-artifacts/       временные тестовые артефакты
```

---

## 4. Где находится Kafka

Основные файлы:

```text
app/services/kafka_events.py
app/workers/quality_worker.py
scripts/run_quality_worker.py
```

`app/services/kafka_events.py` содержит:

```text
FileUploadedEvent
KafkaEventPublisher
build_file_uploaded_event
parse_file_uploaded_event
```

Producer публикует событие после загрузки файла через API.

Topic:

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

Worker находится здесь:

```text
app/workers/quality_worker.py
```

Скрипт запуска worker'а:

```text
scripts/run_quality_worker.py
```

Запуск:

```bash
python scripts/run_quality_worker.py --once
```

---

## 5. Где находится Spark

Основные файлы:

```text
app/services/orders_spark_job.py
scripts/run_orders_spark_job.py
tests/spark/test_orders_spark_job.py
```

`OrdersSparkJob` делает преобразование:

```text
raw/orders/orders.csv
  ↓
Spark
  ↓
silver/orders/*.parquet
```

Что делает Spark job:

```text
1. Скачивает raw CSV из MinIO/S3.
2. Читает CSV через PySpark.
3. Использует явную схему.
4. Фильтрует невалидные строки.
5. Приводит created_at к date.
6. Записывает результат в Parquet.
7. Загружает Parquet-файлы обратно в MinIO/S3.
```

Запуск:

```bash
python scripts/run_orders_spark_job.py
```

Или через Makefile:

```bash
make spark-job
```

Demo-запуск:

```bash
make demo-run-spark
```

---

## 6. Где находится Iceberg

Основные файлы:

```text
app/services/orders_iceberg_job.py
scripts/run_orders_iceberg_job.py
scripts/query_orders_iceberg_table.py
tests/iceberg/test_orders_iceberg_job.py
```

`OrdersIcebergJob` создает Iceberg-таблицу поверх silver Parquet.

Источник:

```text
silver/orders/*.parquet
```

Итоговая таблица:

```text
local.analytics.orders
```

Локальный Iceberg warehouse:

```text
.tmp/iceberg/warehouse
```

Запуск Iceberg job:

```bash
python scripts/run_orders_iceberg_job.py
```

Или:

```bash
make iceberg-job
```

Посмотреть Iceberg-таблицу:

```bash
python scripts/query_orders_iceberg_table.py
```

Или:

```bash
make query-iceberg
```

Demo-просмотр:

```bash
make demo-query-iceberg
```

---

## 7. Где находится pytest-плагин

Основные файлы:

```text
pytest_etl_guard/plugin.py
pytest_etl_guard/config.py
pytest_etl_guard/reporting.py
pytest_etl_guard/s3.py
```

`plugin.py` — точка входа pytest-плагина.

`config.py` отвечает за:

```text
CLI-опции
markers
загрузку конфигурации
автоматический run_id
etl_context
```

`reporting.py` отвечает за:

```text
формирование quality report
summary
локальный путь report.json
S3 key для report.json
сохранение отчета локально
```

`s3.py` отвечает за:

```text
создание boto3 client
загрузку report.json в S3
```

Главные pytest hooks:

```text
pytest_addoption
pytest_configure
pytest_runtest_makereport
pytest_sessionfinish
```

Что делает плагин:

```text
1. Добавляет CLI-опции.
2. Регистрирует markers.
3. Создает fixtures.
4. Собирает результаты ETL/data quality тестов.
5. Формирует report.json.
6. Сохраняет report.json локально.
7. Загружает report.json в MinIO/S3.
```

---

## 8. Pytest fixtures

Основные fixtures плагина:

```text
etl_context
s3_client
s3_bucket
```

`etl_context` содержит параметры запуска:

```text
env
dataset
run_id
s3
quality_report
```

`s3_client` — boto3 client для работы с MinIO/S3.

`s3_bucket` — название bucket, обычно:

```text
data-lake
```

---

## 9. Pytest markers

В проекте используются markers:

```text
etl
quality
s3
spark
silver
iceberg
```

Пример:

```python
@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.silver
def test_orders_silver_schema_is_correct():
    ...
```

Запуск только silver-проверок:

```bash
pytest tests/quality -m silver
```

Запуск только Iceberg-тестов:

```bash
pytest tests/iceberg -q
```

---

## 10. Где находятся data quality checks

Raw checks:

```text
tests/quality/test_orders_s3.py
```

Проверяют:

```text
raw/orders/orders.csv существует
raw-файл не пустой
CSV содержит обязательные колонки
```

Silver checks:

```text
tests/quality/test_orders_silver.py
```

Проверяют:

```text
silver/orders/ содержит _SUCCESS
silver/orders/ содержит .parquet файлы
Parquet читается через Spark
данные не пустые
схема корректная
order_id не null
user_id не null
amount не null
amount >= 0
status входит в допустимый список
```

---

## 11. Где находится orchestration pipeline

Основные файлы:

```text
app/services/pipeline_runner.py
app/workers/quality_worker.py
```

`FileUploadedPipelineRunner` связывает несколько шагов:

```text
Kafka file_uploaded event
  ↓
OrdersSparkJob
  ↓
PytestQualityRunner
  ↓
PipelineRunResult
```

Worker использует pipeline runner после получения Kafka-события.

Итоговая цепочка:

```text
FastAPI upload
  ↓
Kafka event
  ↓
QualityWorker
  ↓
Spark raw → silver
  ↓
pytest quality checks
  ↓
quality report
```

---

## 12. Где находится запуск pytest из worker'а

Файл:

```text
app/services/quality_runner.py
```

Класс:

```text
PytestQualityRunner
```

Он формирует команду:

```text
python -m pytest tests/quality --dataset=<dataset> --run-id=<run_id>
```

Важно: используется `sys.executable`, чтобы pytest запускался тем же Python из текущего виртуального окружения.

---

## 13. Где находится конфигурация проекта

Главный локальный конфиг:

```text
etl_guard.local.json
```

В нем лежат настройки:

```text
etl_env
dataset
s3
quality_report
kafka
lakehouse
```

Основные блоки:

```json
{
  "s3": {
    "endpoint": "http://localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "bucket": "data-lake"
  },
  "kafka": {
    "enabled": true,
    "bootstrap_servers": "localhost:9092",
    "topic_file_uploaded": "etl.file_uploaded"
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

---

## 14. Где находится Docker Compose

Файл:

```text
docker-compose.yml
```

Поднимает:

```text
MinIO
Kafka
create-bucket container
```

Запуск:

```bash
docker compose up -d
```

Или:

```bash
make infra-up
```

Остановка:

```bash
docker compose down
```

Или:

```bash
make infra-down
```

---

## 15. Где находится CI/CD

Файл:

```text
.gitlab-ci.yml
```

Pipeline stages:

```text
lint
test
quality
```

Что делает CI:

```text
lint      → ruff check .
test      → быстрые unit/service/plugin тесты
quality   → smoke-проверка pytest-плагина + artifacts
```

Тяжелые integration-тесты со Spark, Iceberg, Kafka и MinIO остаются локальными, потому что требуют поднятой инфраструктуры.

---

## 16. Где находится Makefile

Файл:

```text
Makefile
```

Основные команды:

```bash
make install
make install-dev
make lint
make test
make test-ci
make test-quality
make test-silver
make test-spark
make test-iceberg
make infra-up
make infra-down
make upload-sample
make spark-job
make iceberg-job
make query-iceberg
make worker
make clean-storage
make demo-reset
make demo-prepare
make demo-run-spark
make demo-run-iceberg
make demo-query-iceberg
make demo-test-quality
make demo-full
```

---

## 17. Основной demo-сценарий

Полный demo-сценарий:

```bash
make demo-full
```

Он выполняет:

```text
1. Поднимает инфраструктуру.
2. Очищает demo-данные.
3. Загружает sample CSV в raw-слой.
4. Запускает Spark raw → silver.
5. Запускает Iceberg job.
6. Показывает Iceberg table.
7. Запускает quality checks.
```

То же самое по шагам:

```bash
make infra-up
make demo-reset
make demo-prepare
make demo-run-spark
make demo-run-iceberg
make demo-query-iceberg
make demo-test-quality
```

---

## 18. Как пощупать последний слой Iceberg

Сначала подготовить данные:

```bash
make infra-up
make demo-reset
make demo-prepare
make demo-run-spark
make demo-run-iceberg
```

Потом посмотреть таблицу:

```bash
make demo-query-iceberg
```

Скрипт покажет:

```text
DESCRIBE TABLE local.analytics.orders
SELECT * FROM local.analytics.orders LIMIT 20
SELECT status, COUNT(*), SUM(amount) GROUP BY status
```

---

## 19. Как очистить MinIO/S3

Обычная очистка временного мусора:

```bash
make clean-storage
```

Demo-reset:

```bash
make demo-reset
```

Полная очистка bucket:

```bash
python scripts/clean_lakehouse_storage.py --all
```

Что чистится:

```text
quality-reports/
test-artifacts/
raw/pytester/
raw/test/
silver/test/
```

В demo-reset дополнительно чистится:

```text
raw/orders/
silver/orders/
```

---

## 20. Как запустить быстрые проверки

Быстрые тесты без тяжелой инфраструктуры:

```bash
make test-ci
```

Они подходят для CI.

---

## 21. Как запустить полный локальный прогон

Сначала подготовить инфраструктуру и данные:

```bash
make infra-up
make upload-sample
make spark-job
make iceberg-job
```

Потом:

```bash
make test
```

---

## 22. Как проверить только pytest-плагин

Plugin tests:

```bash
pytest tests/plugin -q
```

Quality context smoke:

```bash
pytest tests/quality/test_etl_context.py -q
```

---

## 23. Как проверить только Spark

```bash
make test-spark
```

или:

```bash
pytest tests/spark -q
```

---

## 24. Как проверить только Iceberg

```bash
make test-iceberg
```

или:

```bash
pytest tests/iceberg -q
```

---

## 25. Что смотреть на собеседовании

Если нужно быстро показать проект, лучше идти в таком порядке:

1. `README.md` — общая идея.
2. `PROJECT_MAP.md` — карта проекта.
3. `pytest_etl_guard/plugin.py` — pytest hooks.
4. `pytest_etl_guard/reporting.py` — генерация report.
5. `app/api/datasets.py` — FastAPI upload.
6. `app/services/kafka_events.py` — Kafka producer.
7. `app/workers/quality_worker.py` — Kafka consumer worker.
8. `app/services/orders_spark_job.py` — Spark raw → silver.
9. `tests/quality/test_orders_silver.py` — silver quality checks.
10. `app/services/orders_iceberg_job.py` — Iceberg table.
11. `.gitlab-ci.yml` — CI/CD.
12. `Makefile` — удобные команды запуска.

---

## 26. Что важно не забыть

Перед запуском Spark/Iceberg нужна Java:

```bash
java -version
```

Перед S3/Kafka-тестами нужна инфраструктура:

```bash
make infra-up
```

Перед silver-проверками нужен Spark job:

```bash
make spark-job
```

Перед просмотром Iceberg-таблицы нужен Iceberg job:

```bash
make iceberg-job
```

Если MinIO засорился:

```bash
make demo-reset
```

или:

```bash
python scripts/clean_lakehouse_storage.py --all
```
