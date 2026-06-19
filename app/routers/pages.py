from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "supabase_url": settings.SUPABASE_URL or "",
        "supabase_anon_key": settings.SUPABASE_ANON_KEY or "",
    })
