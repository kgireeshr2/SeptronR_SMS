from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "School Management System"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://smsapi.septronr.com",
        "https://septronr-sms.onrender.com",
    ]

    DATABASE_URL: str = "postgresql+asyncpg://sms_user:sms_pass@localhost:5432/sms_db"

    # Render injects DATABASE_URL as "postgresql://..." — auto-fix to asyncpg driver
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = ""

    SMS_PROVIDER: str = "msg91"
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = "SCHOOL"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    META_WHATSAPP_TOKEN: str = ""
    META_PHONE_NUMBER_ID: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "School SMS"
    SMTP_FROM_EMAIL: str = "noreply@school.com"

    SENDGRID_API_KEY: str = ""

    FCM_SERVER_KEY: str = ""
    FIREBASE_PROJECT_ID: str = ""

    FRONTEND_URL: str = "http://localhost:5173"

    # Installation secret (set this to enable POST /api/v1/install)
    INSTALL_SECRET_KEY: str = ""

    # Super Admin Seed
    SUPER_ADMIN_EMAIL: str = "superadmin@sms.com"
    SUPER_ADMIN_USERNAME: str = "superadmin"
    SUPER_ADMIN_PASSWORD: str = "SuperAdmin@123"

    # Email aliases (used in email tasks)
    MAIL_HOST: str = ""
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "School SMS"
    MAIL_TLS: bool = True

    # ── AI / LLM (optional — enables agentic chat assistant) ──────────────
    # Supported providers: "groq" | "openai" | "none"
    # Set LLM_PROVIDER + corresponding key in .env to enable smart chat
    LLM_PROVIDER: str = "none"      # "groq" | "openai" | "none"
    GROQ_API_KEY: str = ""          # https://console.groq.com  (free tier available)
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.2


settings = Settings()
