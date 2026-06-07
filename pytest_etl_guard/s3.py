import boto3

from pytest_etl_guard.config import get_etl_guard_config


def build_s3_client(config):
    """
    Создает boto3 S3 client на основе итоговой конфигурации плагина.
    """
    etl_config = get_etl_guard_config(config)
    s3_config = etl_config["s3"]

    return boto3.client(
        "s3",
        endpoint_url=s3_config["endpoint"],
        aws_access_key_id=s3_config["access_key"],
        aws_secret_access_key=s3_config["secret_key"],
    )


def upload_report_to_s3(config, s3_key, report_json):
    """
    Загружает report.json в S3-compatible хранилище.
    """
    etl_config = get_etl_guard_config(config)

    s3_client = build_s3_client(config)
    bucket = etl_config["s3"]["bucket"]

    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=report_json.encode("utf-8"),
        ContentType="application/json",
    )