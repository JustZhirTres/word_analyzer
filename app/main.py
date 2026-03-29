# app/main.py
# ОБНОВИТЬ

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.endpoints import router
from .application.services.adaptive_analyzer import AdaptiveWordAnalyzer
from .application.services.excel_generator import ExcelGeneratorService
from .application.use_cases import (
    GetQueueStatusUseCase,
    GetTaskStatusUseCase,
    ProcessFileUseCase,
    CreateTaskUseCase,
)
from .config.settings import settings
from .infrastructure.logger import logger
from .infrastructure.repositories import TaskRepository
from .infrastructure.worker import AdaptiveTaskWorker

task_repo = TaskRepository()
task_queue = asyncio.Queue()
worker: AdaptiveTaskWorker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global worker

    # Создаём директории
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_STATS_DIR, exist_ok=True)
    os.makedirs(settings.TEST_FILES_DIR, exist_ok=True)

    # Инициализируем зависимости
    adaptive_analyzer = AdaptiveWordAnalyzer(settings.TEMP_STATS_DIR)
    excel_generator = ExcelGeneratorService()

    process_file_uc = ProcessFileUseCase(
        task_repo,
        adaptive_analyzer,
        excel_generator
    )

    # Сохраняем в app state
    app.state.task_repo = task_repo
    app.state.task_queue = task_queue
    app.state.process_file_uc = process_file_uc
    app.state.get_status_uc = GetTaskStatusUseCase(task_repo)
    app.state.get_queue_uc = GetQueueStatusUseCase(task_repo, task_queue)

    worker = AdaptiveTaskWorker(
        task_queue=task_queue,
        min_workers=2,
        max_workers=10,
        target_queue_size=10
    )

    async def process_task(task_id: str, file_path: str):
        await process_file_uc.execute(task_id, file_path)

    await worker.start(process_task)
    logger.info(f"Adaptive worker started (min={worker.min_workers}, max={worker.max_workers})")

    yield

    if worker:
        await worker.stop()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Word Frequency Analyzer API",
        description="Сервис для анализа частоты слов в TXT файлах (до 5GB)",
        version="2.0.0",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

