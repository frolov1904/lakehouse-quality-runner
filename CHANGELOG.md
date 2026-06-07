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