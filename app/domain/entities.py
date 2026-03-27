from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid


@dataclass
class WordStatistics:
    """Статистика по одному слову"""
    total: int = 0
    per_line: List[int] = field(default_factory=list)


@dataclass
class WordFrequencyStats:
    """Статистика по всем словам"""
    stats: Dict[str, WordStatistics] = field(default_factory=dict)

    def add_word(self, word_form: str, line_num: int, count: int = 1):
        """Добавляет вхождение слова"""
        if word_form not in self.stats:
            self.stats[word_form] = WordStatistics()

        word_stat = self.stats[word_form]

        # Расширяем список per_line если нужно
        if len(word_stat.per_line) <= line_num:
            word_stat.per_line.extend([0] * (line_num - len(word_stat.per_line) + 1))

        word_stat.per_line[line_num] += count
        word_stat.total += count

    def ensure_line_counts(self, total_lines: int):
        """Выравнивает списки per_line для всех слов"""
        for word_stat in self.stats.values():
            if len(word_stat.per_line) < total_lines:
                word_stat.per_line.extend([0] * (total_lines - len(word_stat.per_line)))


@dataclass
class Task:
    """Сущность задачи"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = 'queued'
    progress: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error: Optional[str] = None

    filename: str = ''
    file_size_mb: float = 0.0
    file_extension: str = ''
    result_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Преобразует в словарь для API"""
        result = {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'file_name': self.filename,
            'file_size_mb': self.file_size_mb
        }

        if self.started_at:
            result['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        if self.failed_at:
            result['failed_at'] = self.failed_at.isoformat()
        if self.error:
            result['error'] = self.error
        if self.result_path:
            result['download_url'] = f'/public/report/download/{self.task_id}'

        return result