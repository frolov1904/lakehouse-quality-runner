import pytest
import boto3


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


def pytest_configure(config):
    """
    pytest_configure — hook pytest.

    Регистрирует пользовательские markers.
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


@pytest.fixture
def etl_context(request):
    """
    Общий контекст ETL-запуска.

    """
    return {
        "env": request.config.getoption("--etl-env"),
        "dataset": request.config.getoption("--dataset"),
        "run_id": request.config.getoption("--run-id"),
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