from dataclasses import dataclass

from app.core.settings import (
    AppSettings,
    KafkaSettings,
    LakehouseSettings,
    S3Settings,
)
from app.services.kafka_events import FileUploadedEvent
from app.services.orders_spark_job import OrdersSparkJobResult
from app.services.pipeline_runner import FileUploadedPipelineRunner
from app.services.quality_runner import QualityRunResult


@dataclass
class FakeSparkJob:
    """
    Фейковый Spark job для unit-теста pipeline runner.
    """

    calls: list

    def run(self, raw_key: str, silver_prefix: str) -> OrdersSparkJobResult:
        self.calls.append(
            {
                "raw_key": raw_key,
                "silver_prefix": silver_prefix,
            }
        )

        return OrdersSparkJobResult(
            raw_key=raw_key,
            silver_prefix=silver_prefix,
            local_raw_path=".tmp/raw/orders.csv",
            local_silver_path=".tmp/silver/orders",
            rows_read=5,
            rows_written=3,
            uploaded_keys=[
                f"{silver_prefix}/part-00000.snappy.parquet",
                f"{silver_prefix}/_SUCCESS",
            ],
        )


@dataclass
class FakeQualityRunner:
    """
    Фейковый quality runner для unit-теста pipeline runner.
    """

    calls: list

    def run(self, dataset: str, run_id: str) -> QualityRunResult:
        self.calls.append(
            {
                "dataset": dataset,
                "run_id": run_id,
            }
        )

        return QualityRunResult(
            dataset=dataset,
            run_id=run_id,
            exit_code=0,
            command=[
                "python",
                "-m",
                "pytest",
                "tests/quality",
            ],
        )


def test_file_uploaded_pipeline_runner_runs_spark_then_quality_checks():
    """
    Проверяем orchestration-логику:

    1. Pipeline runner получает file_uploaded event.
    2. Запускает Spark job с raw_key из события.
    3. Записывает результат в silver/<dataset>.
    4. Запускает quality checks с тем же dataset и run_id.
    5. Возвращает общий результат pipeline.
    """
    settings = _build_test_settings()

    spark_calls = []
    quality_calls = []

    fake_spark_job = FakeSparkJob(calls=spark_calls)
    fake_quality_runner = FakeQualityRunner(calls=quality_calls)

    pipeline_runner = FileUploadedPipelineRunner(
        settings=settings,
        quality_runner=fake_quality_runner,
        spark_job_factory=lambda run_id: fake_spark_job,
    )

    event = FileUploadedEvent(
        event_id="71c6b017-e6d0-43c1-bb73-71164d597b55",
        event_type="file_uploaded",
        dataset="orders",
        bucket="data-lake",
        key="raw/orders/orders.csv",
        filename="orders.csv",
        content_type="text/csv",
        occurred_at="2026-06-08T07:00:00+00:00",
    )

    result = pipeline_runner.run(
        event=event,
        run_id="orders_71c6b017",
    )

    assert spark_calls == [
        {
            "raw_key": "raw/orders/orders.csv",
            "silver_prefix": "silver/orders",
        }
    ]

    assert quality_calls == [
        {
            "dataset": "orders",
            "run_id": "orders_71c6b017",
        }
    ]

    assert result.dataset == "orders"
    assert result.run_id == "orders_71c6b017"
    assert result.raw_key == "raw/orders/orders.csv"
    assert result.silver_prefix == "silver/orders"
    assert result.spark_rows_read == 5
    assert result.spark_rows_written == 3
    assert result.quality_exit_code == 0
    assert result.status == "success"


def _build_test_settings() -> AppSettings:
    """
    Создает тестовые настройки без чтения etl_guard.local.json.
    """
    return AppSettings(
        s3=S3Settings(
            endpoint="http://localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket="data-lake",
        ),
        kafka=KafkaSettings(
            enabled=True,
            bootstrap_servers="localhost:9092",
            topic_file_uploaded="etl.file_uploaded",
            quality_worker_group="test-worker",
            auto_offset_reset="earliest",
        ),
        lakehouse=LakehouseSettings(
            raw_prefix="raw",
            silver_prefix="silver",
            local_tmp_dir=".tmp/lakehouse",
        ),
    )