from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_cleaning_service
from services.cleaning_service import CleaningService

router = APIRouter()


class CleaningTaskCreate(BaseModel):
    property_id: int
    check_out_date: str


class CleaningTaskResponse(BaseModel):
    id: int
    property_id: int
    check_out_date: str
    status: str
    assigned_cleaner_id: int | None

    class Config:
        from_attributes = True


class CleanerCreate(BaseModel):
    name: str
    phone: str
    email: str
    availability_schedule: dict[str, list[str]] = {}


@router.get("/tasks/{property_id}", response_model=list[CleaningTaskResponse])
async def get_cleaning_tasks(
    property_id: int,
    service: CleaningService = Depends(get_cleaning_service),
):
    return await service.get_tasks_for_property(property_id)


@router.post("/tasks", response_model=dict)
async def create_cleaning_task(
    data: CleaningTaskCreate,
    service: CleaningService = Depends(get_cleaning_service),
):
    task_id = await service.create_task(data.property_id, data.check_out_date)
    cleaner_id = await service.assign_cleaner(task_id)
    return {"task_id": task_id, "assigned_cleaner_id": cleaner_id}


@router.post("/tasks/{task_id}/complete")
async def complete_cleaning_task(
    task_id: int,
    service: CleaningService = Depends(get_cleaning_service),
):
    await service.complete_task(task_id)
    return {"status": "completed"}


@router.post("/tasks/{task_id}/confirm")
async def confirm_cleaning_task(
    task_id: int,
    service: CleaningService = Depends(get_cleaning_service),
):
    await service.confirm_task(task_id)
    return {"status": "confirmed"}
