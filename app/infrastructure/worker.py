import asyncio
from typing import Callable

from ..infrastructure.logger import logger


class AdaptiveTaskWorker:
    """
    Адаптивный воркер:
    - Никогда не блокирует приём задач
    - Регулирует количество воркеров в зависимости от нагрузки
    - При большой очереди увеличивает конкуренцию
    """

    def __init__(
        self,
        task_queue: asyncio.Queue,
        min_workers: int = 2,
        max_workers: int = 10,
        target_queue_size: int = 10
    ):
        self.task_queue = task_queue
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.target_queue_size = target_queue_size
        self.current_workers = min_workers
        self.workers: list[asyncio.Task] = []
        self.running = False
        self.adjustment_task: asyncio.Task | None = None

    async def start(self, process_func: Callable):
        """Запуск воркеров"""
        self.running = True
        logger.info(f"Starting adaptive worker with {self.current_workers} workers")

        for i in range(self.current_workers):
            worker = asyncio.create_task(
                self._worker_loop(i, process_func)
            )
            self.workers.append(worker)

        self.adjustment_task = asyncio.create_task(
            self._adjust_workers(process_func)
        )

    async def _adjust_workers(self, process_func: Callable):
        """Динамическая регулировка количества воркеров"""
        while self.running:
            await asyncio.sleep(5)

            queue_size = self.task_queue.qsize()
            new_worker_count = self.current_workers

            # Если очередь растёт - добавляем воркеров
            if queue_size > self.target_queue_size:
                new_worker_count = min(
                    self.current_workers + 1,
                    self.max_workers
                )
                if new_worker_count > self.current_workers:
                    logger.info(
                        f"Queue growing ({queue_size} tasks). "
                        f"Increasing workers: {self.current_workers} -> {new_worker_count}"
                    )

            # Если очередь пуста - убираем лишних воркеров
            elif queue_size == 0 and self.current_workers > self.min_workers:
                new_worker_count = max(
                    self.current_workers - 1,
                    self.min_workers
                )
                if new_worker_count < self.current_workers:
                    logger.info(
                        f"Queue empty. "
                        f"Decreasing workers: {self.current_workers} -> {new_worker_count}"
                    )

            # Добавляем воркеров
            while self.current_workers < new_worker_count:
                worker_id = len(self.workers)
                worker = asyncio.create_task(
                    self._worker_loop(worker_id, process_func)
                )
                self.workers.append(worker)
                self.current_workers += 1
                logger.info(f"Added worker {worker_id}, total: {self.current_workers}")

            # Убираем воркеров
            while self.current_workers > new_worker_count and self.workers:
                worker = self.workers.pop()
                worker.cancel()
                self.current_workers -= 1
                logger.info(f"Removed worker, total: {self.current_workers}")

    async def _worker_loop(self, worker_id: int, process_func: Callable):
        """Цикл работы воркера"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                task_id, file_path = await self.task_queue.get()
                logger.info(f"Worker {worker_id} processing task {task_id}")

                await process_func(task_id, file_path)

                self.task_queue.task_done()
                logger.info(
                    f"Worker {worker_id} completed task {task_id}. "
                    f"Queue size: {self.task_queue.qsize()}"
                )

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                continue

    async def stop(self):
        """Остановка воркеров"""
        self.running = False

        if self.adjustment_task:
            self.adjustment_task.cancel()

        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All workers stopped")