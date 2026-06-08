from app.services.kafka_events import FileUploadedEvent
from app.workers.quality_worker import build_quality_run_id


def test_build_quality_run_id():
    """
    Проверяем генерацию run_id для quality checks на основе Kafka event_id.
    """
    event = FileUploadedEvent(
        event_id="71c6b017-e6d0-43c1-bb73-71164d597b55",
        event_type="file_uploaded",
        dataset="orders",
        bucket="data-lake",
        key="raw/orders/orders.csv",
        filename="orders.csv",
        content_type="text/csv",
        occurred_at="2026-06-08T07:00:00+00:00",
    )

    run_id = build_quality_run_id(event)

    assert run_id == "orders_71c6b017"