from pathlib import Path
import os
from dotenv import load_dotenv
import environ
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env only in development
if not os.environ.get("RENDER"):  # RENDER env var is set by Render platform
    load_dotenv(BASE_DIR / ".env")

env = environ.Env()
if not os.environ.get("RENDER"):
    environ.Env.read_env(BASE_DIR / '.env')

# --- Security ---
SECRET_KEY = env('DJANGO_SECRET_KEY')

DEBUG = os.environ.get("DEBUG", "False") == "True"

# Allow all hosts (Render will assign dynamic hostname)
ALLOWED_HOSTS = ["*",]

# --- Installed Apps ---
INSTALLED_APPS = [
    'widget_tweaks',
    'myapp',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be above SessionMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# --- DATABASE ---
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600
    )
}

# Only set sslmode if not already in the URL
if "sslmode" not in DATABASES["default"].get("OPTIONS", {}):
    DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}



# --- Password Validators ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC Files ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Media Files ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Default PK ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Razorpay Keys ---
RAZOR_SECRET_KEY = env('RAZOR_SECRET_KEY')
RAZOR_KEY_ID = env('RAZOR_KEY_ID')

# --- Redirects ---
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'index'
