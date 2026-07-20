from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "SeptroSchool"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://septronr.com",
        "https://www.septronr.com",
        "https://smsapi.septronr.com",
        "https://septronr-sms.onrender.com",
    ]

    DATABASE_URL: str = "postgresql+asyncpg://sms_user:sms_pass@localhost:5432/sms_db"
    # DB TLS verification. Default keeps the encrypt-without-verify behaviour for
    # managed providers that don't distribute a CA. Set DB_SSL_VERIFY=true (and
    # optionally DB_SSL_ROOT_CERT=/path/to/ca.pem, e.g. the Aiven CA) in production
    # to authenticate the DB server and prevent MITM on the database link.
    DB_SSL_VERIFY: bool = False
    DB_SSL_ROOT_CERT: str = ""

    # Render/Aiven inject DATABASE_URL as "postgres://..." or "postgresql://..."
    # — auto-fix to the asyncpg driver prefix. (The sslmode query param, if any,
    # is handled in db/session.py.)
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+" not in v.split("://")[0]:
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
    S3_PUBLIC_BASE_URL: str = ""   # optional CDN/base URL for objects (else uses S3 virtual-host URL)

    # ── Payments (Razorpay) ───────────────────────────────────────────────
    # Per-school keys live in the Settings 'fees' category (razorpay_key_id /
    # razorpay_key_secret / razorpay_webhook_secret). These are the global fallback.
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    SMS_PROVIDER: str = "msg91"
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = "SCHOOL"
    # Canonical MSG91 fields used by the notification pipeline (fall back to *_AUTH_KEY/_SENDER_ID)
    MSG91_API_KEY: str = ""        # = MSG91_AUTH_KEY (auth key for api.msg91.com)
    MSG91_SENDER: str = ""         # = MSG91_SENDER_ID
    MSG91_TEMPLATE_ID: str = ""    # DLT flow/template id (required for transactional SMS in India)

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    META_WHATSAPP_TOKEN: str = ""
    META_PHONE_NUMBER_ID: str = ""
    META_WHATSAPP_VERIFY_TOKEN: str = "sms_whatsapp_verify"
    # Meta App Secret — used to verify the X-Hub-Signature-256 on inbound webhooks.
    # When set, every webhook POST must carry a valid HMAC-SHA256 signature or it is rejected.
    META_APP_SECRET: str = ""
    META_WHATSAPP_API_VERSION: str = "v18.0"
    WHATSAPP_DEFAULT_LANG: str = "en"

    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"  # Public URL of this API server

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "SeptroSchool"
    SMTP_FROM_EMAIL: str = "noreply@school.com"

    SENDGRID_API_KEY: str = ""

    FCM_SERVER_KEY: str = ""
    FIREBASE_PROJECT_ID: str = ""

    # ── Push notifications ────────────────────────────────────────────────
    # Web Push (VAPID) — generate with `vapid --gen` or the py_vapid CLI.
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@school.com"
    # Expo push (mobile app). Access token optional unless the project enforces it.
    EXPO_ACCESS_TOKEN: str = ""
    EXPO_PUSH_URL: str = "https://exp.host/--/api/v2/push/send"

    # Installation secret (set this to enable POST /api/v1/install)
    INSTALL_SECRET_KEY: str = ""

    # CAPTCHA for public, unauthenticated forms (admission apply / enquiry).
    # Leave CAPTCHA_SECRET blank to disable. Provider: "hcaptcha" | "recaptcha".
    CAPTCHA_PROVIDER: str = "hcaptcha"
    CAPTCHA_SECRET: str = ""

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
    MAIL_FROM_NAME: str = "SeptroSchool"
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
