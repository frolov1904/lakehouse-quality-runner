import csv
from io import StringIO

import pytest
from botocore.exceptions import ClientError


ORDERS_RAW_KEY = "raw/orders/orders.csv"

REQUIRED_COLUMNS = {
    "order_id",
    "user_id",
    "amount",
    "status",
    "created_at",
}


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.s3
def test_orders_raw_file_exists(s3_client, s3_bucket):
    """
    Проверяем, что raw-файл с заказами существует в S3.

    Это базовая ETL-проверка: если входного файла нет,
    pipeline не сможет обработать данные.
    """
    response = s3_client.head_object(      #head_object используется для получения метаданных объекта, не загружая его содержимое
        Bucket=s3_bucket,
        Key=ORDERS_RAW_KEY,
    )

    assert response["ContentLength"] > 0


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.s3
def test_orders_raw_file_is_not_empty(s3_client, s3_bucket):
    """
    Проверяем, что файл не пустой.
    """
    response = s3_client.get_object(
        Bucket=s3_bucket,
        Key=ORDERS_RAW_KEY,
    )

    content = response["Body"].read().decode("utf-8")

    assert content.strip() != ""


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.s3
def test_orders_raw_file_has_required_columns(s3_client, s3_bucket):
    """
    Проверяем, что CSV содержит обязательные колонки.

    Для ETL это важная проверка контракта данных:
    если источник прислал файл без нужных колонок,
    обработка может сломаться или дать неправильный результат.
    """
    response = s3_client.get_object(
        Bucket=s3_bucket,
        Key=ORDERS_RAW_KEY,
    )

    content = response["Body"].read().decode("utf-8")

    csv_reader = csv.DictReader(StringIO(content))
    actual_columns = set(csv_reader.fieldnames or [])

    missing_columns = REQUIRED_COLUMNS - actual_columns

    assert not missing_columns, (
        f"В файле отсутствуют обязательные колонки: {sorted(missing_columns)}"
    )