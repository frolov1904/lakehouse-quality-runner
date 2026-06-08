import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CONFIG = {
    "etl_env": "local",
    "dataset": "orders",
    "s3": {
        "endpoint": "http://localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "bucket": "data-lake",
    },
    "quality_report": {
        "local_dir": "quality-reports",
        "upload_to_s3": False,
        "s3_prefix": "quality-reports",
    },
}


def add_etl_guard_options(parser):
    """
    Регистрирует CLI-опции pytest-плагина.

    Теперь большинство CLI-опций необязательные:
    если пользователь не передал их руками, значения берутся из
    etl_guard.local.json или из DEFAULT_CONFIG.
    """
    group = parser.getgroup("etl-guard")

    group.addoption(
        "--etl-config",
        action="store",
        default="etl_guard.local.json",
        help="Path to ETL Guard config file",
    )

    group.addoption(
        "--etl-env",
        action="store",
        default=None,
        help="Environment for ETL checks: local, dev, stage, prod",
    )

    group.addoption(
        "--dataset",
        action="store",
        default=None,
        help="Dataset name for ETL checks, for example: orders, users, payments",
    )

    group.addoption(
        "--run-id",
        action="store",
        default=None,
        help="Pipeline run id. If not provided, it will be generated automatically",
    )

    group.addoption(
        "--s3-endpoint",
        action="store",
        default=None,
        help="S3-compatible endpoint, for example: http://localhost:9000",
    )

    group.addoption(
        "--s3-access-key",
        action="store",
        default=None,
        help="S3 access key",
    )

    group.addoption(
        "--s3-secret-key",
        action="store",
        default=None,
        help="S3 secret key",
    )

    group.addoption(
        "--s3-bucket",
        action="store",
        default=None,
        help="S3 bucket name for ETL checks",
    )

    group.addoption(
        "--quality-report-dir",
        action="store",
        default=None,
        help="Local directory for ETL quality reports",
    )

    group.addoption(
        "--upload-quality-report-to-s3",
        action="store_true",
        default=None,
        help="Upload generated quality report to S3-compatible storage",
    )

    group.addoption(
        "--quality-report-s3-prefix",
        action="store",
        default=None,
        help="S3 prefix for uploaded ETL quality reports",
    )


def register_etl_guard_markers(config):
    """
    Регистрирует пользовательские markers плагина.
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
    config.addinivalue_line(
        "markers",
        "spark: mark test as Spark-related check",
    )
    config.addinivalue_line(
        "markers",
        "silver: mark test as silver layer quality check",
    )
    config.addinivalue_line(
        "markers",
        "iceberg: mark test as Iceberg-related check",
    )


def resolve_etl_guard_config(pytest_config):
    """
    Собирает итоговую конфигурацию плагина.

    Приоритет:
    1. CLI-опции pytest;
    2. etl_guard.local.json;
    3. DEFAULT_CONFIG.

    Также здесь генерируется run_id, если пользователь не передал его руками.
    """
    file_config = _load_config_file(
        pytest_config.getoption("--etl-config")
    )

    dataset = _resolve_value(
        cli_value=pytest_config.getoption("--dataset"),
        file_value=file_config.get("dataset"),
        default_value=DEFAULT_CONFIG["dataset"],
    )

    run_id = _resolve_value(
        cli_value=pytest_config.getoption("--run-id"),
        file_value=file_config.get("run_id"),
        default_value=None,
    )

    if run_id is None:
        run_id = _generate_run_id(dataset)

    resolved_config = {
        "env": _resolve_value(
            cli_value=pytest_config.getoption("--etl-env"),
            file_value=file_config.get("etl_env"),
            default_value=DEFAULT_CONFIG["etl_env"],
        ),
        "dataset": dataset,
        "run_id": run_id,
        "s3": {
            "endpoint": _resolve_value(
                cli_value=pytest_config.getoption("--s3-endpoint"),
                file_value=file_config.get("s3", {}).get("endpoint"),
                default_value=DEFAULT_CONFIG["s3"]["endpoint"],
            ),
            "access_key": _resolve_value(
                cli_value=pytest_config.getoption("--s3-access-key"),
                file_value=file_config.get("s3", {}).get("access_key"),
                default_value=DEFAULT_CONFIG["s3"]["access_key"],
            ),
            "secret_key": _resolve_value(
                cli_value=pytest_config.getoption("--s3-secret-key"),
                file_value=file_config.get("s3", {}).get("secret_key"),
                default_value=DEFAULT_CONFIG["s3"]["secret_key"],
            ),
            "bucket": _resolve_value(
                cli_value=pytest_config.getoption("--s3-bucket"),
                file_value=file_config.get("s3", {}).get("bucket"),
                default_value=DEFAULT_CONFIG["s3"]["bucket"],
            ),
        },
        "quality_report": {
            "local_dir": _resolve_value(
                cli_value=pytest_config.getoption("--quality-report-dir"),
                file_value=file_config.get("quality_report", {}).get("local_dir"),
                default_value=DEFAULT_CONFIG["quality_report"]["local_dir"],
            ),
            "upload_to_s3": _resolve_value(
                cli_value=pytest_config.getoption("--upload-quality-report-to-s3"),
                file_value=file_config.get("quality_report", {}).get("upload_to_s3"),
                default_value=DEFAULT_CONFIG["quality_report"]["upload_to_s3"],
            ),
            "s3_prefix": _resolve_value(
                cli_value=pytest_config.getoption("--quality-report-s3-prefix"),
                file_value=file_config.get("quality_report", {}).get("s3_prefix"),
                default_value=DEFAULT_CONFIG["quality_report"]["s3_prefix"],
            ),
        },
    }

    pytest_config._etl_guard_config = resolved_config

    return resolved_config


def get_etl_guard_config(pytest_config):
    """
    Возвращает уже собранную конфигурацию.

    Если по какой-то причине она еще не была собрана,
    собирает ее лениво.
    """
    if not hasattr(pytest_config, "_etl_guard_config"):
        return resolve_etl_guard_config(pytest_config)

    return pytest_config._etl_guard_config


def build_etl_context(pytest_config):
    """
    Собирает общий ETL-контекст для fixture etl_context.
    """
    return get_etl_guard_config(pytest_config)


def _load_config_file(config_path):
    """
    Загружает JSON-конфиг.

    Если файла нет, возвращает пустой словарь.
    Это позволяет запускать плагин даже без etl_guard.local.json.
    """
    path = Path(config_path)

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _resolve_value(cli_value, file_value, default_value):
    """
    Выбирает итоговое значение по приоритету:
    CLI → config file → default.
    """
    if cli_value is not None:
        return cli_value

    if file_value is not None:
        return file_value

    return default_value


def _generate_run_id(dataset):
    """
    Генерирует run_id для запуска.

    Пример:
    orders_20260607_221530
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_dataset = dataset.replace("/", "_").replace(" ", "_")

    return f"{safe_dataset}_{timestamp}"