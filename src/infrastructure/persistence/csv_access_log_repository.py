import csv
from pathlib import Path

from src.application.ports.access_log_repository import AccessLogRepository
from src.domain.access_log import LoginEvent


class CsvAccessLogRepository(AccessLogRepository):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def save(self, event: LoginEvent) -> None:
        file_exists = self._file_path.exists()

        with self._file_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "username",
                    "attempted_at",
                    "success",
                    "message",
                    "source",
                ],
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "username": event.username,
                    "attempted_at": event.attempted_at.isoformat(),
                    "success": event.success,
                    "message": event.message,
                    "source": event.source,
                }
            )
