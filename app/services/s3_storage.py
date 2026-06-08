from typing import BinaryIO

import boto3

from app.core.settings import S3Settings


class S3Storage:
    """
    Сервис для работы с S3-compatible хранилищем.

    Сейчас он используется FastAPI-эндпоинтами, чтобы загружать
    файлы в raw-слой Data Lake.
    """

    def __init__(self, settings: S3Settings):
        self._settings = settings
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.endpoint,
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
        )

    @property
    def bucket(self) -> str:
        return self._settings.bucket

    def upload_fileobj(self, fileobj: BinaryIO, key: str, content_type: str) -> None:
        """
        Загружает файлоподобный объект в S3.

        Используем upload_fileobj, потому что FastAPI UploadFile
        хранит файл как file-like object.
        """
        self._client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

    def list_objects(self, prefix: str) -> list[dict]:
        """
        Возвращает список объектов по prefix.
        """
        response = self._client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
        )

        return [
            {
                "key": item["Key"],
                "size": item["Size"],
                "last_modified": item["LastModified"].isoformat(),
            }
            for item in response.get("Contents", [])
        ]