import json
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pytest


def pytest_addoption(parser):
    """
    pytest_addoption — hook pytest.

    Добавляет пользовательские CLI-опции для ETL/data quality запусков.
    """
    group = parser.getgroup("etl-guard")

    group.addoption(
        "--etl-env",
        action="store",
        default="local",
        help="Environment for ETL checks: local, dev, stage, prod",
    )

    group.addoption(
        "--dataset",
        action="store",
        default="orders",
        help="Dataset name for ETL checks, for example: orders, users, payments",
    )

    group.addoption(
        "--run-id",
        action="store",
        default="local-run",
        help="Pipeline run id for grouping quality checks",
    )

    group.addoption(
        "--s3-endpoint",
        action="store",
        default="http://localhost:9000",
        help="S3-compatible endpoint, for example: http://localhost:9000",
    )

    group.addoption(
        "--s3-access-key",
        action="store",
        default="minioadmin",
        help="S3 access key",
    )

    group.addoption(
        "--s3-secret-key",
        action="store",
        default="minioadmin",
        help="S3 secret key",
    )

    group.addoption(
        "--s3-bucket",
        action="store",
        default="data-lake",
        help="S3 bucket name for ETL checks",
    )

    group.addoption(
        "--quality-report-dir",
        action="store",
        default="quality-reports",
        help="Local directory for ETL quality reports",
    )


def pytest_configure(config):
    """
    pytest_configure — hook pytest.

    Регистрирует пользовательские markers и подготавливает место
    для хранения результатов ETL-проверок.
    """
    config.addinivalue_line(
        "markers",
        "etl: mark test as ETL-related check",
    )

    config.addinivalue_line(
        "markers",
        "quality: mark test as data quality check",
    )

    config.addinivalue_line(
        "markers",
        "s3: mark test as S3-related check",
    )

    # Здесь мы создаем внутренние поля плагина.
    # В них будем собирать результаты тестов во время запуска pytest.
    config._etl_guard_started_at = _utc_now()
    config._etl_guard_results = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest_runtest_makereport — hook pytest.

    Он вызывается при формировании отчета по каждому тесту.

    Нам важно перехватить результат test call:
    - passed
    - failed
    - skipped

    hookwrapper=True нужен, чтобы сначала дать pytest сформировать
    стандартный отчет, а потом получить его через outcome.get_result().
    """
    outcome = yield
    report = outcome.get_result()

    # У одного теста есть несколько фаз:
    # setup — подготовка
    # call — сам тест
    # teardown — завершение
    #
    # Нас интересует именно call, чтобы не записывать один тест три раза.
    if report.when != "call":
        return

    marker_names = [marker.name for marker in item.iter_markers()]

    # В quality report включаем только тесты, которые относятся к нашему ETL-плагину.
    # Обычные unit-тесты проекта сюда попадать не должны.
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

    Он вызывается один раз в самом конце запуска pytest.

    Здесь мы собираем общий отчет:
    - параметры запуска;
    - список тестов;
    - summary;
    - время старта и завершения;
    - exitstatus pytest.

    После этого сохраняем report.json локально.
    """
    config = session.config

    results = getattr(config, "_etl_guard_results", [])

    report = {
        "run_id": config.getoption("--run-id"),
        "dataset": config.getoption("--dataset"),
        "env": config.getoption("--etl-env"),
        "started_at": getattr(config, "_etl_guard_started_at", None),
        "finished_at": _utc_now(),
        "exitstatus": exitstatus,
        "s3": {
            "endpoint": config.getoption("--s3-endpoint"),
            "bucket": config.getoption("--s3-bucket"),
        },
        "summary": _build_summary(results),
        "tests": results,
    }

    report_path = _build_report_path(config)

    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nETL Guard quality report: {report_path}")


@pytest.fixture
def etl_context(request):
    """
    Общий контекст ETL-запуска.

    В следующих итерациях сюда можно будет добавить Kafka, Spark, Iceberg
    и другие настройки.
    """
    return {
        "env": request.config.getoption("--etl-env"),
        "dataset": request.config.getoption("--dataset"),
        "run_id": request.config.getoption("--run-id"),
        "quality_report_dir": request.config.getoption("--quality-report-dir"),
        "s3": {
            "endpoint": request.config.getoption("--s3-endpoint"),
            "bucket": request.config.getoption("--s3-bucket"),
        },
    }


@pytest.fixture
def s3_client(request):
    """
    S3-клиент для тестов.

    Сейчас он подключается к локальному MinIO, но в будущем через эти же
    параметры можно подключаться к любому S3-compatible хранилищу.
    """
    return boto3.client(
        "s3",
        endpoint_url=request.config.getoption("--s3-endpoint"),
        aws_access_key_id=request.config.getoption("--s3-access-key"),
        aws_secret_access_key=request.config.getoption("--s3-secret-key"),
    )


@pytest.fixture
def s3_bucket(request):
    """
    Название bucket, с которым работают ETL-проверки.
    """
    return request.config.getoption("--s3-bucket")


def _build_summary(results):
    """
    Считает краткую статистику по результатам ETL-проверок.
    """
    return {
        "total": len(results),
        "passed": sum(1 for result in results if result["outcome"] == "passed"),
        "failed": sum(1 for result in results if result["outcome"] == "failed"),
        "skipped": sum(1 for result in results if result["outcome"] == "skipped"),
    }


def _build_report_path(config):
    """
    Формирует путь к локальному report.json.

    Например:
    quality-reports/run_001/report.json
    """
    report_dir = Path(config.getoption("--quality-report-dir"))
    run_id = config.getoption("--run-id")

    safe_run_id = run_id.replace("/", "_").replace(" ", "_")

    return report_dir / safe_run_id / "report.json"


def _utc_now():
    """
    Возвращает текущее время в UTC в ISO-формате.
    """
    return datetime.now(timezone.utc).isoformat()