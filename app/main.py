from fastapi import FastAPI

from app.api.datasets import router as datasets_router


app = FastAPI(
    title="Lakehouse Quality Runner",
    description="Training project for ETL quality checks, S3 and pytest plugins",
    version="0.6.0",
)


@app.get("/health")
def health_check():
    """
    Простейший healthcheck endpoint.
    """
    return {
        "status": "ok",
        "service": "lakehouse-quality-runner",
    }


app.include_router(datasets_router)