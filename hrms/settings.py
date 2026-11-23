"""
Django 项目配置（企业员工管理系统 HRMS）。

技术规范：
- Django 5.2 + MySQL
- 自定义用户模型（继承 AbstractUser），AUTH_USER_MODEL 指向 app01.User
- 语言与时区：zh-hans / Asia/Shanghai
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env（AI 大模型配置）
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥：开发环境使用固定值，生产环境应改为从环境变量读取
SECRET_KEY = "django-insecure-hrms-course-design-2026-@9v!k3x8#qm2$wz7le"

# SECURITY WARNING: 课程设计在开发阶段保持 DEBUG=True；上线前需关闭（对应选做 T13）
DEBUG = True

ALLOWED_HOSTS = ["*"]

# 应用注册
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app01.apps.App01Config",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 自定义：登录认证中间件（未登录统一拦截，见 app01/middleware/auth.py）
    "app01.middleware.auth.AuthMiddleware",
]

ROOT_URLCONF = "hrms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hrms.wsgi.application"

# 数据库：MySQL（127.0.0.1:3306，库名 hrms）
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "hrms",
        "USER": "root",
        "PASSWORD": "cjy060827cjy",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# 密码哈希：Django 内置 PBKDF2（默认），严禁明文 / 裸 MD5
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# 密码强度校验
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 自定义用户模型（关键配置，务必在首次迁移前设置）
AUTH_USER_MODEL = "app01.User"

# 国际化
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 静态文件与媒体文件（头像上传）
STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# 会话
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 2  # 两小时

# 登录相关
LOGIN_URL = "/login/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ========== AI 大模型 API 配置（T1: 全部走环境变量） ==========
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3.5-4B")
# 免费模型首次响应可能超过 30s，这里设 120s 下限，避免 .env 里配得过小导致必然超时
LLM_TIMEOUT = max(int(os.getenv("LLM_TIMEOUT", "120") or 120), 120)
LLM_MAX_INPUT_LEN = int(os.getenv("LLM_MAX_INPUT_LEN", "2000"))
