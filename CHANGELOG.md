# Changelog

## [0.1.0] — Базовый pytest-плагин

### Добавлено

- Создана базовая структура проекта.
- Добавлен Python-пакет `pytest_etl_guard`.
- Настроен `pyproject.toml`.
- Подключен pytest-плагин через `project.entry-points.pytest11`.
- Добавлен hook `pytest_addoption`.
- Добавлены CLI-опции:
  - `--etl-env`
  - `--dataset`
  - `--run-id`
- Добавлен hook `pytest_configure`.
- Зарегистрированы markers:
  - `etl`
  - `quality`
- Добавлена fixture `etl_context`.
- Добавлен первый тест `test_etl_context_is_created`.

### Проверка

- Проверено, что pytest видит пользовательские CLI-опции.
- Проверено, что fixture `etl_context` передает параметры запуска в тест.

## [0.2.0] — Подключение MinIO/S3 и первые проверки данных

### Добавлено

- Добавлен `docker-compose.yml` для запуска локального S3-compatible хранилища MinIO.
- Добавлен автоматический create-bucket контейнер для создания bucket `data-lake`.
- Добавлена зависимость `boto3`.
- Добавлен тестовый dataset `data/orders.csv`.
- Добавлен скрипт `scripts/upload_sample_data.py` для загрузки тестового CSV в MinIO.
- В pytest-плагин добавлены CLI-опции:
  - `--s3-endpoint`
  - `--s3-access-key`
  - `--s3-secret-key`
  - `--s3-bucket`
- Добавлен marker `s3`.
- Добавлены fixtures:
  - `s3_client`
  - `s3_bucket`
- Расширена fixture `etl_context`: теперь она содержит S3-настройки.
- Добавлены первые S3/data quality тесты:
  - проверка существования raw-файла;
  - проверка, что raw-файл не пустой;
  - проверка обязательных колонок CSV.

### Проверка

- Проверено подключение к локальному MinIO через `boto3`.
- Проверена загрузка файла `orders.csv` в `s3://data-lake/raw/orders/orders.csv`.
- Проверено выполнение ETL quality тестов через pytest.

## [0.3.0] — Генерация quality report через pytest hooks

### Добавлено

- Добавлена CLI-опция `--quality-report-dir`.
- Добавлен hook `pytest_runtest_makereport`.
- Добавлен сбор результатов ETL/data quality тестов:
  - `nodeid`;
  - имя теста;
  - статус выполнения;
  - длительность выполнения;
  - markers;
  - текст ошибки при падении.
- Добавлен hook `pytest_sessionfinish`.
- Добавлена генерация локального `report.json` после завершения pytest-сессии.
- Добавлен расчет summary:
  - общее количество проверок;
  - количество успешных проверок;
  - количество упавших проверок;
  - количество пропущенных проверок.
- Расширена fixture `etl_context`: добавлено поле `quality_report_dir`.

### Проверка

- Проверено, что после запуска pytest создается файл `quality-reports/run_001/report.json`.
- Проверено, что в отчет попадают только тесты с markers `etl` или `quality`.
- Проверено, что отчет содержит параметры запуска, S3-настройки, summary и список проверок.

## [0.4.0] — Сохранение quality report в S3

### Добавлено

- Добавлена CLI-опция `--upload-quality-report-to-s3`.
- Добавлена CLI-опция `--quality-report-s3-prefix`.
- Добавлена возможность загружать сформированный `report.json` в S3-compatible хранилище.
- Добавлено формирование S3 key для отчета в формате:
  - `quality-reports/<run_id>/report.json`.
- В `report.json` добавлен блок `quality_report`:
  - локальный путь к отчету;
  - флаг загрузки отчета в S3;
  - S3 key отчета.
- Добавлен pytester-тест `test_plugin_uploads_quality_report_to_s3`, который проверяет полный сценарий работы плагина:
  - создание временного ETL-теста;
  - запуск pytest через `pytester`;
  - генерацию quality report;
  - загрузку `report.json` в S3/MinIO;
  - чтение загруженного отчета через `boto3.get_object`.
- Добавлен корневой `conftest.py` для подключения встроенного pytest-плагина `pytester`.
- Добавлены вспомогательные функции:
  - `_build_s3_client`;
  - `_build_report_s3_key`;
  - `_save_report_locally`;
  - `_upload_report_to_s3`;
  - `_make_safe_path_part`.

### Изменено

- Расширена fixture `etl_context`:
  - добавлено поле `quality_report_s3_prefix`;
  - добавлено поле `upload_quality_report_to_s3`.
- Обновлена версия проекта до `0.4.0`.
- Исправлена настройка package discovery в `pyproject.toml`.
- Явно указано, что устанавливаемым Python-пакетом является только `pytest_etl_guard`.
- Исключены из package discovery служебные директории:
  - `data`;
  - `tests`;
  - `scripts`;
  - `quality-reports`.

### Проверка

- Проверено локальное создание `quality-reports/run_001/report.json`.
- Проверена загрузка отчета в `s3://data-lake/quality-reports/run_001/report.json`.
- Ручная проверка чтения отчета из S3 заменена на автоматизированный pytester-тест.
- Проверено, что общий запуск тестов проходит успешно.

## [0.5.0] — Рефакторинг плагина и конфигурация запуска

### Добавлено

- Добавлен модуль `pytest_etl_guard.config`.
- Добавлен модуль `pytest_etl_guard.reporting`.
- Добавлен модуль `pytest_etl_guard.s3`.
- Добавлен конфигурационный файл `etl_guard.local.json`.
- Добавлена CLI-опция `--etl-config`.
- Добавлена автоматическая генерация `run_id`, если он не передан вручную.
- Добавлен пример файла окружения `.env.example`.

### Изменено

- Упрощен файл `pytest_etl_guard/plugin.py`.
- Логика регистрации CLI-опций вынесена в `config.py`.
- Логика регистрации pytest markers вынесена в `config.py`.
- Логика формирования `etl_context` вынесена в `config.py`.
- Логика создания S3-клиента вынесена в `s3.py`.
- Логика загрузки `report.json` в S3 вынесена в `s3.py`.
- Логика формирования quality report вынесена в `reporting.py`.
- Логика расчета summary вынесена в `reporting.py`.
- Логика формирования локального пути отчета и S3 key вынесена в `reporting.py`.
- Основные параметры запуска теперь можно хранить в `etl_guard.local.json`.
- CLI-флаги теперь переопределяют значения из конфигурационного файла.
- Структура `etl_context` стала более явной:
  - настройки S3 лежат в блоке `s3`;
  - настройки отчета лежат в блоке `quality_report`.
- Обновлена версия проекта до `0.5.0`.

### Проверка

- Проверено, что проект запускается короткой командой `pytest tests`.
- Проверено, что `run_id` генерируется автоматически.
- Проверено, что `report.json` создается в директории с автоматически сгенерированным `run_id`.
- Проверено, что `report.json` загружается в MinIO/S3.
- Проверено, что pytester-тест полного сценария работы плагина проходит успешно.

## [0.6.0] — FastAPI-слой для загрузки raw-файлов в S3

### Добавлено

- Добавлен FastAPI-слой проекта.
- Добавлен пакет `app`.
- Добавлен healthcheck endpoint:
  - `GET /health`.
- Добавлен endpoint для загрузки dataset-файла в raw-слой S3:
  - `POST /datasets/{dataset}/upload`.
- Добавлен endpoint для просмотра объектов raw-слоя:
  - `GET /datasets/{dataset}/objects`.
- Добавлен модуль `app.core.settings` для загрузки S3-настроек из `etl_guard.local.json`.
- Добавлен сервис `S3Storage` для работы с S3-compatible хранилищем.
- Добавлены API-тесты:
  - проверка healthcheck;
  - проверка загрузки CSV-файла через API в MinIO/S3;
  - проверка получения списка объектов dataset.

### Изменено

- В `pyproject.toml` добавлены зависимости:
  - `fastapi`;
  - `uvicorn`;
  - `python-multipart`.
- В package discovery добавлен пакет `app`.
- Обновлена версия проекта до `0.6.0`.

### Проверка

- Проверено, что FastAPI запускается командой `uvicorn app.main:app --reload`.
- Проверено, что Swagger UI доступен по адресу `/docs`.
- Проверена загрузка `orders.csv` через API в `s3://data-lake/raw/orders/orders.csv`.
- Проверено, что общий запуск тестов проходит успешно.

## [0.7.0] — Публикация Kafka-события после загрузки файла

### Добавлено

- Добавлен сервис Kafka в `docker-compose.yml`.
- Добавлена зависимость `confluent-kafka`.
- В `etl_guard.local.json` добавлен блок `kafka`.
- Добавлены настройки Kafka:
  - `enabled`;
  - `bootstrap_servers`;
  - `topic_file_uploaded`.
- Добавлен dataclass `KafkaSettings`.
- Расширен dataclass `AppSettings`: добавлен блок Kafka-настроек.
- Добавлен модуль `app.services.kafka_events`.
- Добавлен dataclass `FileUploadedEvent`.
- Добавлен сервис `KafkaEventPublisher`.
- Добавлена функция `build_file_uploaded_event`.
- После загрузки файла через `POST /datasets/{dataset}/upload` теперь публикуется событие `file_uploaded` в Kafka topic `etl.file_uploaded`.
- В ответ endpoint загрузки добавлен блок `event`:
  - `published`;
  - `topic`;
  - `event_id`.
- Добавлен API-тест `test_upload_dataset_file_publishes_kafka_event`, который проверяет публикацию Kafka-события после загрузки файла.
- В тесты добавлены helper-функции:
  - `_ensure_topic_exists`;
  - `_poll_event_by_id`;
  - `_wait_until_consumer_assigned`.

### Изменено

- Endpoint `POST /datasets/{dataset}/upload` теперь выполняет две операции:
  - загружает файл в raw-слой S3;
  - публикует событие о загрузке файла в Kafka.
- API-тест загрузки файла теперь дополнительно проверяет, что событие было опубликовано.
- Kafka consumer в интеграционном тесте теперь использует `auto.offset.reset=earliest`, чтобы надежно находить опубликованное событие по `event_id`.
- Добавлено ожидание partition assignment перед публикацией тестового события.
- Добавлено безопасное закрытие Kafka consumer через `finally`.
- Обновлена версия проекта до `0.7.0`.

### Проверка

- Проверено, что Kafka поднимается через Docker Compose.
- Проверено, что FastAPI после загрузки файла возвращает `event_id`.
- Проверено, что событие `file_uploaded` публикуется в topic `etl.file_uploaded`.
- Проверено, что Kafka consumer в тесте может прочитать опубликованное событие.
- Исправлена нестабильность Kafka-теста, при которой consumer мог не успеть получить partition assignment и пропустить событие.
- Проверено, что общий запуск тестов проходит успешно командой:
  - `pytest tests`.

## [0.8.0] — Kafka consumer worker для запуска quality checks

### Добавлено

- Добавлен Kafka consumer worker для обработки событий `file_uploaded`.
- Добавлен модуль `app.workers.quality_worker`.
- Добавлен класс `QualityWorker`.
- Добавлена функция `build_quality_run_id`.
- Добавлен сервис `PytestQualityRunner` в модуле `app.services.quality_runner`.
- Добавлен dataclass `QualityRunResult`.
- Добавлена функция `parse_file_uploaded_event` для преобразования Kafka message value в `FileUploadedEvent`.
- Добавлен скрипт `scripts/run_quality_worker.py` для запуска worker’а.
- В `etl_guard.local.json` добавлены Kafka-настройки worker’а:
  - `quality_worker_group`;
  - `auto_offset_reset`.
- Добавлены тесты:
  - проверка формирования команды запуска pytest;
  - проверка парсинга Kafka-события;
  - проверка генерации `run_id` на основе `event_id`.

### Изменено

- Расширен dataclass `KafkaSettings`: добавлены настройки consumer group и offset reset.
- Worker после получения события `file_uploaded` запускает quality checks через `python -m pytest tests/quality`.
- Для каждого события формируется отдельный `run_id` вида `<dataset>_<short_event_id>`.
- После успешной обработки сообщения worker вручную коммитит Kafka offset.
- Обновлена версия проекта до `0.8.0`.

### Проверка

- Проверено, что worker запускается командой:
  - `python scripts/run_quality_worker.py --once`.
- Проверено, что worker читает событие `file_uploaded` из Kafka topic `etl.file_uploaded`.
- Проверено, что после получения события worker запускает ETL/data quality проверки.
- Проверено, что pytest-плагин формирует `report.json` для события, обработанного worker’ом.
- Проверено, что общий запуск тестов проходит успешно командой:
  - `pytest tests`.

## [0.9.0] — Spark job raw CSV → silver Parquet

### Добавлено

- Добавлена зависимость `pyspark`.
- В `etl_guard.local.json` добавлен блок `lakehouse`.
- Добавлены настройки lakehouse-слоев:
  - `raw_prefix`;
  - `silver_prefix`;
  - `local_tmp_dir`.
- Добавлен dataclass `LakehouseSettings`.
- Расширен dataclass `AppSettings`: добавлен блок `lakehouse`.
- Расширен сервис `S3Storage`:
  - добавлен метод `download_file`;
  - добавлен метод `upload_file`;
  - добавлен метод `upload_directory`;
  - добавлен метод `delete_prefix`.
- Добавлен модуль `app.services.orders_spark_job`.
- Добавлен класс `OrdersSparkJob`.
- Добавлен dataclass `OrdersSparkJobResult`.
- Добавлен Spark job для обработки `orders` dataset:
  - скачивание raw CSV из S3;
  - чтение CSV через Spark;
  - явная схема входных данных;
  - фильтрация невалидных строк;
  - приведение `created_at` к date;
  - запись результата в Parquet;
  - загрузка Parquet-файлов в silver prefix в S3.
- Добавлен скрипт `scripts/run_orders_spark_job.py`.
- Зарегистрирован pytest marker `spark`.
- Добавлен Spark integration test `test_orders_spark_job_writes_silver_parquet`.

### Изменено

- Проект теперь содержит первый полноценный Spark processing step.
- Данные после raw-слоя могут быть преобразованы в silver-слой.
- Обновлена версия проекта до `0.9.0`.

### Проверка

- Проверено, что Spark job запускается командой:
  - `python scripts/run_orders_spark_job.py`.
- Проверено, что raw CSV читается из S3/MinIO.
- Проверено, что Spark job записывает результат в Parquet.
- Проверено, что Parquet-файлы загружаются в `s3://data-lake/silver/orders/`.
- Проверено, что Spark integration test проходит успешно.
- Проверено, что общий запуск тестов проходит успешно командой:
  - `pytest tests`.

## [0.10.0] — Data quality проверки silver-слоя

### Добавлено

- Зарегистрирован pytest marker `silver`.
- Добавлен файл `tests/quality/test_orders_silver.py`.
- Добавлены проверки silver-слоя `orders`:
  - проверка наличия marker-файла `_SUCCESS`;
  - проверка наличия `.parquet` файлов;
  - проверка, что silver Parquet читается через Spark;
  - проверка, что silver Parquet не пустой;
  - проверка схемы silver-данных;
  - проверка business/data quality правил.
- Добавлены ожидаемые правила схемы для `silver/orders`:
  - `order_id: int`;
  - `user_id: int`;
  - `amount: double`;
  - `status: string`;
  - `created_at: date`.
- Добавлены data quality правила для silver-слоя:
  - `order_id` не должен быть `null`;
  - `user_id` не должен быть `null`;
  - `amount` не должен быть `null`;
  - `amount` должен быть больше или равен 0;
  - `status` не должен быть `null`;
  - `status` должен входить в допустимый список: `new`, `paid`, `cancelled`.
- Добавлены helper-функции для silver-проверок:
  - `_read_silver_orders_df`;
  - `_list_silver_parquet_keys`;
  - `_list_s3_keys`.

### Изменено

- Плагин теперь поддерживает отдельную маркировку проверок silver-слоя через `@pytest.mark.silver`.
- Quality report теперь может включать проверки не только raw-слоя, но и silver-слоя.
- Обновлена версия проекта до `0.10.0`.

### Проверка

- Проверено, что после Spark job в MinIO/S3 появляется silver-слой:
  - `s3://data-lake/silver/orders/`.
- Проверено, что в silver-слое есть `_SUCCESS`.
- Проверено, что в silver-слое есть `.parquet` файлы.
- Проверено, что Parquet-файлы можно скачать из S3 и прочитать через Spark.
- Проверено, что silver-данные имеют ожидаемую схему.
- Проверено, что silver-данные проходят business/data quality правила.
- Проверено, что silver-проверки запускаются командой:
  - `pytest tests/quality -m silver`.
- Проверено, что общий запуск тестов проходит успешно командой:
  - `pytest tests`.

## [0.11.0] — Worker запускает Spark job и quality checks

### Добавлено

- Добавлен модуль `app.services.pipeline_runner`.
- Добавлен dataclass `PipelineRunResult`.
- Добавлен класс `FileUploadedPipelineRunner`.
- Добавлена orchestration-логика для события `file_uploaded`:
  - запуск Spark job `raw -> silver`;
  - запуск pytest quality checks после Spark job;
  - формирование общего результата pipeline.
- Worker теперь запускает полный pipeline после получения Kafka-события.
- Добавлен unit-тест `test_file_uploaded_pipeline_runner_runs_spark_then_quality_checks`.

### Изменено

- `QualityWorker` теперь принимает `AppSettings`, а не только `KafkaSettings`.
- `QualityWorker` теперь использует `FileUploadedPipelineRunner`.
- После получения события `file_uploaded` worker запускает:
  - `OrdersSparkJob`;
  - затем `PytestQualityRunner`.
- Для Spark job используется `raw_key` из Kafka-события.
- Silver prefix формируется по dataset:
  - `silver/<dataset>`.
- Worker теперь логирует итоговый статус pipeline:
  - dataset;
  - run_id;
  - status;
  - количество строк, прочитанных Spark;
  - количество строк, записанных в silver;
  - exit code quality checks.
- Обновлена версия проекта до `0.11.0`.

### Проверка

- Проверено, что pipeline runner сначала запускает Spark job, а затем quality checks.
- Проверено, что worker читает событие `file_uploaded` и запускает полный pipeline.
- Проверено, что Spark job создает silver Parquet.
- Проверено, что после Spark job запускаются raw и silver quality checks.
- Проверено, что pytest-плагин формирует `report.json` для запуска worker’а.
- Проверено, что общий запуск тестов проходит успешно командой:
  - `pytest tests`.

## [0.12.0] — Iceberg table поверх silver-данных

### Добавлено

- Добавлена интеграция Apache Iceberg через Spark runtime package.
- В `etl_guard.local.json` добавлены настройки Iceberg:
  - `iceberg_warehouse`;
  - `iceberg_catalog`;
  - `iceberg_namespace`.
- Расширен dataclass `LakehouseSettings`: добавлены настройки Iceberg.
- Добавлен модуль `app.services.orders_iceberg_job`.
- Добавлен класс `OrdersIcebergJob`.
- Добавлен dataclass `OrdersIcebergJobResult`.
- Добавлен Iceberg job для создания таблицы `local.analytics.orders` на основе `silver/orders` Parquet-файлов.
- Добавлен локальный Iceberg warehouse:
  - `.tmp/iceberg/warehouse`.
- Добавлен скрипт `scripts/run_orders_iceberg_job.py`.
- Зарегистрирован pytest marker `iceberg`.
- Добавлен integration test `test_orders_iceberg_job_creates_readable_table`.

### Изменено

- Проект теперь содержит Iceberg table layer поверх silver-данных.
- Silver Parquet-файлы теперь можно использовать как источник для Iceberg-таблицы.
- Обновлена версия проекта до `0.12.0`.

### Проверка

- Проверено, что Iceberg job запускается командой:
  - `python scripts/run_orders_iceberg_job.py`.
- Проверено, что SparkSession создается с Iceberg runtime package.
- Проверено, что создается namespace `local.analytics`.
- Проверено, что создается Iceberg-таблица `local.analytics.orders`.
- Проверено, что таблица читается через Spark SQL.
- Проверено, что Iceberg metadata появляется в локальном warehouse:
  - `.tmp/iceberg/warehouse`.
- Проверено, что Iceberg integration test проходит успешно.
- Проверено, что общий запуск тестов проходит успешно командой:
  - `pytest tests`.

## [0.13.0] — GitLab CI/CD и команды запуска

### Добавлено

- Добавлен файл `.gitlab-ci.yml`.
- Добавлен GitLab CI/CD pipeline со stages:
  - `lint`;
  - `test`;
  - `quality`.
- Добавлен job `lint` для проверки кода через `ruff`.
- Добавлен job `unit_tests` для запуска быстрых unit/service/plugin тестов.
- Добавлен job `quality_smoke` для smoke-проверки pytest-плагина.
- Добавлено сохранение `quality-reports/` как GitLab CI artifact.
- Добавлен `Makefile` с локальными командами:
  - `make install`;
  - `make install-dev`;
  - `make lint`;
  - `make test`;
  - `make test-ci`;
  - `make test-quality`;
  - `make test-silver`;
  - `make test-spark`;
  - `make test-iceberg`;
  - `make infra-up`;
  - `make infra-down`;
  - `make upload-sample`;
  - `make spark-job`;
  - `make iceberg-job`;
  - `make worker`.

### Изменено

- В `pyproject.toml` добавлены настройки `ruff`.
- Быстрые CI-тесты отделены от локальных integration-тестов.
- Spark, Iceberg, Kafka и MinIO тесты явно остаются локальными integration-тестами.
- Обновлена версия проекта до `0.13.0`.

### Проверка

- Проверено, что `ruff check .` запускается локально.
- Проверено, что быстрый набор тестов запускается командой:
  - `make test-ci`.
- Проверено, что GitLab CI configuration содержит stages `lint`, `test`, `quality`.
- Проверено, что `quality-reports/` сохраняется как artifact.

## [0.14.0] — Стабилизация, очистка S3 и demo-режим

### Добавлено

- Добавлен скрипт `scripts/clean_lakehouse_storage.py`.
- Добавлена очистка MinIO/S3 prefix'ов:
  - `quality-reports/`;
  - `test-artifacts/`;
  - `raw/pytester/`;
  - `raw/test/`;
  - `silver/test/`.
- Добавлен режим demo-очистки:
  - `python scripts/clean_lakehouse_storage.py --demo-reset`.
- Добавлен режим полной очистки lakehouse bucket:
  - `python scripts/clean_lakehouse_storage.py --all`.
- Добавлена очистка локальных артефактов:
  - `.tmp/`;
  - `quality-reports/`.
- Добавлен скрипт `scripts/query_orders_iceberg_table.py` для просмотра Iceberg-таблицы.
- Добавлен файл `PROJECT_MAP.md` с картой проекта.
- В `Makefile` добавлены demo-команды:
  - `make clean-storage`;
  - `make demo-reset`;
  - `make demo-prepare`;
  - `make demo-run-spark`;
  - `make demo-run-iceberg`;
  - `make demo-query-iceberg`;
  - `make demo-test-quality`;
  - `make demo-full`.

### Изменено

- Расширен демонстрационный датасет `data/orders.csv`.
- Датасет теперь содержит валидные и невалидные строки для демонстрации очистки данных.
- Проект стал удобнее для локальной демонстрации.
- Обновлена версия проекта до `0.14.0`.

### Проверка

- Проверено, что MinIO/S3 можно очистить командой:
  - `python scripts/clean_lakehouse_storage.py --demo-reset`.
- Проверено, что расширенный датасет загружается в raw-слой.
- Проверено, что Spark job обрабатывает расширенный датасет и записывает silver Parquet.
- Проверено, что Iceberg job создает таблицу `local.analytics.orders`.
- Проверено, что Iceberg-таблицу можно посмотреть командой:
  - `python scripts/query_orders_iceberg_table.py`.
- Проверено, что demo-сценарий можно запускать через Makefile.

Я начал проект с разработки собственного pytest-плагина для ETL/data quality проверок. 
На первом этапе добавил hook pytest_addoption, чтобы передавать параметры запуска через CLI: окружение, dataset и run_id. 
Через pytest_configure зарегистрировал кастомные markers, а через fixture etl_context сделал общий контекст запуска, который будет использоваться в ETL-тестах.

Во второй итерации я подключил локальное S3-compatible хранилище MinIO через Docker Compose. 
Через boto3 написал загрузку тестового raw CSV-файла в bucket data-lake. 
Затем расширил свой pytest-плагин: добавил S3 CLI-опции, fixture s3_client и marker s3. 
После этого написал первые data quality тесты: проверку существования объекта в S3, проверку непустого файла и проверку обязательных колонок CSV.

На третьей итерации я расширил pytest-плагин и добавил сбор quality report. 
Через hook pytest_runtest_makereport я перехватываю результат каждого ETL-теста: passed, failed, skipped, duration, markers и ошибку при падении. 
Через hook pytest_sessionfinish в конце pytest-сессии формирую общий report.json с run_id, dataset, окружением, S3-настройками, summary и списком всех проверок.

На четвертой итерации я добавил загрузку quality report в S3.
Плагин через pytest_sessionfinish формирует report.json, сохраняет его локально и при включенной CLI-опции загружает в MinIO/S3 через boto3.put_object.
Также я добавил pytester-тест, который проверяет работу плагина как пользовательского инструмента: создает временный тест, запускает pytest, проверяет генерацию отчета, загрузку в S3 и чтение отчета обратно через boto3.get_object.

На пятой итерации я упростил запуск плагина и сделал рефакторинг. Вместо длинной команды с большим количеством CLI-флагов добавил конфигурационный файл etl_guard.local.json, а run_id теперь генерируется автоматически. CLI-флаги остались, но теперь они нужны только для переопределения настроек. Также я разнес код по модулям: config.py, s3.py, reporting.py, а plugin.py оставил как точку входа для pytest hooks и fixtures.

На шестой итерации я добавил FastAPI-слой. Реализовал endpoint для загрузки CSV-файлов в raw-слой S3 и endpoint для просмотра объектов по dataset. Внутри API используется отдельный S3Storage-сервис на boto3, а настройки берутся из etl_guard.local.json. Также я добавил API-тесты через TestClient, которые проверяют healthcheck, загрузку файла в MinIO/S3 и получение списка объектов.

На седьмой итерации я добавил Kafka и сделал публикацию события после загрузки файла. Теперь FastAPI после сохранения CSV в S3 отправляет событие file_uploaded в topic etl.file_uploaded. Для этого я добавил Kafka в Docker Compose, подключил confluent-kafka, сделал сервис KafkaEventPublisher и написал интеграционный тест, который через consumer проверяет, что событие реально попало в Kafka.

На восьмой итерации я добавил Kafka consumer worker. Теперь после того как FastAPI публикует событие file_uploaded, worker читает это событие из Kafka и запускает quality checks через python -m pytest. Для каждого события формируется отдельный run_id, а результат проверок сохраняется через уже существующий pytest-плагин в виде report.json локально и в S3.

На девятой итерации я добавил Spark job для обработки данных. Он берет raw/orders/orders.csv из S3/MinIO, читает его через PySpark, очищает данные, фильтрует невалидные строки и записывает результат в Parquet. После этого Parquet-файлы загружаются обратно в S3 в silver/orders/. Это первый полноценный шаг обработки данных в pipeline: raw CSV → silver Parquet.

На десятой итерации я добавил data quality проверки silver-слоя. Теперь pytest-плагин проверяет не только raw CSV, но и результат Spark job в silver/orders/: наличие _SUCCESS, наличие Parquet-файлов, читаемость через Spark, корректную схему и бизнес-правила качества данных. Это делает pipeline ближе к реальному ETL-процессу, где важно валидировать не только входные данные, но и результат обработки.

На одиннадцатой итерации я сделал worker полноценным оркестратором pipeline. Теперь после Kafka-события file_uploaded он запускает Spark job raw → silver, а потом запускает pytest quality checks. То есть цепочка стала полной: загрузка файла → Kafka event → worker → Spark обработка → проверки качества → report.json в S3.

На двенадцатой итерации я добавил Iceberg. Spark job раньше писал результат в silver/orders/ как Parquet-файлы, а теперь отдельный Iceberg job создает на их основе таблицу local.analytics.orders. Для этого я настроил Spark Iceberg runtime, Hadoop catalog и локальный Iceberg warehouse. Таблица читается через Spark SQL, а integration test проверяет, что Iceberg-таблица создается и содержит данные.

На тринадцатой итерации я добавил GitLab CI/CD. Pipeline состоит из stages lint, test и quality: проверка кода через ruff, быстрые unit/plugin/service тесты и smoke-проверка pytest-плагина с сохранением quality report как artifact. Также я добавил Makefile, чтобы локально запускать инфраструктуру, Spark job, Iceberg job и тесты короткими командами.