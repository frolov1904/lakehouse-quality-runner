import json

import boto3
import pytest


@pytest.mark.s3
def test_plugin_uploads_quality_report_to_s3(pytester):
    """
    Проверяем pytest-плагин как пользовательский инструмент.

    Сценарий:
    1. pytester создает временный тестовый файл;
    2. внутри временного теста используется fixture s3_client из нашего плагина;
    3. pytester запускает pytest с CLI-опциями нашего плагина;
    4. плагин генерирует quality report;
    5. плагин загружает report.json в MinIO/S3;
    6. внешний тест проверяет, что report.json реально появился в S3.
    """
    run_id = "pytester_run"
    bucket = "data-lake"
    report_key = f"quality-reports/{run_id}/report.json"

    pytester.makepyfile(
        test_temp_etl_check="""
        import pytest

        @pytest.mark.etl
        @pytest.mark.quality
        @pytest.mark.s3
        def test_temporary_s3_quality_check(s3_client, s3_bucket):
            key = "raw/pytester/sample.txt"

            s3_client.put_object(
                Bucket=s3_bucket,
                Key=key,
                Body=b"hello from pytester",
            )

            response = s3_client.head_object(
                Bucket=s3_bucket,
                Key=key,
            )

            assert response["ContentLength"] > 0
        """
    )

    result = pytester.runpytest(
        "test_temp_etl_check.py",
        "--etl-env=local",
        "--dataset=orders",
        f"--run-id={run_id}",
        "--s3-endpoint=http://localhost:9000",
        "--s3-access-key=minioadmin",
        "--s3-secret-key=minioadmin",
        f"--s3-bucket={bucket}",
        "--quality-report-dir=quality-reports",
        "--upload-quality-report-to-s3",
        "--quality-report-s3-prefix=quality-reports",
    )

    result.assert_outcomes(passed=1)

    s3_client = boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )

    response = s3_client.get_object(
        Bucket=bucket,
        Key=report_key,
    )

    report = json.loads(response["Body"].read().decode("utf-8"))

    assert report["run_id"] == run_id
    assert report["dataset"] == "orders"
    assert report["env"] == "local"

    assert report["quality_report"]["upload_to_s3"] is True
    assert report["quality_report"]["s3_key"] == report_key

    assert report["summary"]["total"] == 1
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 0