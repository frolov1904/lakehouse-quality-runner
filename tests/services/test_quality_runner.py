import sys
from pathlib import Path

from app.services.quality_runner import PytestQualityRunner


def test_pytest_quality_runner_builds_command():
    """
    Проверяем, что PytestQualityRunner правильно формирует команду запуска pytest.
    """
    runner = PytestQualityRunner(
        project_root=Path("."),
        tests_path="tests/quality",
    )

    command = runner.build_command(
        dataset="orders",
        run_id="orders_test_run",
    )

    assert command == [
        sys.executable,
        "-m",
        "pytest",
        "tests/quality",
        "--dataset=orders",
        "--run-id=orders_test_run",
    ]