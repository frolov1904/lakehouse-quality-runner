import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

from pyspark.sql import SparkSession

from app.core.settings import AppSettings
from app.services.s3_storage import S3Storage


ICEBERG_PACKAGE = "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.11.0"


@dataclass(frozen=True)
class OrdersIcebergJobResult:
    """
    Результат выполнения Iceberg job.
    """

    table_name: str
    warehouse_path: str
    local_silver_path: str
    rows_loaded: int


class OrdersIcebergJob:
    """
    Job для создания Iceberg-таблицы analytics.orders
    на основе silver/orders Parquet-файлов.
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
        silver_prefix: str = "silver/orders",
        table: str = "orders",
    ) -> OrdersIcebergJobResult:
        """
        Запускает Iceberg job.

        Схема:
        S3 silver Parquet -> local tmp -> Spark -> Iceberg table.
        """
        work_dir = self._build_work_dir()
        local_silver_path = work_dir / "silver" / "orders"

        if work_dir.exists():
            shutil.rmtree(work_dir)

        local_silver_path.mkdir(parents=True, exist_ok=True)

        parquet_keys = self._download_silver_parquet_files(
            silver_prefix=silver_prefix,
            local_silver_path=local_silver_path,
        )

        if not parquet_keys:
            raise FileNotFoundError(
                f"Не найдены parquet-файлы по prefix: {silver_prefix}"
            )

        spark = self._external_spark or self._build_spark_session()

        catalog = self._settings.lakehouse.iceberg_catalog
        namespace = self._settings.lakehouse.iceberg_namespace
        full_table_name = f"{catalog}.{namespace}.{table}"

        try:
            df = spark.read.parquet(str(local_silver_path))
            rows_loaded = df.count()

            spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {catalog}.{namespace}")

            df.createOrReplaceTempView("orders_silver_tmp")

            spark.sql(
                f"""
                CREATE OR REPLACE TABLE {full_table_name}
                USING iceberg
                AS SELECT * FROM orders_silver_tmp
                """
            )

            # Простая проверка, что таблица реально читается через Spark SQL.
            spark.sql(f"SELECT * FROM {full_table_name}").count()

        finally:
            if self._external_spark is None:
                spark.stop()

        return OrdersIcebergJobResult(
            table_name=full_table_name,
            warehouse_path=str(self._warehouse_path()),
            local_silver_path=str(local_silver_path),
            rows_loaded=rows_loaded,
        )

    def _download_silver_parquet_files(
        self,
        silver_prefix: str,
        local_silver_path: Path,
    ) -> list[str]:
        """
        Скачивает .parquet файлы из S3 silver prefix в локальную папку.
        """
        objects = self._storage.list_objects(prefix=silver_prefix)

        parquet_keys = [
            item["key"]
            for item in objects
            if item["key"].endswith(".parquet")
        ]

        for key in parquet_keys:
            local_path = local_silver_path / Path(key).name
            self._storage.download_file(
                key=key,
                local_path=local_path,
            )

        return parquet_keys

    def _build_work_dir(self) -> Path:
        """
        Формирует временную директорию для Iceberg job.
        """
        return (
            Path(self._settings.lakehouse.local_tmp_dir)
            / "iceberg"
            / self._run_id
        )

    def _warehouse_path(self) -> Path:
        """
        Возвращает путь к локальному Iceberg warehouse.
        """
        return Path(self._settings.lakehouse.iceberg_warehouse).resolve()

    def _build_spark_session(self) -> SparkSession:
        """
        Создает SparkSession с Iceberg runtime и Hadoop catalog.

        Hadoop catalog — простой directory-based catalog.
        Iceberg документация описывает SparkCatalog и Hadoop catalog
        как один из вариантов конфигурации Spark + Iceberg.
        """
        catalog = self._settings.lakehouse.iceberg_catalog
        warehouse = self._warehouse_path()

        return (
            SparkSession.builder
            .appName("orders-silver-to-iceberg")
            .master("local[*]")
            .config("spark.jars.packages", ICEBERG_PACKAGE)
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            )
            .config(
                f"spark.sql.catalog.{catalog}",
                "org.apache.iceberg.spark.SparkCatalog",
            )
            .config(f"spark.sql.catalog.{catalog}.type", "hadoop")
            .config(f"spark.sql.catalog.{catalog}.warehouse", str(warehouse))
            .getOrCreate()
        )