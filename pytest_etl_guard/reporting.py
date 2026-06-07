import json
from datetime import datetime, timezone
from pathlib import Path

from pytest_etl_guard.config import get_etl_guard_config


def build_quality_report(config, exitstatus, results):
    """
    Формирует итоговый quality report.
    """
    etl_config = get_etl_guard_config(config)

    local_report_path = build_report_path(config)
    s3_report_key = build_report_s3_key(config)
    upload_to_s3 = etl_config["quality_report"]["upload_to_s3"]

    return {
        "run_id": etl_config["run_id"],
        "dataset": etl_config["dataset"],
        "env": etl_config["env"],
        "started_at": getattr(config, "_etl_guard_started_at", None),
        "finished_at": utc_now(),
        "exitstatus": exitstatus,
        "s3": {
            "endpoint": etl_config["s3"]["endpoint"],
            "bucket": etl_config["s3"]["bucket"],
        },
        "quality_report": {
            "local_path": str(local_report_path),
            "upload_to_s3": upload_to_s3,
            "s3_key": s3_report_key if upload_to_s3 else None,
        },
        "summary": build_summary(results),
        "tests": results,
    }


def report_to_json(report):
    """
    Превращает quality report в красивый JSON.
    """
    return json.dumps(report, ensure_ascii=False, indent=2)


def build_summary(results):
    """
    Считает краткую статистику по результатам ETL-проверок.
    """
    return {
        "total": len(results),
        "passed": sum(1 for result in results if result["outcome"] == "passed"),
        "failed": sum(1 for result in results if result["outcome"] == "failed"),
        "skipped": sum(1 for result in results if result["outcome"] == "skipped"),
    }


def build_report_path(config):
    """
    Формирует путь к локальному report.json.
    """
    etl_config = get_etl_guard_config(config)

    report_dir = Path(etl_config["quality_report"]["local_dir"])
    safe_run_id = make_safe_path_part(etl_config["run_id"])

    return report_dir / safe_run_id / "report.json"


def build_report_s3_key(config):
    """
    Формирует S3 key для quality report.
    """
    etl_config = get_etl_guard_config(config)

    prefix = etl_config["quality_report"]["s3_prefix"]
    clean_prefix = prefix.strip("/")
    safe_run_id = make_safe_path_part(etl_config["run_id"])

    return f"{clean_prefix}/{safe_run_id}/report.json"


def save_report_locally(report_path, report_json):
    """
    Сохраняет report.json на локальный диск.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_json, encoding="utf-8")


def make_safe_path_part(value):
    """
    Делает значение безопасным для использования в локальном пути и S3 key.
    """
    return value.replace("/", "_").replace(" ", "_")


def utc_now():
    """
    Возвращает текущее время в UTC в ISO-формате.
    """
    return datetime.now(timezone.utc).isoformat()