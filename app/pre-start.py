"""Pre-start скрипт для инициализации приложения"""
import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config.settings import settings
from .infrastructure.logger import logger


def init_directories() -> None:
    """Создание необходимых директорий"""
    directories = [
        settings.RESULTS_DIR,
        settings.UPLOADS_DIR,
        settings.TEST_FILES_DIR,
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise


def main() -> None:
    """Основная функция pre-start"""
    logger.info("Running pre-start initialization...")

    init_directories()

    logger.info("Pre-start initialization completed successfully")


if __name__ == "__main__":
    main()