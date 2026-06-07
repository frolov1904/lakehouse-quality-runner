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

    group.addoption(
        "--upload-quality-report-to-s3",
        action="store_true",
        default=False,
        help="Upload generated quality report to S3-compatible storage",
    )

    group.addoption(
        "--quality-report-s3-prefix",
        action="store",
        default="quality-reports",
        help="S3 prefix for uploaded ETL quality reports",
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

    config._etl_guard_started_at = _utc_now()
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

    results = getattr(config, "_etl_guard_results", [])

    local_report_path = _build_report_path(config)
    s3_report_key = _build_report_s3_key(config)

    upload_to_s3 = config.getoption("--upload-quality-report-to-s3")

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
        "quality_report": {
            "local_path": str(local_report_path),
            "upload_to_s3": upload_to_s3,
            "s3_key": s3_report_key if upload_to_s3 else None,
        },
        "summary": _build_summary(results),
        "tests": results,
    }

    report_json = json.dumps(report, ensure_ascii=False, indent=2)

    _save_report_locally(local_report_path, report_json)

    print(f"\nETL Guard quality report: {local_report_path}")

    if upload_to_s3:
        _upload_report_to_s3(config, s3_report_key, report_json)
        bucket = config.getoption("--s3-bucket")
        print(f"ETL Guard quality report uploaded: s3://{bucket}/{s3_report_key}")


@pytest.fixture
def etl_context(request):
    """
    Общий контекст ETL-запуска.

    Содержит параметры окружения, dataset, run_id, настройки S3
    и настройки quality report.
    """
    return {
        "env": request.config.getoption("--etl-env"),
        "dataset": request.config.getoption("--dataset"),
        "run_id": request.config.getoption("--run-id"),
        "quality_report_dir": request.config.getoption("--quality-report-dir"),
        "quality_report_s3_prefix": request.config.getoption(
            "--quality-report-s3-prefix"
        ),
        "upload_quality_report_to_s3": request.config.getoption(
            "--upload-quality-report-to-s3"
        ),
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
    return _build_s3_client(request.config)


@pytest.fixture
def s3_bucket(request):
    """
    Название bucket, с которым работают ETL-проверки.
    """
    return request.config.getoption("--s3-bucket")


def _build_s3_client(config):
    """
    Создает boto3 S3 client на основе pytest CLI-опций.

    Важно: эту функцию можно использовать и внутри fixture,
    и внутри pytest_sessionfinish, где fixture напрямую недоступны.
    """
    return boto3.client(
        "s3",
        endpoint_url=config.getoption("--s3-endpoint"),
        aws_access_key_id=config.getoption("--s3-access-key"),
        aws_secret_access_key=config.getoption("--s3-secret-key"),
    )


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

    safe_run_id = _make_safe_path_part(run_id)

    return report_dir / safe_run_id / "report.json"


def _build_report_s3_key(config):
    """
    Формирует S3 key для quality report.

    Например:
    quality-reports/run_001/report.json
    """
    prefix = config.getoption("--quality-report-s3-prefix")
    run_id = config.getoption("--run-id")

    clean_prefix = prefix.strip("/")
    safe_run_id = _make_safe_path_part(run_id)

    return f"{clean_prefix}/{safe_run_id}/report.json"


def _save_report_locally(report_path, report_json):
    """
    Сохраняет report.json на локальный диск.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_json, encoding="utf-8")


def _upload_report_to_s3(config, s3_key, report_json):
    """
    Загружает report.json в S3-compatible хранилище.

    Используем put_object, потому что отчет уже есть в памяти как строка.
    """
    s3_client = _build_s3_client(config)
    bucket = config.getoption("--s3-bucket")

    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=report_json.encode("utf-8"),
        ContentType="application/json",
    )


def _make_safe_path_part(value):
    """
    Делает значение безопасным для использования в локальном пути и S3 key.
    """
    return value.replace("/", "_").replace(" ", "_")


def _utc_now():
    """
    Возвращает текущее время в UTC в ISO-формате.
    """
    return datetime.now(timezone.utc).isoformat()