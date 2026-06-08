from pathlib import Path
from typing import BinaryIO

import boto3

from app.core.settings import S3Settings


class S3Storage:
    """
    Сервис для работы с S3-compatible хранилищем.

    Используется FastAPI endpoint'ами и ETL/Spark job'ами.
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
        """
        self._client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

    def download_file(self, key: str, local_path: Path) -> None:
        """
        Скачивает объект из S3 в локальный файл.
        """
        local_path.parent.mkdir(parents=True, exist_ok=True)

        self._client.download_file(
            Bucket=self.bucket,
            Key=key,
            Filename=str(local_path),
        )

    def upload_file(self, local_path: Path, key: str) -> None:
        """
        Загружает локальный файл в S3.
        """
        self._client.upload_file(
            Filename=str(local_path),
            Bucket=self.bucket,
            Key=key,
        )

    def upload_directory(self, local_dir: Path, prefix: str) -> list[str]:
        """
        Загружает все файлы из локальной директории в S3 prefix.

        Возвращает список S3 key, которые были загружены.
        """
        uploaded_keys = []

        for file_path in local_dir.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.name.startswith("."):
                continue

            relative_path = file_path.relative_to(local_dir)
            key = f"{prefix.rstrip('/')}/{relative_path.as_posix()}"

            self.upload_file(
                local_path=file_path,
                key=key,
            )

            uploaded_keys.append(key)

        return uploaded_keys

    def delete_prefix(self, prefix: str) -> int:
        """
        Удаляет все объекты по prefix.

        Это удобно перед перезаписью silver-слоя, чтобы не оставались старые
        part-файлы от предыдущих запусков.
        """
        paginator = self._client.get_paginator("list_objects_v2")

        deleted_count = 0

        for page in paginator.paginate(
            Bucket=self.bucket,
            Prefix=prefix,
        ):
            objects = page.get("Contents", [])

            if not objects:
                continue

            delete_payload = {
                "Objects": [
                    {
                        "Key": item["Key"],
                    }
                    for item in objects
                ]
            }

            self._client.delete_objects(
                Bucket=self.bucket,
                Delete=delete_payload,
            )

            deleted_count += len(objects)

        return deleted_count

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