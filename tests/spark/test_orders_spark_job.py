from uuid import uuid4

import boto3
import pytest

from app.core.settings import load_settings
from app.services.orders_spark_job import OrdersSparkJob


@pytest.mark.spark
def test_orders_spark_job_writes_silver_parquet():
    """
    Проверяем полный сценарий Spark job:

    1. Кладем raw CSV в MinIO/S3.
    2. Spark job скачивает raw CSV.
    3. Spark job обрабатывает данные.
    4. Spark job пишет локальный Parquet.
    5. Spark job загружает Parquet в silver prefix в S3.
    """
    settings = load_settings()

    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.s3.endpoint,
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )

    raw_key = "raw/orders/orders.csv"

    s3_client.put_object(
        Bucket=settings.s3.bucket,
        Key=raw_key,
        Body=(
            b"order_id,user_id,amount,status,created_at\n"
            b"1,101,1500.50,paid,2026-06-01\n"
            b"2,102,700.00,paid,2026-06-01\n"
            b"3,103,-10.00,paid,2026-06-02\n"
            b"4,,250.00,new,2026-06-02\n"
            b"5,105,300.00,unknown,2026-06-02\n"
        ),
        ContentType="text/csv",
    )

    silver_prefix = f"silver/test/orders/{uuid4()}"

    job = OrdersSparkJob(
        settings=settings,
        run_id=f"test_spark_{uuid4()}",
    )

    result = job.run(
        raw_key=raw_key,
        silver_prefix=silver_prefix,
    )

    assert result.rows_read == 5
    assert result.rows_written == 2

    response = s3_client.list_objects_v2(
        Bucket=settings.s3.bucket,
        Prefix=silver_prefix,
    )

    uploaded_keys = [
        item["Key"]
        for item in response.get("Contents", [])
    ]

    assert uploaded_keys
    assert any(key.endswith(".parquet") for key in uploaded_keys)