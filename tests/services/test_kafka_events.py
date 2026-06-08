import json

from app.services.kafka_events import parse_file_uploaded_event


def test_parse_file_uploaded_event():
    """
    Проверяем преобразование Kafka message value в FileUploadedEvent.
    """
    payload = {
        "event_id": "123",
        "event_type": "file_uploaded",
        "dataset": "orders",
        "bucket": "data-lake",
        "key": "raw/orders/orders.csv",
        "filename": "orders.csv",
        "content_type": "text/csv",
        "occurred_at": "2026-06-08T07:00:00+00:00",
    }

    event = parse_file_uploaded_event(
        json.dumps(payload).encode("utf-8")
    )

    assert event.event_id == "123"
    assert event.event_type == "file_uploaded"
    assert event.dataset == "orders"
    assert event.bucket == "data-lake"
    assert event.key == "raw/orders/orders.csv"
    assert event.filename == "orders.csv"
    assert event.content_type == "text/csv"
    assert event.occurred_at == "2026-06-08T07:00:00+00:00"