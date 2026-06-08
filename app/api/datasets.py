from fastapi import APIRouter, File, UploadFile

from app.core.settings import load_settings
from app.services.s3_storage import S3Storage


router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_storage() -> S3Storage:
    """
    Создает S3Storage на основе локального конфига.

    Пока делаем простую реализацию. Позже можно заменить на нормальную
    dependency injection через Depends и кеширование настроек.
    """
    settings = load_settings()
    return S3Storage(settings.s3)


@router.post("/{dataset}/upload")
async def upload_dataset_file(
    dataset: str,
    file: UploadFile = File(...),
):
    """
    Загружает файл в raw-слой S3.

    Пример итогового key:
    raw/orders/orders.csv
    """
    storage = get_storage()

    key = f"raw/{dataset}/{file.filename}"

    storage.upload_fileobj(
        fileobj=file.file,
        key=key,
        content_type=file.content_type or "application/octet-stream",
    )

    return {
        "dataset": dataset,
        "bucket": storage.bucket,
        "key": key,
        "status": "uploaded",
    }


@router.get("/{dataset}/objects")
def list_dataset_objects(dataset: str):
    """
    Показывает объекты в raw-слое для конкретного dataset.

    Например:
    GET /datasets/orders/objects
    вернет объекты с prefix raw/orders/
    """
    storage = get_storage()

    prefix = f"raw/{dataset}/"

    return {
        "dataset": dataset,
        "bucket": storage.bucket,
        "prefix": prefix,
        "objects": storage.list_objects(prefix=prefix),
    }