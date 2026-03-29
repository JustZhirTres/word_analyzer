"""Репозиторий для хранения задач"""
from typing import Any

from ..domain.entities import Task


class TaskRepository:
    """In-memory репозиторий задач"""

    def __init__(self) -> None:
        self._storage: dict[str, Task] = {}

    def create(self, filename: str, file_extension: str) -> Task:
        """Создать новую задачу с использованием фабричного метода"""
        task = Task.create(filename, file_extension)
        self._storage[task.task_id] = task
        return task

    def save(self, task: Task) -> None:
        """Сохранить задачу"""
        self._storage[task.task_id] = task

    def get(self, task_id: str) -> Task | None:
        """Получить задачу по ID"""
        return self._storage.get(task_id)

    def get_all(self) -> dict[str, Task]:
        """Получить все задачи"""
        return self._storage.copy()

    def update(self, task_id: str, **kwargs: Any) -> Task | None:
        """Обновить поля задачи"""
        task = self.get(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self.save(task)
        return task