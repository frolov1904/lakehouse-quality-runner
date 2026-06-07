import pytest


def pytest_addoption(parser):
    """
    pytest_addoption — хук для добавления собственных параметров командной строки.

    После этого мы сможем запускать pytest так:

    pytest --etl-env=local --dataset=orders --run-id=run_001
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


def pytest_configure(config):
    """
    pytest_configure — хук, который вызывается при настройке pytest.

    Здесь мы регистрируем свои markers:

    @pytest.mark.etl
    @pytest.mark.quality
    """
    config.addinivalue_line(
        "markers",
        "etl: mark test as ETL-related check",
    )

    config.addinivalue_line(
        "markers",
        "quality: mark test as data quality check",
    )


@pytest.fixture
def etl_context(request):
    """
    etl_context — это фикстура плагина.

    Она собирает параметры запуска ETL-проверок в один словарь.

    """
    return {
        "env": request.config.getoption("--etl-env"),
        "dataset": request.config.getoption("--dataset"),
        "run_id": request.config.getoption("--run-id"),
    }