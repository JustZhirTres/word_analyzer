import os

from ...infrastructure.repositories import TaskRepository
from ...application.services.adaptive_analyzer import AdaptiveWordAnalyzer
from ...application.services.excel_generator import ExcelGeneratorService
from ...infrastructure.logger import logger


class ProcessFileUseCase:
    """Обработка файла с адаптивной стратегией"""

    def __init__(
        self,
        task_repo: TaskRepository,
        adaptive_analyzer: AdaptiveWordAnalyzer,
        excel_generator: ExcelGeneratorService
    ) -> None:
        self.task_repo = task_repo
        self.adaptive_analyzer = adaptive_analyzer
        self.excel_generator = excel_generator

    async def execute(self, task_id: str, file_path: str) -> None:
        """Выполнить обработку файла"""
        task = self.task_repo.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        try:
            task.start_processing()
            self.task_repo.save(task)
            logger.info(f"Started processing task {task_id}")

            from ..services.word_normalizer import create_word_normalizer
            normalizer = create_word_normalizer()

            # Анализируем файл с адаптивной стратегией
            results = await self.adaptive_analyzer.analyze_file(
                file_path, task_id, normalizer
            )

            result_path = await self.excel_generator.generate(
                results,
                task.task_id,
                task.filename
            )

            task.complete(result_path)
            self.task_repo.save(task)
            logger.info(f"Completed processing task {task_id}")

            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Removed temp file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed processing task {task_id}: {e}")
            task.fail(str(e))
            self.task_repo.save(task)