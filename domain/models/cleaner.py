from dataclasses import dataclass


@dataclass
class Cleaner:
    name: str
    phone: str
    email: str
    availability_schedule: dict[str, list[str]]
    id: int | None = None


@dataclass
class PropertyCleaner:
    property_id: int
    cleaner_id: int
    priority: int = 1


@dataclass
class CleaningTask:
    property_id: int
    check_out_date: str
    status: str = "pending"
    assigned_cleaner_id: int | None = None
    id: int | None = None
