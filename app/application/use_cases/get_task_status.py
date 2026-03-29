"""Use case для получения статуса задачи"""
from ...domain.entities import Task
from ...infrastructure.repositories import TaskRepository


class GetTaskStatusUseCase:
    """Получение статуса задачи"""

    def __init__(self, task_repo: TaskRepository) -> None:
        self.task_repo = task_repo

    def execute(self, task_id: str) -> Task | None:
        """Получить задачу"""
        return self.task_repo.get(task_id)