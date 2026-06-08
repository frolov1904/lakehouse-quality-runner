from fastapi import APIRouter, File, UploadFile
from typing import Optional

from app.core.settings import load_settings
from app.services.kafka_events import (
    KafkaEventPublisher,
    build_file_uploaded_event,
)
from app.services.s3_storage import S3Storage


router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_settings():
    """
    Загружает настройки приложения.
    """
    return load_settings()


def get_storage() -> S3Storage:
    """
    Создает S3Storage на основе локального конфига.
    """
    settings = get_settings()
    return S3Storage(settings.s3)


def get_event_publisher() -> Optional[KafkaEventPublisher]:
    """
    Создает Kafka publisher, если Kafka включена в конфиге.
    """
    settings = get_settings()

    if not settings.kafka.enabled:
        return None

    return KafkaEventPublisher(settings.kafka)


@router.post("/{dataset}/upload")
async def upload_dataset_file(
    dataset: str,
    file: UploadFile = File(...),
):
    """
    Загружает файл в raw-слой S3 и публикует событие в Kafka.
    """
    storage = get_storage()
    publisher = get_event_publisher()

    key = f"raw/{dataset}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    storage.upload_fileobj(
        fileobj=file.file,
        key=key,
        content_type=content_type,
    )

    event_info = {
        "published": False,
        "topic": None,
        "event_id": None,
    }

    if publisher is not None:
        event = build_file_uploaded_event(
            dataset=dataset,
            bucket=storage.bucket,
            key=key,
            filename=file.filename,
            content_type=content_type,
        )

        publisher.publish_file_uploaded(event)

        event_info = {
            "published": True,
            "topic": publisher.topic_file_uploaded,
            "event_id": event.event_id,
        }

    return {
        "dataset": dataset,
        "bucket": storage.bucket,
        "key": key,
        "status": "uploaded",
        "event": event_info,
    }


@router.get("/{dataset}/objects")
def list_dataset_objects(dataset: str):
    """
    Показывает объекты в raw-слое для конкретного dataset.
    """
    storage = get_storage()

    prefix = f"raw/{dataset}/"

    return {
        "dataset": dataset,
        "bucket": storage.bucket,
        "prefix": prefix,
        "objects": storage.list_objects(prefix=prefix),
    }