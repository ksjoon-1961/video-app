from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_auth_context, get_current_user
from app.config import settings
from app.schemas import SignedUrlResponse, Video
from app.services import catalog, storage

router = APIRouter(prefix="/api")


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"id": user.get("sub"), "email": user.get("email")}


@router.get("/videos", response_model=list[Video])
async def videos(auth: dict = Depends(get_auth_context)):
    return await catalog.get_videos(auth["token"])


@router.get("/videos/{video_id}/url", response_model=SignedUrlResponse)
async def video_url(video_id: str, auth: dict = Depends(get_auth_context)):
    video = await catalog.get_video_by_id(video_id, auth["token"])
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    if not video.get("is_ready") or not video.get("storage_path"):
        raise HTTPException(status_code=409, detail="video not ready")
    url = await storage.create_signed_url(video["storage_path"], auth["token"])
    return {"url": url, "expires_in": settings.SIGNED_URL_TTL}
