import asyncio
from dataclasses import dataclass

from ...infrastructure.repositories import TaskRepository
from ...config.settings import settings


@dataclass
class QueueStatus:
    queue_size: int
    max_queue_size: int
    active_tasks: int
    total_tasks: int
    status: str

    def to_dict(self) -> dict:
        return {
            'queue_size': self.queue_size,
            'max_queue_size': self.max_queue_size,
            'active_tasks': self.active_tasks,
            'total_tasks': self.total_tasks,
            'status': self.status
        }


class GetQueueStatusUseCase:
    def __init__(self, task_repo: TaskRepository, queue: asyncio.Queue):
        self.task_repo = task_repo
        self.queue = queue

    def execute(self) -> QueueStatus:
        tasks = self.task_repo.get_all()
        active_tasks = len([t for t in tasks.values() if t.status == 'processing'])

        queue_status = 'accepting'

        return QueueStatus(
            queue_size=self.queue.qsize(),
            max_queue_size=settings.MAX_QUEUE_SIZE,
            active_tasks=active_tasks,
            total_tasks=len(tasks),
            status=queue_status
        )