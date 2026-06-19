from fastapi import APIRouter, Depends

from app.auth import get_auth_context, get_current_user
from app.schemas import Video
from app.services import catalog

router = APIRouter(prefix="/api")


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"id": user.get("sub"), "email": user.get("email")}


@router.get("/videos", response_model=list[Video])
async def videos(auth: dict = Depends(get_auth_context)):
    return await catalog.get_videos(auth["token"])
