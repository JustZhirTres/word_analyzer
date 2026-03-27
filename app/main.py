import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.infrastructure.repositories import TaskRepository
from app.infrastructure.file_parsers import FileParser
from app.infrastructure.excel_generator import ExcelGenerator
from app.infrastructure.word_normalizer import create_word_normalizer
from app.application.use_cases import (
    ProcessFileUseCase,
    GetTaskStatusUseCase,
    GetQueueStatusUseCase
)
from app.api.endpoints import create_upload_routes

# Глобальные объекты
task_repo = TaskRepository()
task_queue = asyncio.Queue()
worker_started = False

# Инициализация зависимостей
file_parser = FileParser()
normalizer = create_word_normalizer()
excel_generator = ExcelGenerator()
process_file_uc = ProcessFileUseCase(task_repo, file_parser, normalizer, excel_generator)
get_status_uc = GetTaskStatusUseCase(task_repo)
get_queue_uc = GetQueueStatusUseCase(task_repo, task_queue)


async def worker():
    """Воркер для обработки задач"""
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

    while True:
        try:
            task_id, file_path = await task_queue.get()

            async with semaphore:
                try:
                    task = task_repo.get(task_id)
                    if task:
                        await process_file_uc.execute(task, file_path)
                except Exception as e:
                    print(f"Worker error for task {task_id}: {e}")
                finally:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    task_queue.task_done()

        except Exception as e:
            print(f"Worker error: {e}")
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст для запуска воркера"""
    global worker_started
    if not worker_started:
        asyncio.create_task(worker())
        worker_started = True
        print("Worker started successfully")
    yield
    print("Shutting down...")


def create_app() -> FastAPI:
    """Фабрика приложения"""
    app = FastAPI(title="Word Frequency Analyzer", lifespan=lifespan)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роуты
    router = create_upload_routes(
        task_repo, task_queue,
        process_file_uc, get_status_uc, get_queue_uc
    )
    app.include_router(router)

    # Корневая ручка
    @app.get("/")
    async def root():
        return {
            "message": "Word Frequency Analyzer API",
            "documentation": "/docs",
            "endpoints": {
                "upload": "POST /public/report/export",
                "status": "GET /public/report/status/{task_id}",
                "download": "GET /public/report/download/{task_id}",
                "queue": "GET /public/report/queue/status"
            }
        }

    return app


app = create_app()