from uuid import UUID
from pydantic import BaseModel


class Video(BaseModel):
    id: UUID
    name: str
    storage_path: str
    sort_order: int
    is_ready: bool = False


class SignedUrlResponse(BaseModel):
    url: str
    expires_in: int
