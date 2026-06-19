from uuid import UUID
from pydantic import BaseModel


class Video(BaseModel):
    id: UUID
    name: str
    storage_path: str
    sort_order: int
