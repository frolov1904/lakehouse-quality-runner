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