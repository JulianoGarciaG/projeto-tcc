from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-=0ep41=asz_+utd_sy_7g-a_lm4cc+e()nt8%a_a(3ngj%w_9t')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'imoveis',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Banco de dados — usar SQLite em dev, MySQL em prod via .env
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')

if DB_ENGINE == 'django.db.backends.mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'gestao_imoveis'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Arquivos de mídia (uploads: PDFs, imagens)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Armazenamento de arquivos (uploads) — plugável via .env, no mesmo padrão do
# DB_ENGINE acima: FileSystemStorage em dev, S3 no futuro sem mudar código de
# aplicação (todos os FileFields usam o storage "default" do STORAGES).
#
# Passo futuro para habilitar S3 (NÃO implementado nesta rodada — boto3 e
# django-storages NÃO devem ser instalados agora):
#   1. pip install django-storages boto3 (e adicionar ao requirements.txt)
#   2. No .env: STORAGE_BACKEND=s3 + AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
#      AWS_STORAGE_BUCKET_NAME e AWS_S3_REGION_NAME
#   3. Trocar o backend do ramo 's3' abaixo por
#      'storages.backends.s3.S3Storage' (lendo as credenciais do .env)
STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'filesystem')

if STORAGE_BACKEND == 's3':
    # Placeholder: falha explícita até django-storages/boto3 serem adicionados
    # (mesmo comportamento do DB_ENGINE=mysql sem mysqlclient instalado).
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'STORAGE_BACKEND=s3 requer django-storages e boto3 — '
        'ver o passo a passo comentado em core/settings.py.'
    )

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autenticação
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
