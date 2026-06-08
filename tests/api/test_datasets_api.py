import json
import time
from uuid import uuid4

import boto3
from confluent_kafka import Consumer
from confluent_kafka.admin import AdminClient, NewTopic
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
FILE_UPLOADED_TOPIC = "etl.file_uploaded"


def test_health_check():
    """
    Проверяем, что FastAPI-приложение запускается и healthcheck работает.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "lakehouse-quality-runner",
    }


def test_upload_dataset_file_to_s3():
    """
    Проверяем загрузку файла через API в MinIO/S3.
    """
    filename = "orders_api_test.csv"
    content = (
        b"order_id,user_id,amount,status,created_at\n"
        b"1,101,1500.50,paid,2026-06-01\n"
    )

    response = client.post(
        "/datasets/orders/upload",
        files={
            "file": (
                filename,
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["dataset"] == "orders"
    assert body["bucket"] == "data-lake"
    assert body["key"] == f"raw/orders/{filename}"
    assert body["status"] == "uploaded"
    assert body["event"]["published"] is True
    assert body["event"]["topic"] == FILE_UPLOADED_TOPIC
    assert body["event"]["event_id"] is not None

    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )

    s3_response = s3_client.head_object(
        Bucket="data-lake",
        Key=f"raw/orders/{filename}",
    )

    assert s3_response["ContentLength"] > 0


def test_upload_dataset_file_publishes_kafka_event():
    """
    Проверяем полный сценарий:

    1. Создаем consumer.
    2. Загружаем файл через FastAPI.
    3. FastAPI кладет файл в S3.
    4. FastAPI публикует событие в Kafka.
    5. Consumer читает событие из Kafka.
    6. Проверяем содержимое события.
    """
    _ensure_topic_exists(FILE_UPLOADED_TOPIC)

    group_id = f"test-group-{uuid4()}"
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    consumer.subscribe([FILE_UPLOADED_TOPIC])
    _wait_until_consumer_assigned(consumer)

    try:
        filename = f"orders_kafka_test_{uuid4()}.csv"
        content = (
            b"order_id,user_id,amount,status,created_at\n"
            b"1,101,1500.50,paid,2026-06-01\n"
        )

        response = client.post(
            "/datasets/orders/upload",
            files={
                "file": (
                    filename,
                    content,
                    "text/csv",
                )
            },
        )

        assert response.status_code == 200

        body = response.json()
        expected_event_id = body["event"]["event_id"]

        event = _poll_event_by_id(
            consumer=consumer,
            expected_event_id=expected_event_id,
            timeout_seconds=10,
        )

    finally:
        consumer.close()

    assert event["event_id"] == expected_event_id
    assert event["event_type"] == "file_uploaded"
    assert event["dataset"] == "orders"
    assert event["bucket"] == "data-lake"
    assert event["key"] == f"raw/orders/{filename}"
    assert event["filename"] == filename
    assert event["content_type"] == "text/csv"
    assert event["occurred_at"]


def test_list_dataset_objects():
    """
    Проверяем, что API умеет показывать объекты raw-слоя по dataset.
    """
    response = client.get("/datasets/orders/objects")

    assert response.status_code == 200

    body = response.json()

    assert body["dataset"] == "orders"
    assert body["bucket"] == "data-lake"
    assert body["prefix"] == "raw/orders/"
    assert isinstance(body["objects"], list)


def _ensure_topic_exists(topic_name: str) -> None:
    """
    Создает Kafka topic, если он еще не существует.
    """
    admin = AdminClient(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        }
    )

    futures = admin.create_topics(
        [
            NewTopic(
                topic=topic_name,
                num_partitions=1,
                replication_factor=1,
            )
        ]
    )

    for _, future in futures.items():
        try:
            future.result(timeout=5)
        except Exception as error:
            # Если topic уже существует, это не ошибка для теста.
            if "already exists" not in str(error).lower():
                raise


def _poll_event_by_id(
    consumer: Consumer,
    expected_event_id: str,
    timeout_seconds: int,
) -> dict:
    """
    Читает сообщения из Kafka, пока не найдет событие с нужным event_id.
    """
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        message = consumer.poll(0.5)

        if message is None:
            continue

        if message.error():
            continue

        event = json.loads(message.value().decode("utf-8"))

        if event.get("event_id") == expected_event_id:
            return event

    raise AssertionError(
        f"Не удалось найти Kafka event с event_id={expected_event_id}"
    )
    
def _wait_until_consumer_assigned(
    consumer: Consumer,
    timeout_seconds: int = 5,
) -> None:
    """
    Ждем, пока Kafka назначит consumer'у partition.

    Это нужно, чтобы тест не был flaky: если сразу после subscribe
    отправить событие, consumer может еще не успеть подключиться к partition.
    """
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        consumer.poll(0.2)

        if consumer.assignment():
            return

    raise AssertionError("Kafka consumer не получил partition assignment")