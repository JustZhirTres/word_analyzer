# app/domain/entities.py - добавляем новую сущность

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class WordFrequencyResult:
    """Результат частотного анализа"""
    word: str
    total_count: int
    line_counts: list[int]

    def line_counts_str(self) -> str:
        """Форматирует частоты по строкам в строку через запятую"""
        return ','.join(str(count) for count in self.line_counts)


@dataclass
class Task:
    """Сущность задачи"""
    task_id: str
    filename: str
    file_extension: str
    status: str = "pending"
    progress: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    error: str | None = None
    result_path: str | None = None
    file_size_mb: float = 0.0

    @classmethod
    def create(cls, filename: str, file_extension: str) -> 'Task':
        """Фабричный метод для создания задачи"""
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        if not file_extension:
            raise ValueError("File extension cannot be empty")

        file_extension = file_extension.lower()
        task_id = str(uuid.uuid4())

        return cls(
            task_id=task_id,
            filename=filename.strip(),
            file_extension=file_extension
        )

    def to_dict(self) -> dict[str, object]:
        """Преобразует в словарь для API"""
        result: dict[str, object] = {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'file_name': self.filename,
            'file_size_mb': self.file_size_mb
        }

        optional_fields: dict[str, object] = {
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'failed_at': self.failed_at,
            'error': self.error,
        }

        for field_name, field_value in optional_fields.items():
            if field_value is not None:
                if isinstance(field_value, datetime):
                    result[field_name] = field_value.isoformat()
                else:
                    result[field_name] = field_value

        if self.result_path:
            result['download_url'] = f'/public/report/download/{self.task_id}'

        return result

    def start_processing(self) -> None:
        """Начать обработку задачи"""
        if self.status != "pending":
            raise ValueError(f"Cannot start task with status {self.status}")
        self.status = "processing"
        self.started_at = datetime.now()
        self.progress = 0

    def update_progress(self, progress: int) -> None:
        """Обновить прогресс"""
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress

    def complete(self, result_path: str) -> None:
        """Завершить задачу успешно"""
        if self.status != "processing":
            raise ValueError(f"Cannot complete task with status {self.status}")
        self.status = "completed"
        self.completed_at = datetime.now()
        self.progress = 100
        self.result_path = result_path

    def fail(self, error: str) -> None:
        """Завершить задачу с ошибкой"""
        if self.status not in ["pending", "processing"]:
            raise ValueError(f"Cannot fail task with status {self.status}")
        self.status = "failed"
        self.failed_at = datetime.now()
        self.error = error