import httpx
from fastapi import HTTPException

from app.config import settings


async def create_signed_url(storage_path: str, user_token: str) -> str:
    url = (
        f"{settings.SUPABASE_URL}/storage/v1/object/sign"
        f"/{settings.VIDEO_BUCKET}/{storage_path}"
    )
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY or "",
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                url,
                headers=headers,
                json={"expiresIn": settings.SIGNED_URL_TTL},
            )
            res.raise_for_status()
            signed_path = res.json().get("signedURL", "")
            if not signed_path:
                raise HTTPException(status_code=500, detail="signed URL 생성 실패")
            return f"{settings.SUPABASE_URL}/storage/v1{signed_path}"
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="signed URL 생성 실패")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Storage에 연결할 수 없습니다")
