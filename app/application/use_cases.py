import asyncio
import os
from datetime import datetime
from typing import Optional

from app.domain.entities import Task, WordFrequencyStats
from app.infrastructure.repositories import TaskRepository
from app.infrastructure.file_parsers import FileParser
from app.infrastructure.excel_generator import ExcelGenerator
from app.domain.services import WordNormalizerService
from app.config.settings import settings


class ProcessFileUseCase:
    """Use case для обработки файла"""

    def __init__(
            self,
            task_repo: TaskRepository,
            file_parser: FileParser,
            normalizer: WordNormalizerService,
            excel_generator: ExcelGenerator
    ):
        self.task_repo = task_repo
        self.file_parser = file_parser
        self.normalizer = normalizer
        self.excel_generator = excel_generator

    async def execute(self, task: Task, file_path: str) -> Task:
        """Выполняет обработку файла"""
        try:
            task.status = 'processing'
            task.started_at = datetime.now()
            self.task_repo.update(task.task_id, status='processing', started_at=task.started_at)

            # Извлекаем текст из файла
            text_path = self.file_parser.extract_text(file_path, task.file_extension)
            is_extracted = (text_path != file_path)

            # Обрабатываем текст
            stats = await self._process_text(text_path, task)

            # Создаём Excel
            excel_buffer = await asyncio.get_event_loop().run_in_executor(
                None, self.excel_generator.generate, stats
            )

            # Сохраняем результат
            result_path = os.path.join(settings.RESULTS_DIR, f"{task.task_id}.xlsx")
            with open(result_path, "wb") as f:
                f.write(excel_buffer.getvalue())

            task.status = 'completed'
            task.completed_at = datetime.now()
            task.progress = 100
            task.result_path = result_path
            self.task_repo.update(
                task.task_id,
                status='completed',
                completed_at=task.completed_at,
                progress=100,
                result_path=result_path
            )

            # Удаляем временный файл если был создан
            if is_extracted and os.path.exists(text_path):
                os.unlink(text_path)

            return task

        except Exception as e:
            task.status = 'failed'
            task.failed_at = datetime.now()
            task.error = str(e)
            self.task_repo.update(
                task.task_id,
                status='failed',
                failed_at=task.failed_at,
                error=str(e)
            )
            raise

    async def _process_text(self, text_path: str, task: Task) -> WordFrequencyStats:
        """Потоковая обработка текста"""
        stats = WordFrequencyStats()
        line_num = 0

        file_size = os.path.getsize(text_path)
        bytes_processed = 0

        with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                lines = []
                for _ in range(1000):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
                    bytes_processed += len(line.encode('utf-8'))

                if not lines:
                    break

                # Обновляем прогресс
                if file_size > 0:
                    progress = int((bytes_processed / file_size) * 100)
                    task.progress = min(progress, 99)
                    self.task_repo.update(task.task_id, progress=task.progress)

                # Обрабатываем строки
                for line in lines:
                    if not line.strip():
                        line_num += 1
                        continue

                    line_counts = {}
                    words = line.strip().split()

                    for raw_word in words:
                        word_form = self.normalizer.normalize(raw_word)
                        if word_form:
                            line_counts[word_form] = line_counts.get(word_form, 0) + 1

                    for word_form, cnt in line_counts.items():
                        stats.add_word(word_form, line_num, cnt)

                    line_num += 1

                await asyncio.sleep(0)

        stats.ensure_line_counts(line_num)
        return stats


class GetTaskStatusUseCase:
    """Use case для получения статуса задачи"""

    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(self, task_id: str) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        return task.to_dict() if task else None


class GetQueueStatusUseCase:
    """Use case для получения статуса очереди"""

    def __init__(self, task_repo: TaskRepository, queue: asyncio.Queue):
        self.task_repo = task_repo
        self.queue = queue

    def execute(self) -> dict:
        tasks = self.task_repo.get_all()
        active_tasks = len([t for t in tasks.values() if t.status == 'processing'])

        return {
            'queue_size': self.queue.qsize(),
            'max_queue_size': settings.MAX_QUEUE_SIZE,
            'active_tasks': active_tasks,
            'total_tasks': len(tasks),
            'status': 'accepting' if self.queue.qsize() < settings.MAX_QUEUE_SIZE else 'busy'
        }