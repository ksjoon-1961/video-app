import httpx
from fastapi import HTTPException

from app.config import settings


async def get_video_by_id(video_id: str, user_token: str) -> dict | None:
    url = f"{settings.SUPABASE_URL}/rest/v1/videos"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY or "",
        "Authorization": f"Bearer {user_token}",
    }
    params = {"select": "*", "id": f"eq.{video_id}", "limit": "1"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=headers, params=params)
            res.raise_for_status()
            items = res.json()
            return items[0] if items else None
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="영상 조회 실패")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Supabase에 연결할 수 없습니다")


async def get_videos(user_token: str) -> list[dict]:
    url = f"{settings.SUPABASE_URL}/rest/v1/videos"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY or "",
        "Authorization": f"Bearer {user_token}",
    }
    params = {"select": "*", "order": "sort_order"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=headers, params=params)
            res.raise_for_status()
            return res.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="카탈로그 조회 실패")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Supabase에 연결할 수 없습니다")
