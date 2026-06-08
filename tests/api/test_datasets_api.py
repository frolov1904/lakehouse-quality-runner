import boto3
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
    Проверяем полный сценарий загрузки файла через API:

    1. Отправляем CSV-файл в FastAPI.
    2. FastAPI загружает его в MinIO/S3.
    3. Через boto3 проверяем, что объект реально появился в bucket.
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