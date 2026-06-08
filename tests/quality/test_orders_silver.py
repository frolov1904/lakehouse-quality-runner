from pathlib import Path

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


SILVER_ORDERS_PREFIX = "silver/orders/"

EXPECTED_SCHEMA = {
    "order_id": "int",
    "user_id": "int",
    "amount": "double",
    "status": "string",
    "created_at": "date",
}

ALLOWED_STATUSES = ["new", "paid", "cancelled"]


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.s3
@pytest.mark.silver
def test_orders_silver_success_marker_exists(s3_client, s3_bucket):
    """
    Проверяем, что в silver-слое есть marker-файл _SUCCESS.

    Spark создает _SUCCESS после успешной записи результата.
    Это служебный файл, который показывает, что запись директории завершилась.
    """
    keys = _list_s3_keys(
        s3_client=s3_client,
        bucket=s3_bucket,
        prefix=SILVER_ORDERS_PREFIX,
    )

    assert f"{SILVER_ORDERS_PREFIX}_SUCCESS" in keys, (
        "В silver/orders/ не найден marker-файл _SUCCESS. "
        "Сначала запусти: python scripts/run_orders_spark_job.py"
    )


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.s3
@pytest.mark.silver
def test_orders_silver_parquet_files_exist(s3_client, s3_bucket):
    """
    Проверяем, что в silver-слое есть Parquet-файлы с данными.

    _SUCCESS сам по себе не является данными.
    Данные Spark лежат в part-*.parquet файлах.
    """
    parquet_keys = _list_silver_parquet_keys(
        s3_client=s3_client,
        bucket=s3_bucket,
    )

    assert parquet_keys, (
        "В silver/orders/ не найдены .parquet-файлы. "
        "Сначала запусти: python scripts/run_orders_spark_job.py"
    )


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.spark
@pytest.mark.silver
def test_orders_silver_parquet_is_readable_and_not_empty(
    s3_client,
    s3_bucket,
    tmp_path,
):
    """
    Проверяем, что silver Parquet можно прочитать через Spark
    и что результат не пустой.
    """
    df = _read_silver_orders_df(
        s3_client=s3_client,
        bucket=s3_bucket,
        tmp_path=tmp_path,
    )

    assert df.count() > 0


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.spark
@pytest.mark.silver
def test_orders_silver_schema_is_correct(
    s3_client,
    s3_bucket,
    tmp_path,
):
    """
    Проверяем схему silver-слоя.

    После Spark job ожидаем:
    - order_id: int
    - user_id: int
    - amount: double
    - status: string
    - created_at: date
    """
    df = _read_silver_orders_df(
        s3_client=s3_client,
        bucket=s3_bucket,
        tmp_path=tmp_path,
    )

    actual_schema = {
        field.name: field.dataType.simpleString()
        for field in df.schema.fields
    }

    assert actual_schema == EXPECTED_SCHEMA


@pytest.mark.etl
@pytest.mark.quality
@pytest.mark.spark
@pytest.mark.silver
def test_orders_silver_quality_rules(
    s3_client,
    s3_bucket,
    tmp_path,
):
    """
    Проверяем бизнес-правила качества данных в silver-слое.

    В silver-слое не должно быть:
    - null в order_id;
    - null в user_id;
    - null в amount;
    - отрицательных amount;
    - null в status;
    - неизвестных status.
    """
    df = _read_silver_orders_df(
        s3_client=s3_client,
        bucket=s3_bucket,
        tmp_path=tmp_path,
    )

    assert df.filter(col("order_id").isNull()).count() == 0
    assert df.filter(col("user_id").isNull()).count() == 0
    assert df.filter(col("amount").isNull()).count() == 0
    assert df.filter(col("amount") < 0).count() == 0
    assert df.filter(col("status").isNull()).count() == 0

    invalid_status_count = df.filter(
        ~col("status").isin(ALLOWED_STATUSES)
    ).count()

    assert invalid_status_count == 0


def _read_silver_orders_df(s3_client, bucket: str, tmp_path: Path):
    """
    Скачивает silver Parquet-файлы из S3 во временную папку
    и читает их через Spark.

    Мы не читаем напрямую s3a://, чтобы не зависеть от Hadoop S3A jars.
    Для локального учебного проекта схема такая:
    S3 → временная локальная папка → Spark read.parquet.
    """
    parquet_keys = _list_silver_parquet_keys(
        s3_client=s3_client,
        bucket=bucket,
    )

    assert parquet_keys, (
        "В silver/orders/ не найдены .parquet-файлы. "
        "Сначала запусти: python scripts/run_orders_spark_job.py"
    )

    local_silver_dir = tmp_path / "silver_orders"
    local_silver_dir.mkdir(parents=True, exist_ok=True)

    for key in parquet_keys:
        local_path = local_silver_dir / Path(key).name

        s3_client.download_file(
            bucket,
            key,
            str(local_path),
        )

    spark = (
        SparkSession.builder
        .appName("orders-silver-quality-check")
        .master("local[*]")
        .getOrCreate()
    )

    return spark.read.parquet(str(local_silver_dir))


def _list_silver_parquet_keys(s3_client, bucket: str) -> list[str]:
    """
    Возвращает список .parquet-файлов из silver/orders/.
    """
    keys = _list_s3_keys(
        s3_client=s3_client,
        bucket=bucket,
        prefix=SILVER_ORDERS_PREFIX,
    )

    return [
        key
        for key in keys
        if key.endswith(".parquet")
    ]


def _list_s3_keys(s3_client, bucket: str, prefix: str) -> list[str]:
    """
    Возвращает все S3 keys по prefix.
    """
    paginator = s3_client.get_paginator("list_objects_v2")

    keys = []

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=prefix,
    ):
        for item in page.get("Contents", []):
            keys.append(item["Key"])

    return keys