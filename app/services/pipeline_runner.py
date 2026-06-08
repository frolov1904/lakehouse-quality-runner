from dataclasses import dataclass
from typing import Callable, Optional

from app.core.settings import AppSettings
from app.services.kafka_events import FileUploadedEvent
from app.services.orders_spark_job import OrdersSparkJob, OrdersSparkJobResult
from app.services.quality_runner import PytestQualityRunner, QualityRunResult


@dataclass(frozen=True)
class PipelineRunResult:
    """
    Результат выполнения pipeline по одному Kafka-событию.
    """

    dataset: str
    run_id: str
    raw_key: str
    silver_prefix: str
    spark_rows_read: int
    spark_rows_written: int
    quality_exit_code: int
    status: str


class FileUploadedPipelineRunner:
    """
    Оркестратор pipeline для события file_uploaded.

    Делает цепочку:
    Kafka event -> Spark raw to silver -> pytest quality checks.
    """

    def __init__(
        self,
        settings: AppSettings,
        quality_runner: Optional[PytestQualityRunner] = None,
        spark_job_factory: Optional[Callable[[str], OrdersSparkJob]] = None,
    ):
        self._settings = settings
        self._quality_runner = quality_runner or PytestQualityRunner()
        self._spark_job_factory = spark_job_factory or self._build_spark_job

    def run(
        self,
        event: FileUploadedEvent,
        run_id: str,
    ) -> PipelineRunResult:
        """
        Запускает pipeline для одного события file_uploaded.
        """
        silver_prefix = self._build_silver_prefix(event.dataset)

        spark_job = self._spark_job_factory(run_id)

        spark_result = spark_job.run(
            raw_key=event.key,
            silver_prefix=silver_prefix,
        )

        quality_result = self._quality_runner.run(
            dataset=event.dataset,
            run_id=run_id,
        )

        status = self._build_status(quality_result)

        return PipelineRunResult(
            dataset=event.dataset,
            run_id=run_id,
            raw_key=event.key,
            silver_prefix=silver_prefix,
            spark_rows_read=spark_result.rows_read,
            spark_rows_written=spark_result.rows_written,
            quality_exit_code=quality_result.exit_code,
            status=status,
        )

    def _build_spark_job(self, run_id: str) -> OrdersSparkJob:
        """
        Создает Spark job для конкретного запуска.
        """
        return OrdersSparkJob(
            settings=self._settings,
            run_id=run_id,
        )

    def _build_silver_prefix(self, dataset: str) -> str:
        """
        Формирует S3 prefix для silver-слоя.

        Например:
        silver/orders
        """
        silver_prefix = self._settings.lakehouse.silver_prefix.strip("/")

        return f"{silver_prefix}/{dataset}"

    def _build_status(self, quality_result: QualityRunResult) -> str:
        """
        Определяет итоговый статус pipeline.
        """
        if quality_result.exit_code == 0:
            return "success"

        return "quality_failed"