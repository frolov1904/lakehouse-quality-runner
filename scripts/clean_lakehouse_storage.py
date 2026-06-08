import argparse
import shutil
from pathlib import Path

import boto3

from app.core.settings import load_settings


DEFAULT_PREFIXES_TO_CLEAN = [
    "quality-reports/",
    "test-artifacts/",
    "raw/pytester/",
    "raw/test/",
    "silver/test/",
]

DEMO_PREFIXES_TO_CLEAN = [
    "raw/orders/",
    "silver/orders/",
    "quality-reports/",
    "test-artifacts/",
]

ALL_PREFIXES_TO_CLEAN = [
    "raw/",
    "silver/",
    "quality-reports/",
    "test-artifacts/",
]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--demo-reset",
        action="store_true",
        help="Clean demo prefixes: raw/orders, silver/orders, quality-reports, test-artifacts",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all lakehouse prefixes: raw, silver, quality-reports, test-artifacts",
    )

    parser.add_argument(
        "--keep-local",
        action="store_true",
        help="Do not clean local .tmp and quality-reports directories",
    )

    args = parser.parse_args()

    settings = load_settings()

    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.s3.endpoint,
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )

    if args.all:
        prefixes = ALL_PREFIXES_TO_CLEAN
    elif args.demo_reset:
        prefixes = DEMO_PREFIXES_TO_CLEAN
    else:
        prefixes = DEFAULT_PREFIXES_TO_CLEAN

    print("Cleaning S3/MinIO prefixes:")

    total_deleted = 0

    for prefix in prefixes:
        deleted_count = _delete_prefix(
            s3_client=s3_client,
            bucket=settings.s3.bucket,
            prefix=prefix,
        )

        total_deleted += deleted_count
        print(f"- {prefix}: deleted {deleted_count} object(s)")

    print(f"Total deleted from S3/MinIO: {total_deleted}")

    if not args.keep_local:
        _clean_local_paths(
            [
                Path(".tmp"),
                Path("quality-reports"),
            ]
        )


def _delete_prefix(s3_client, bucket: str, prefix: str) -> int:
    paginator = s3_client.get_paginator("list_objects_v2")

    deleted_count = 0

    for page in paginator.paginate(
        Bucket=bucket,
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

        s3_client.delete_objects(
            Bucket=bucket,
            Delete=delete_payload,
        )

        deleted_count += len(objects)

    return deleted_count


def _clean_local_paths(paths: list[Path]) -> None:
    print("Cleaning local artifacts:")

    for path in paths:
        if not path.exists():
            print(f"- {path}: skipped, path does not exist")
            continue

        if path.is_dir():
            shutil.rmtree(path)
            print(f"- {path}: directory removed")
        else:
            path.unlink()
            print(f"- {path}: file removed")


if __name__ == "__main__":
    main()