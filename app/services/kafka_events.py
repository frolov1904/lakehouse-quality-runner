import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Producer

from app.core.settings import KafkaSettings


@dataclass(frozen=True)
class FileUploadedEvent:
    """
    Событие, которое публикуется после загрузки файла в raw-слой S3.
    """

    event_id: str
    event_type: str
    dataset: str
    bucket: str
    key: str
    filename: str
    content_type: str
    occurred_at: str


class KafkaEventPublisher:
    """
    Сервис для публикации событий в Kafka.
    """

    def __init__(self, settings: KafkaSettings):
        self._settings = settings
        self._producer = Producer(
            {
                "bootstrap.servers": settings.bootstrap_servers,
            }
        )

    @property
    def topic_file_uploaded(self) -> str:
        return self._settings.topic_file_uploaded

    def publish_file_uploaded(self, event: FileUploadedEvent) -> None:
        """
        Публикует событие о загрузке файла.

        key используем равным dataset, чтобы события одного dataset
        логически группировались.
        """
        errors = []

        def delivery_callback(error, message):
            if error is not None:
                errors.append(str(error))

        self._producer.produce(
            topic=self.topic_file_uploaded,
            key=event.dataset.encode("utf-8"),
            value=json.dumps(
                asdict(event),
                ensure_ascii=False,
            ).encode("utf-8"),
            callback=delivery_callback,
        )

        self._producer.flush(timeout=10)

        if errors:
            raise RuntimeError(
                f"Не удалось опубликовать событие в Kafka: {errors}"
            )


def build_file_uploaded_event(
    dataset: str,
    bucket: str,
    key: str,
    filename: str,
    content_type: str,
) -> FileUploadedEvent:
    """
    Создает событие file_uploaded.
    """
    return FileUploadedEvent(
        event_id=str(uuid4()),
        event_type="file_uploaded",
        dataset=dataset,
        bucket=bucket,
        key=key,
        filename=filename,
        content_type=content_type,
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )