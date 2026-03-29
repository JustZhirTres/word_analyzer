"""Use case для создания задачи"""
import os
from typing import BinaryIO

from ...domain.entities import Task
from ...infrastructure.repositories import TaskRepository
from ...config.settings import settings
from ...infrastructure.logger import logger


class CreateTaskUseCase:
    """Создание задачи из загруженного файла"""

    def __init__(self, task_repo: TaskRepository) -> None:
        self.task_repo = task_repo

    async def execute(
            self,
            filename: str,
            file_extension: str,
            content: bytes
    ) -> tuple[Task, str]:
        """
        Создать задачу и сохранить файл

        Returns:
            tuple[Task, str]: (задача, путь к временному файлу)
        """
        # Создаём задачу
        task = self.task_repo.create(filename, file_extension)

        # Сохраняем файл
        upload_dir = settings.UPLOADS_DIR
        os.makedirs(upload_dir, exist_ok=True)
        temp_file = os.path.join(upload_dir, f"{task.task_id}{file_extension}")

        try:
            with open(temp_file, 'wb') as f:
                f.write(content)

            file_size = os.path.getsize(temp_file)
            task.file_size_mb = file_size / (1024 * 1024)
            self.task_repo.save(task)

            logger.info(f"Task {task.task_id} created, file size: {task.file_size_mb:.2f} MB")
            return task, temp_file

        except Exception as e:
            logger.error(f"Failed to save file for task {task.task_id}: {e}")
            raise