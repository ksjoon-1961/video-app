import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str | None = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET: str | None = os.getenv("SUPABASE_JWT_SECRET")
    VIDEO_BUCKET: str = os.getenv("VIDEO_BUCKET", "videos")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
