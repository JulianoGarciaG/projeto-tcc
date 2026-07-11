from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-=0ep41=asz_+utd_sy_7g-a_lm4cc+e()nt8%a_a(3ngj%w_9t')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin
]

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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                'imoveis.context_processors.notificacoes_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Storage do django.contrib.messages — persiste uma cópia de cada mensagem em
# NotificacaoUsuario (histórico por usuário), além do comportamento padrão de
# toast efêmero (ver imoveis/message_storage.py).
MESSAGE_STORAGE = 'imoveis.message_storage.PersistentFallbackStorage'

# Banco de dados — usar SQLite em dev, PostgreSQL em prod via .env
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')

if DB_ENGINE == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'gestao_imoveis'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
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

# Arquivos estáticos — servidos via Whitenoise em produção (sem Nginx dedicado)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Arquivos de mídia (uploads: PDFs, imagens)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Armazenamento de arquivos (uploads) — plugável via .env, no mesmo padrão do
# DB_ENGINE acima: FileSystemStorage em dev, S3 (Cloudflare R2) em prod, sem
# mudar código de aplicação (todos os FileFields usam o storage "default").
#
# Para habilitar R2 (compatível com a API S3), no .env:
#   STORAGE_BACKEND=s3
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY  (API Token do R2)
#   AWS_STORAGE_BUCKET_NAME                    (nome do bucket no R2)
#   AWS_S3_ENDPOINT_URL                        (endpoint da conta no R2)
#   AWS_S3_CUSTOM_DOMAIN (opcional, se o bucket tiver domínio público)
STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'filesystem')

if STORAGE_BACKEND == 's3':
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN') or None
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'auto')
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = True
    AWS_QUERYSTRING_AUTH = False

    STORAGES = {
        'default': {'BACKEND': 'storages.backends.s3.S3Storage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
else:
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Dados fixos do locador jurídico (Shelter) — usados no PDF de contrato
# (imoveis/views.py:_gerar_pdf_contrato). O locador do contrato gerado é
# sempre a Shelter, independentemente do Proprietario cadastrado do imóvel.
SHELTER_LOCADOR = {
    'razao_social': 'SHELTER ADMINISTRADORA DE BENS PRÓPRIOS LTDA.',
    'cnpj': '65.764.617/0001-29',
    'representante_nome': 'JOSÉ MÍLTON GARCIA',
    'representante_rg': '19.249.055',
    'representante_cpf': '493.583.406-49',
    'endereco': 'Rua São Paulo, 134, Centro, Poços de Caldas/MG',
    'telefone': '035-3722-1838',
    'pix_chave': '65.764.617/0001-29',
    'foro': 'Comarca de Poços de Caldas, MG',
}

# Autenticação
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
