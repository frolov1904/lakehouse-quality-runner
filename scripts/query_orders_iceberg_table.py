from app.core.settings import load_settings
from app.services.orders_iceberg_job import OrdersIcebergJob


def main() -> None:
    settings = load_settings()

    job = OrdersIcebergJob(
        settings=settings,
        run_id="query_orders_iceberg",
    )

    spark = job._build_spark_session()

    catalog = settings.lakehouse.iceberg_catalog
    namespace = settings.lakehouse.iceberg_namespace
    table_name = f"{catalog}.{namespace}.orders"

    try:
        print(f"\nTable: {table_name}\n")

        print("DESCRIBE TABLE:")
        spark.sql(f"DESCRIBE TABLE {table_name}").show(
            truncate=False,
        )

        print("DATA SAMPLE:")
        spark.sql(f"SELECT * FROM {table_name} LIMIT 20").show(
            truncate=False,
        )

        print("STATUS AGGREGATION:")
        spark.sql(
            f"""
            SELECT
                status,
                COUNT(*) AS orders_count,
                ROUND(SUM(amount), 2) AS total_amount
            FROM {table_name}
            GROUP BY status
            ORDER BY status
            """
        ).show(
            truncate=False,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()