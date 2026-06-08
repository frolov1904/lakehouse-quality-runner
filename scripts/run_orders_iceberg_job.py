import argparse
from datetime import datetime, timezone

from app.core.settings import load_settings
from app.services.orders_iceberg_job import OrdersIcebergJob


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run-id",
        default=None,
        help="Run id for Iceberg job",
    )

    parser.add_argument(
        "--silver-prefix",
        default="silver/orders",
        help="S3 prefix with silver Parquet data",
    )

    parser.add_argument(
        "--table",
        default="orders",
        help="Iceberg table name",
    )

    args = parser.parse_args()

    run_id = args.run_id or _generate_run_id()

    settings = load_settings()

    job = OrdersIcebergJob(
        settings=settings,
        run_id=run_id,
    )

    result = job.run(
        silver_prefix=args.silver_prefix,
        table=args.table,
    )

    print("Iceberg job finished")
    print(f"table_name: {result.table_name}")
    print(f"warehouse_path: {result.warehouse_path}")
    print(f"local_silver_path: {result.local_silver_path}")
    print(f"rows_loaded: {result.rows_loaded}")


def _generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"orders_iceberg_{timestamp}"


if __name__ == "__main__":
    main()