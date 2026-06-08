import argparse
from typing import Optional

from confluent_kafka import Consumer, KafkaError

from app.core.settings import AppSettings, KafkaSettings, load_settings
from app.services.kafka_events import (
    FileUploadedEvent,
    parse_file_uploaded_event,
)
from app.services.pipeline_runner import FileUploadedPipelineRunner


def build_quality_run_id(event: FileUploadedEvent) -> str:
    """
    Формирует run_id для pipeline на основе Kafka-события.

    Пример:
    orders_71c6b017
    """
    short_event_id = event.event_id.split("-")[0]
    return f"{event.dataset}_{short_event_id}"


class QualityWorker:
    """
    Kafka consumer worker.

    Читает события file_uploaded и запускает pipeline:
    Spark raw -> silver, затем pytest quality checks.
    """

    def __init__(
        self,
        app_settings: AppSettings,
        pipeline_runner: Optional[FileUploadedPipelineRunner] = None,
    ):
        self._app_settings = app_settings
        self._kafka_settings = app_settings.kafka
        self._pipeline_runner = pipeline_runner or FileUploadedPipelineRunner(
            settings=app_settings,
        )
        self._consumer = self._build_consumer(self._kafka_settings)

    def run(self, once: bool = False) -> None:
        """
        Запускает worker.

        Если once=True, worker обработает одно сообщение и завершится.
        Это удобно для локальной проверки.
        """
        topic = self._kafka_settings.topic_file_uploaded

        print(f"Quality worker subscribed to topic: {topic}")

        self._consumer.subscribe([topic])

        try:
            while True:
                message = self._consumer.poll(1.0)

                if message is None:
                    continue

                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue

                    print(f"Kafka consumer error: {message.error()}")
                    continue

                self._process_message(message)

                self._consumer.commit(message=message)

                if once:
                    print("Quality worker processed one message and stopped")
                    break

        finally:
            self._consumer.close()

    def _process_message(self, message) -> None:
        """
        Обрабатывает одно Kafka-сообщение.
        """
        event = parse_file_uploaded_event(message.value())
        run_id = build_quality_run_id(event)

        print(
            "Received file_uploaded event: "
            f"dataset={event.dataset}, key={event.key}, event_id={event.event_id}"
        )

        print(
            "Starting pipeline: "
            f"dataset={event.dataset}, run_id={run_id}, raw_key={event.key}"
        )

        result = self._pipeline_runner.run(
            event=event,
            run_id=run_id,
        )

        print(
            "Pipeline finished: "
            f"dataset={result.dataset}, "
            f"run_id={result.run_id}, "
            f"status={result.status}, "
            f"spark_rows_read={result.spark_rows_read}, "
            f"spark_rows_written={result.spark_rows_written}, "
            f"quality_exit_code={result.quality_exit_code}"
        )

    def _build_consumer(self, kafka_settings: KafkaSettings) -> Consumer:
        """
        Создает Kafka consumer.
        """
        return Consumer(
            {
                "bootstrap.servers": kafka_settings.bootstrap_servers,
                "group.id": kafka_settings.quality_worker_group,
                "auto.offset.reset": kafka_settings.auto_offset_reset,
                "enable.auto.commit": False,
            }
        )


def main() -> None:
    """
    CLI entrypoint для запуска quality worker.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--once",
        action="store_true",
        help="Process only one Kafka message and stop",
    )

    args = parser.parse_args()

    settings = load_settings()

    worker = QualityWorker(
        app_settings=settings,
    )

    worker.run(once=args.once)