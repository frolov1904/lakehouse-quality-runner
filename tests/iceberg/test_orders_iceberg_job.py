from uuid import uuid4

import boto3
import pytest

from app.core.settings import load_settings
from app.services.orders_iceberg_job import OrdersIcebergJob
from app.services.orders_spark_job import OrdersSparkJob


@pytest.mark.iceberg
def test_orders_iceberg_job_creates_readable_table():
    """
    Проверяем Iceberg job:

    1. Создаем SparkSession сразу с Iceberg runtime.
    2. Через эту же SparkSession готовим silver Parquet.
    3. Через эту же SparkSession создаем Iceberg table.
    4. Проверяем, что таблица создана и содержит строки.
    """
    settings = load_settings()
    run_id = f"test_iceberg_{uuid4()}"

    iceberg_job_for_session = OrdersIcebergJob(
        settings=settings,
        run_id=run_id,
    )

    spark = iceberg_job_for_session._build_spark_session()

    try:
        _prepare_silver_orders_data(
            settings=settings,
            spark=spark,
        )

        iceberg_job = OrdersIcebergJob(
            settings=settings,
            run_id=run_id,
            spark=spark,
        )

        result = iceberg_job.run(
            silver_prefix="silver/orders",
            table="orders",
        )

        assert result.table_name == "local.analytics.orders"
        assert result.rows_loaded > 0
        assert result.warehouse_path.endswith(".tmp/iceberg/warehouse")

    finally:
        spark.stop()


def _prepare_silver_orders_data(settings, spark):
    """
    Готовит минимальный silver/orders Parquet через OrdersSparkJob.

    Важно: используем ту же SparkSession, которая уже создана с Iceberg runtime.
    Иначе внутри pytest может сначала подняться обычная SparkSession без Iceberg,
    а потом Iceberg catalog уже не подхватится.
    """
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.s3.endpoint,
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )

    s3_client.put_object(
        Bucket=settings.s3.bucket,
        Key="raw/orders/orders.csv",
        Body=(
            b"order_id,user_id,amount,status,created_at\n"
            b"1,101,1500.50,paid,2026-06-01\n"
            b"2,102,700.00,paid,2026-06-01\n"
        ),
        ContentType="text/csv",
    )

    spark_job = OrdersSparkJob(
        settings=settings,
        run_id=f"prepare_silver_{uuid4()}",
        spark=spark,
    )

    spark_job.run(
        raw_key="raw/orders/orders.csv",
        silver_prefix="silver/orders",
    )