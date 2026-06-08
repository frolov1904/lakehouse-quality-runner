import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class QualityRunResult:
    """
    Результат запуска quality checks.
    """

    dataset: str
    run_id: str
    exit_code: int
    command: List[str]


class PytestQualityRunner:
    """
    Сервис для запуска ETL/data quality проверок через pytest.

    Worker будет использовать этот сервис после получения Kafka-события.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        tests_path: str = "tests/quality",
    ):
        self._project_root = project_root or Path(__file__).resolve().parents[2]
        self._tests_path = tests_path

    def build_command(self, dataset: str, run_id: str) -> List[str]:
        """
        Формирует команду запуска pytest.

        Используем sys.executable, чтобы запускать pytest тем же Python,
        в котором работает текущий worker.
        """
        return [
            sys.executable,
            "-m",
            "pytest",
            self._tests_path,
            f"--dataset={dataset}",
            f"--run-id={run_id}",
        ]

    def run(self, dataset: str, run_id: str) -> QualityRunResult:
        """
        Запускает quality checks через subprocess.
        """
        command = self.build_command(dataset=dataset, run_id=run_id)

        completed_process = subprocess.run(
            command,
            cwd=self._project_root,
            check=False,
        )

        return QualityRunResult(
            dataset=dataset,
            run_id=run_id,
            exit_code=completed_process.returncode,
            command=command,
        )