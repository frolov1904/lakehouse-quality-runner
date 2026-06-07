import pytest

from pytest_etl_guard.config import (
    add_etl_guard_options,
    build_etl_context,
    get_etl_guard_config,
    register_etl_guard_markers,
    resolve_etl_guard_config,
)
from pytest_etl_guard.reporting import (
    build_quality_report,
    build_report_path,
    build_report_s3_key,
    report_to_json,
    save_report_locally,
    utc_now,
)
from pytest_etl_guard.s3 import build_s3_client, upload_report_to_s3


def pytest_addoption(parser):
    """
    pytest_addoption — hook pytest.

    Делегируем регистрацию CLI-опций в отдельный модуль config.py.
    """
    add_etl_guard_options(parser)


def pytest_configure(config):
    """
    pytest_configure — hook pytest.

    Регистрирует markers, собирает итоговую конфигурацию
    и подготавливает внутреннее состояние плагина.
    """
    register_etl_guard_markers(config)
    resolve_etl_guard_config(config)

    config._etl_guard_started_at = utc_now()
    config._etl_guard_results = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest_runtest_makereport — hook pytest.

    Перехватывает результат выполнения каждого ETL/data quality теста.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    marker_names = [marker.name for marker in item.iter_markers()]

    if "etl" not in marker_names and "quality" not in marker_names:
        return

    test_result = {
        "nodeid": report.nodeid,
        "name": item.name,
        "outcome": report.outcome,
        "duration": round(report.duration, 6),
        "markers": marker_names,
    }

    if report.failed:
        test_result["error"] = str(report.longrepr)

    item.config._etl_guard_results.append(test_result)


def pytest_sessionfinish(session, exitstatus):
    """
    pytest_sessionfinish — hook pytest.

    В конце pytest-сессии:
    1. собирает общий quality report;
    2. сохраняет его локально;
    3. при включенной опции загружает report.json в S3/MinIO.
    """
    config = session.config
    etl_config = get_etl_guard_config(config)
    results = getattr(config, "_etl_guard_results", [])

    report = build_quality_report(
        config=config,
        exitstatus=exitstatus,
        results=results,
    )

    report_json = report_to_json(report)
    local_report_path = build_report_path(config)

    save_report_locally(local_report_path, report_json)

    print(f"\nETL Guard quality report: {local_report_path}")

    if etl_config["quality_report"]["upload_to_s3"]:
        s3_report_key = build_report_s3_key(config)

        upload_report_to_s3(
            config=config,
            s3_key=s3_report_key,
            report_json=report_json,
        )

        bucket = etl_config["s3"]["bucket"]
        print(f"ETL Guard quality report uploaded: s3://{bucket}/{s3_report_key}")


@pytest.fixture
def etl_context(request):
    """
    Общий контекст ETL-запуска.
    """
    return build_etl_context(request.config)


@pytest.fixture
def s3_client(request):
    """
    S3-клиент для ETL/data quality тестов.
    """
    return build_s3_client(request.config)


@pytest.fixture
def s3_bucket(request):
    """
    Название bucket, с которым работают ETL-проверки.
    """
    etl_config = get_etl_guard_config(request.config)
    return etl_config["s3"]["bucket"]