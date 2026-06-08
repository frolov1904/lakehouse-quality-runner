import argparse
from datetime import datetime, timezone

from app.core.settings import load_settings
from app.services.orders_spark_job import OrdersSparkJob


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run-id",
        default=None,
        help="Run id for Spark job",
    )

    parser.add_argument(
        "--raw-key",
        default="raw/orders/orders.csv",
        help="Raw S3 key with orders CSV",
    )

    parser.add_argument(
        "--silver-prefix",
        default="silver/orders",
        help="S3 prefix for silver Parquet output",
    )

    args = parser.parse_args()

    run_id = args.run_id or _generate_run_id()

    settings = load_settings()

    job = OrdersSparkJob(
        settings=settings,
        run_id=run_id,
    )

    result = job.run(
        raw_key=args.raw_key,
        silver_prefix=args.silver_prefix,
    )

    print("Spark job finished")
    print(f"raw_key: {result.raw_key}")
    print(f"silver_prefix: {result.silver_prefix}")
    print(f"rows_read: {result.rows_read}")
    print(f"rows_written: {result.rows_written}")
    print("uploaded_keys:")
    for key in result.uploaded_keys:
        print(f"- {key}")


def _generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"orders_spark_{timestamp}"


if __name__ == "__main__":
    main()