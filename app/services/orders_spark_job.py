import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from app.core.settings import AppSettings
from app.services.s3_storage import S3Storage


@dataclass(frozen=True)
class OrdersSparkJobResult:
    """
    Результат выполнения Spark job.
    """

    raw_key: str
    silver_prefix: str
    local_raw_path: str
    local_silver_path: str
    rows_read: int
    rows_written: int
    uploaded_keys: list[str]


class OrdersSparkJob:
    """
    Spark job для обработки orders dataset.

    Делает преобразование:
    raw/orders/orders.csv -> silver/orders/*.parquet
    """

    def __init__(
        self,
        settings: AppSettings,
        run_id: str,
        spark: Optional[SparkSession] = None,
    ):
        self._settings = settings
        self._run_id = run_id
        self._storage = S3Storage(settings.s3)
        self._external_spark = spark

    def run(
        self,
        raw_key: str = "raw/orders/orders.csv",
        silver_prefix: str = "silver/orders",
    ) -> OrdersSparkJobResult:
        """
        Запускает Spark job.
        """
        work_dir = self._build_work_dir()
        local_raw_path = work_dir / "raw" / "orders.csv"
        local_silver_path = work_dir / "silver" / "orders"

        if work_dir.exists():
            shutil.rmtree(work_dir)

        local_silver_path.parent.mkdir(parents=True, exist_ok=True)

        self._storage.download_file(
            key=raw_key,
            local_path=local_raw_path,
        )

        spark = self._external_spark or self._build_spark_session()

        try:
            raw_df = self._read_raw_orders(
                spark=spark,
                local_raw_path=local_raw_path,
            )

            rows_read = raw_df.count()

            silver_df = self._transform_orders(raw_df)

            rows_written = silver_df.count()

            silver_df.write.mode("overwrite").parquet(
                str(local_silver_path)
            )

        finally:
            if self._external_spark is None:
                spark.stop()

        self._storage.delete_prefix(silver_prefix)

        uploaded_keys = self._storage.upload_directory(
            local_dir=local_silver_path,
            prefix=silver_prefix,
        )

        return OrdersSparkJobResult(
            raw_key=raw_key,
            silver_prefix=silver_prefix,
            local_raw_path=str(local_raw_path),
            local_silver_path=str(local_silver_path),
            rows_read=rows_read,
            rows_written=rows_written,
            uploaded_keys=uploaded_keys,
        )

    def _build_work_dir(self) -> Path:
        """
        Формирует временную рабочую директорию для конкретного запуска.
        """
        return (
            Path(self._settings.lakehouse.local_tmp_dir)
            / "spark"
            / self._run_id
        )

    def _build_spark_session(self) -> SparkSession:
        """
        Создает локальную SparkSession.
        """
        return (
            SparkSession.builder
            .appName("orders-raw-to-silver")
            .master("local[*]")
            .getOrCreate()
        )

    def _read_raw_orders(
        self,
        spark: SparkSession,
        local_raw_path: Path,
    ):
        """
        Читает raw CSV с явной схемой.
        """
        schema = StructType(
            [
                StructField("order_id", IntegerType(), True),
                StructField("user_id", IntegerType(), True),
                StructField("amount", DoubleType(), True),
                StructField("status", StringType(), True),
                StructField("created_at", StringType(), True),
            ]
        )

        return (
            spark.read
            .option("header", True)
            .schema(schema)
            .csv(str(local_raw_path))
        )

    def _transform_orders(self, raw_df):
        """
        Приводит raw orders к silver-слою.

        Здесь делаем минимальную очистку:
        - убираем строки без order_id;
        - убираем строки без user_id;
        - убираем строки без amount;
        - убираем отрицательные amount;
        - оставляем только допустимые status;
        - приводим created_at к date.
        """
        allowed_statuses = ["new", "paid", "cancelled"]

        return (
            raw_df
            .filter(col("order_id").isNotNull())
            .filter(col("user_id").isNotNull())
            .filter(col("amount").isNotNull())
            .filter(col("amount") >= 0)
            .filter(col("status").isin(allowed_statuses))
            .withColumn("created_at", to_date(col("created_at")))
            .select(
                "order_id",
                "user_id",
                "amount",
                "status",
                "created_at",
            )
        )