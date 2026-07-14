import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "apps.assignments", "apps.ai_tools", "apps.workfile", "apps.marketing", "apps.billing", "apps.preflight",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates", "DIRS":[BASE_DIR / "templates"], "APP_DIRS":True,
    "OPTIONS":{"context_processors":["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "assets"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGE_BACKEND = os.getenv("COAPPRAISER_STORAGE_BACKEND", "r2" if os.getenv("R2_BUCKET_NAME") else "local")
STATIC_STORAGE_BACKEND = "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage"
if STORAGE_BACKEND == "r2":
    R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
    R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "")
    R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com")
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": R2_BUCKET_NAME,
                "endpoint_url": R2_ENDPOINT_URL,
                "region_name": "auto",
                "access_key": os.getenv("R2_ACCESS_KEY_ID", ""),
                "secret_key": os.getenv("R2_SECRET_ACCESS_KEY", ""),
                "querystring_auth": True,
                "file_overwrite": False,
                "default_acl": None,
                "addressing_style": "path",
                "object_parameters": {"CacheControl": "private, max-age=0, no-store"},
            },
        },
        "staticfiles": {"BACKEND": STATIC_STORAGE_BACKEND},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": MEDIA_ROOT}},
        "staticfiles": {"BACKEND": STATIC_STORAGE_BACKEND},
    }
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/app/preflight/"
LOGOUT_REDIRECT_URL = "/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
COAPPRAISER_LLM_PROVIDER = os.getenv("COAPPRAISER_LLM_PROVIDER", "mock")
COAPPRAISER_LLM_MODEL = os.getenv("COAPPRAISER_LLM_MODEL", "mock-revision-response")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Accept the explicit private-key name used by Railway, while retaining the
# documented STRIPE_SECRET_KEY name. Never use a webhook signing secret as an
# API key if a misconfigured environment contains one.
_stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_SECRET_KEY = (
    _stripe_secret_key
    if _stripe_secret_key.startswith("sk_")
    else os.getenv("STRIPE_PRIVATE_KEY", "")
)
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_ELITE = os.getenv("STRIPE_PRICE_ELITE", "")
STRIPE_PRICE_PREFLIGHT = os.getenv("STRIPE_PRICE_PREFLIGHT", "")
COAPPRAISER_BILLING_MODE = os.getenv("COAPPRAISER_BILLING_MODE", "mock" if DEBUG else "stripe")
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
