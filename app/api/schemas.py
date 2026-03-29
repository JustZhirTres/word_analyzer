"""Pydantic схемы для API ответов"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskResponse(BaseModel):
    """Схема ответа для задачи"""
    task_id: str
    status: str
    progress: int
    created_at: datetime
    file_name: str
    file_size_mb: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class QueueStatusResponse(BaseModel):
    """Схема ответа для статуса очереди"""
    queue_size: int
    max_queue_size: int
    active_tasks: int
    total_tasks: int
    status: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Схема ответа для ошибки"""
    detail: str
    status_code: int