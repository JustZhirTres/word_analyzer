# app/config/settings.py
import os
from dataclasses import dataclass, field
from typing import Set


@dataclass
class Settings:
    """Настройки приложения"""

    # Очередь и обработка
    MAX_CONCURRENT_TASKS: int = 2
    MAX_QUEUE_SIZE: int = 50
    CHUNK_SIZE: int = 1024 * 1024  # 1MB

    # Пути
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    RESULTS_DIR: str = os.path.join(BASE_DIR, "results")
    TEST_FILES_DIR: str = os.path.join(BASE_DIR, "test_files")

    # Поддерживаемые форматы (используем field с default_factory)
    ALLOWED_EXTENSIONS: Set[str] = field(default_factory=lambda: {'.txt', '.docx', '.pdf'})

    def __post_init__(self):
        """Создаём папки если их нет"""
        os.makedirs(self.RESULTS_DIR, exist_ok=True)
        os.makedirs(self.TEST_FILES_DIR, exist_ok=True)


settings = Settings()