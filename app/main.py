from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import api, pages

app = FastAPI(title="VideoApp")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(api.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
