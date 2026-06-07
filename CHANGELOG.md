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