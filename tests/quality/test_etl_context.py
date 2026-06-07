import pytest


@pytest.mark.etl
@pytest.mark.quality
def test_etl_context_is_created(etl_context):
    """
    Проверяем, что наш pytest-плагин:
    1. загрузился;
    2. добавил fixture etl_context;
    3. передал в тест значения из CLI-опций.
    """
    assert etl_context["env"] == "local"
    assert etl_context["dataset"] == "orders"
    assert etl_context["run_id"] == "run_001"