from fastapi import APIRouter, Depends

from app.auth import get_current_user

router = APIRouter(prefix="/api")


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"id": user.get("sub"), "email": user.get("email")}
