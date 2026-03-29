import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse

from ..application.use_cases import (
    ProcessFileUseCase,
    GetTaskStatusUseCase,
    GetQueueStatusUseCase,
    CreateTaskUseCase,
)
from ..infrastructure.repositories import TaskRepository
from ..config.settings import settings
from ..infrastructure.logger import logger
from .schemas import TaskResponse, QueueStatusResponse, ErrorResponse


router = APIRouter(prefix="/public/report", tags=["report"])


def get_task_repo() -> TaskRepository:
    from ..main import app
    return app.state.task_repo


def get_task_queue():
    from ..main import app
    return app.state.task_queue


def get_process_file_uc() -> ProcessFileUseCase:
    from ..main import app
    return app.state.process_file_uc


def get_get_status_uc() -> GetTaskStatusUseCase:
    from ..main import app
    return app.state.get_status_uc


def get_get_queue_uc() -> GetQueueStatusUseCase:
    from ..main import app
    return app.state.get_queue_uc


@router.post(
    "/export",
    status_code=status.HTTP_202_ACCEPTED,  # Всегда 202, никогда не блокируем
    response_model=TaskResponse,
    summary="Загрузить TXT файл для анализа",
)
async def upload_file(
    file: UploadFile = File(...),
    task_repo: TaskRepository = Depends(get_task_repo),
    task_queue: asyncio.Queue = Depends(get_task_queue),
):
    """Загрузка TXT файла"""
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Only TXT files are supported."
        )

    queue_size = task_queue.qsize()
    logger.info(f"New task. Queue size: {queue_size}")

    create_uc = CreateTaskUseCase(task_repo)

    upload_dir = settings.UPLOADS_DIR
    os.makedirs(upload_dir, exist_ok=True)
    temp_file = os.path.join(upload_dir, f"{file.filename}_{id(file)}.tmp")
    
    file_size = 0
    try:
        with open(temp_file, 'wb') as f:
            while True:
                chunk = await file.read(settings.CHUNK_SIZE_SMALL)
                if not chunk:
                    break
                f.write(chunk)
                file_size += len(chunk)

        task = task_repo.create(file.filename, file_extension)
        task.file_size_mb = file_size / (1024 * 1024)
        task_repo.save(task)

        final_temp_file = os.path.join(upload_dir, f"{task.task_id}.txt")
        os.rename(temp_file, final_temp_file)
        

        await task_queue.put((task.task_id, final_temp_file))
        
        logger.info(
            f"Task {task.task_id} added. "
            f"Size: {task.file_size_mb:.2f} MB. "
            f"Queue size: {task_queue.qsize()}"
        )
        
        return TaskResponse.model_validate(task.to_dict())
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Получить статус задачи",
)
async def get_status(
    task_id: str,
    get_status_uc: GetTaskStatusUseCase = Depends(get_get_status_uc),
):
    task = get_status_uc.execute(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task.to_dict())


@router.get(
    "/{task_id}/download",
    summary="Скачать результат",
)
async def download_result(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repo),
):
    task = task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task not completed yet. Current status: {task.status}"
        )
    
    if not task.result_path or not os.path.exists(task.result_path):
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        path=task.result_path,
        filename=f"{task.filename}_analysis.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get(
    "/queue/status",
    response_model=QueueStatusResponse,
    summary="Статус очереди"
)
async def get_queue_status(
    get_queue_uc: GetQueueStatusUseCase = Depends(get_get_queue_uc),
):
    """Получение статуса очереди"""
    status_obj = get_queue_uc.execute()
    return QueueStatusResponse.model_validate(status_obj.to_dict())