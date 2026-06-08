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
class AppSettings:
    s3: S3Settings


def load_settings(config_path: str = DEFAULT_CONFIG_PATH) -> AppSettings:
    """
    Загружает настройки приложения из etl_guard.local.json.

    Сейчас FastAPI-приложение использует тот же локальный конфиг,
    что и pytest-плагин.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Конфигурационный файл не найден: {config_path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_config = json.load(file)

    s3_config = raw_config["s3"]

    return AppSettings(
        s3=S3Settings(
            endpoint=s3_config["endpoint"],
            access_key=s3_config["access_key"],
            secret_key=s3_config["secret_key"],
            bucket=s3_config["bucket"],
        )
    )