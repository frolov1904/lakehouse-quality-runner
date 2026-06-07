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