import pytest


@pytest.mark.etl
@pytest.mark.quality
def test_etl_context_is_created(etl_context):
    """
    Проверяем, что pytest-плагин создает общий ETL-контекст.
    """
    assert etl_context["env"] == "local"
    assert etl_context["dataset"] == "orders"
    assert etl_context["run_id"] == "run_001"

    assert etl_context["s3"]["endpoint"] == "http://localhost:9000"
    assert etl_context["s3"]["bucket"] == "data-lake"