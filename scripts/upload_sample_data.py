import boto3


S3_ENDPOINT = "http://localhost:9000"
S3_ACCESS_KEY = "minioadmin"
S3_SECRET_KEY = "minioadmin"

BUCKET = "data-lake"
LOCAL_FILE = "data/orders.csv"
S3_KEY = "raw/orders/orders.csv"


def main():
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )

    s3.upload_file(
        LOCAL_FILE,
        BUCKET,
        S3_KEY,
    )

    print(f"Файл загружен: s3://{BUCKET}/{S3_KEY}")


if __name__ == "__main__":
    main()