import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Настройки приложения"""

    MAX_CONCURRENT_TASKS: int = 2
    MAX_QUEUE_SIZE: int = 0

    CHUNK_SIZE_SMALL: int = 1024 * 1024  # 1MB для маленьких файлов
    CHUNK_SIZE_LARGE: int = 10 * 1024 * 1024  # 10MB для больших файлов

    HYBRID_THRESHOLD: int = 100 * 1024 * 1024  # 100MB
    STREAMING_THRESHOLD: int = 1024 * 1024 * 1024  # 1GB

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    RESULTS_DIR: str = os.path.join(BASE_DIR, "results")
    UPLOADS_DIR: str = os.path.join(BASE_DIR, "uploads")
    TEMP_STATS_DIR: str = os.path.join(BASE_DIR, "temp_stats")
    TEST_FILES_DIR: str = os.path.join(BASE_DIR, "test_files")

    ALLOWED_EXTENSIONS: set[str] = field(default_factory=lambda: {'.txt'})

    HOST: str = "127.0.0.1"
    PORT: int = 8000


settings = Settings()