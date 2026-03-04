from infrastructure.database.repository import CleanerRepository, CleaningTaskRepository


class CleaningService:
    def __init__(
        self,
        cleaner_repo: CleanerRepository,
        task_repo: CleaningTaskRepository,
    ):
        self.cleaner_repo = cleaner_repo
        self.task_repo = task_repo

    async def create_task(self, property_id: int, check_out_date: str) -> int:
        return await self.task_repo.create(
            property_id=property_id,
            check_out_date=check_out_date,
        )

    async def assign_cleaner(self, task_id: int) -> int | None:
        task = await self.task_repo.get_by_id(task_id)
        cleaners = await self.cleaner_repo.get_for_property(task.property_id)

        for cleaner in sorted(cleaners, key=lambda c: c.priority):
            is_available = await self.cleaner_repo.check_availability(
                cleaner.cleaner_id, task.check_out_date
            )
            if is_available:
                await self.task_repo.assign(task_id, cleaner.cleaner_id)
                return cleaner.cleaner_id

        return None

    async def confirm_task(self, task_id: int) -> None:
        await self.task_repo.update_status(task_id, "confirmed")

    async def complete_task(self, task_id: int) -> None:
        await self.task_repo.update_status(task_id, "completed")

    async def get_tasks_for_property(self, property_id: int) -> list:
        return await self.task_repo.get_by_property(property_id)
