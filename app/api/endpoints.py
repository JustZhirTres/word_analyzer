import os
import asyncio
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse

from app.config.settings import settings
from app.domain.entities import Task
from app.infrastructure.repositories import TaskRepository
from app.application.use_cases import ProcessFileUseCase, GetTaskStatusUseCase, GetQueueStatusUseCase

router = APIRouter()


def create_upload_routes(
        task_repo: TaskRepository,
        task_queue: asyncio.Queue,
        process_file_uc: ProcessFileUseCase,
        get_status_uc: GetTaskStatusUseCase,
        get_queue_uc: GetQueueStatusUseCase
):
    """Создаёт эндпоинты с зависимостями"""

    @router.post("/public/report/export")
    async def export_report(file: UploadFile = File(...)):
        """Загрузка файла и создание задачи"""
        # Проверяем расширение
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                400,
                f"Unsupported file format. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Проверяем очередь
        if task_queue.qsize() >= settings.MAX_QUEUE_SIZE:
            raise HTTPException(429, "Server is busy. Please try again later.")

        # Сохраняем файл
        task = Task(
            filename=file.filename,
            file_extension=file_extension
        )

        upload_dir = os.path.join(settings.BASE_DIR, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        temp_file = os.path.join(upload_dir, f"{task.task_id}{file_extension}")

        try:
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = await file.read(settings.CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)

            file_size = os.path.getsize(temp_file)
            task.file_size_mb = file_size / (1024 * 1024)
            task_repo.save(task)

            # Добавляем в очередь
            await task_queue.put((task.task_id, temp_file))

            return JSONResponse({
                'task_id': task.task_id,
                'status': 'queued',
                'queue_position': task_queue.qsize(),
                'file_size_mb': task.file_size_mb,
                'file_format': file_extension[1:].upper(),
                'check_status_url': f'/public/report/status/{task.task_id}'
            })

        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise HTTPException(500, f"Failed to process request: {str(e)}")

    @router.get("/public/report/status/{task_id}")
    async def get_task_status(task_id: str):
        """Получение статуса задачи"""
        result = get_status_uc.execute(task_id)
        if not result:
            raise HTTPException(404, "Task not found")
        return JSONResponse(result)

    @router.get("/public/report/download/{task_id}")
    async def download_report(task_id: str):
        """Скачивание готового отчёта"""
        task = task_repo.get(task_id)
        if not task:
            raise HTTPException(404, "Task not found")

        if task.status != 'completed':
            raise HTTPException(400, f"Task not completed. Status: {task.status}")

        if not task.result_path or not os.path.exists(task.result_path):
            raise HTTPException(404, "Result file not found")

        original_name = task.filename.rsplit('.', 1)[0]
        filename = f"{original_name}_report.xlsx"

        return StreamingResponse(
            open(task.result_path, 'rb'),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @router.get("/public/report/queue/status")
    async def get_queue_status():
        """Статус очереди"""
        return JSONResponse(get_queue_uc.execute())

    return router