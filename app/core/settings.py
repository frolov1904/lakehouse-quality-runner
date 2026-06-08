import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = "etl_guard.local.json"


@dataclass(frozen=True)
class S3Settings:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


@dataclass(frozen=True)
class KafkaSettings:
    enabled: bool
    bootstrap_servers: str
    topic_file_uploaded: str
    quality_worker_group: str
    auto_offset_reset: str


@dataclass(frozen=True)
class LakehouseSettings:
    raw_prefix: str
    silver_prefix: str
    local_tmp_dir: str
    iceberg_warehouse: str
    iceberg_catalog: str
    iceberg_namespace: str


@dataclass(frozen=True)
class AppSettings:
    s3: S3Settings
    kafka: KafkaSettings
    lakehouse: LakehouseSettings


def load_settings(config_path: str = DEFAULT_CONFIG_PATH) -> AppSettings:
    """
    Загружает настройки приложения из etl_guard.local.json.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Конфигурационный файл не найден: {config_path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_config = json.load(file)

    s3_config = raw_config["s3"]
    kafka_config = raw_config.get("kafka", {})
    lakehouse_config = raw_config.get("lakehouse", {})

    return AppSettings(
        s3=S3Settings(
            endpoint=s3_config["endpoint"],
            access_key=s3_config["access_key"],
            secret_key=s3_config["secret_key"],
            bucket=s3_config["bucket"],
        ),
        kafka=KafkaSettings(
            enabled=kafka_config.get("enabled", False),
            bootstrap_servers=kafka_config.get(
                "bootstrap_servers",
                "localhost:9092",
            ),
            topic_file_uploaded=kafka_config.get(
                "topic_file_uploaded",
                "etl.file_uploaded",
            ),
            quality_worker_group=kafka_config.get(
                "quality_worker_group",
                "lqr-quality-worker",
            ),
            auto_offset_reset=kafka_config.get(
                "auto_offset_reset",
                "earliest",
            ),
        ),
        lakehouse=LakehouseSettings(
            raw_prefix=lakehouse_config.get("raw_prefix", "raw"),
            silver_prefix=lakehouse_config.get("silver_prefix", "silver"),
            local_tmp_dir=lakehouse_config.get(
                "local_tmp_dir",
                ".tmp/lakehouse",
            ),
            iceberg_warehouse=lakehouse_config.get(
                "iceberg_warehouse",
                ".tmp/iceberg/warehouse",
            ),
            iceberg_catalog=lakehouse_config.get(
                "iceberg_catalog",
                "local",
            ),
            iceberg_namespace=lakehouse_config.get(
                "iceberg_namespace",
                "analytics",
            ),
        ),
    )