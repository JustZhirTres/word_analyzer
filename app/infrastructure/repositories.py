from typing import Dict, Optional
from app.domain.entities import Task


class TaskRepository:
    """Хранилище задач (in-memory)"""

    def __init__(self):
        self._storage: Dict[str, Task] = {}

    def save(self, task: Task) -> Task:
        """Сохраняет задачу"""
        self._storage[task.task_id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Получает задачу по ID"""
        return self._storage.get(task_id)

    def get_all(self) -> Dict[str, Task]:
        """Возвращает все задачи"""
        return self._storage

    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Обновляет поля задачи"""
        task = self.get(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
        return task