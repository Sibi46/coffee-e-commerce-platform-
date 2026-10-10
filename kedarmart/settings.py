import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ON_VERCEL = os.environ.get('VERCEL') == '1'
DEBUG = os.environ.get('DJANGO_DEBUG', 'false' if ON_VERCEL else 'true').lower() == 'true'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'development-only-change-before-deployment')
if not DEBUG and SECRET_KEY == 'development-only-change-before-deployment':
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY for production.')
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',') if host.strip()]
# This project's public alias may be absent from Vercel's generated host variables.
if 'kedarkhand.vercel.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('kedarkhand.vercel.app')
if ON_VERCEL:
    for key in ['VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL', 'VERCEL_BRANCH_URL']:
        if os.environ.get(key):
            ALLOWED_HOSTS.append(os.environ[key])
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
if 'https://kedarkhand.vercel.app' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://kedarkhand.vercel.app')
if ON_VERCEL:
    CSRF_TRUSTED_ORIGINS += ['https://' + host for host in ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1', '[::1]']]
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
                  'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'store']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware',
              'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
              'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
              'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'kedarmart.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True,
              'OPTIONS': {'context_processors': ['django.template.context_processors.request',
                          'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'kedarmart.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': os.environ.get('DB_PATH', str(BASE_DIR / 'db.sqlite3')), 'OPTIONS': {'timeout': 20}}}
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=0,
                                               ssl_require=ON_VERCEL or not DEBUG)
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
elif os.environ.get('DB_ENGINE') == 'postgresql':
    DATABASES['default'] = {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ['DB_NAME'],
                           'USER': os.environ['DB_USER'], 'PASSWORD': os.environ['DB_PASSWORD'],
                           'HOST': os.environ['DB_HOST'], 'PORT': os.environ.get('DB_PORT', '5432')}
if ON_VERCEL and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('Vercel requires a persistent PostgreSQL DATABASE_URL. SQLite is local-only.')
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.' + name} for name in
                           ['UserAttributeSimilarityValidator', 'MinimumLengthValidator', 'CommonPasswordValidator', 'NumericPasswordValidator']]
LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'dist']
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
if os.environ.get('MEDIA_S3_BUCKET'):
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': {
        'bucket_name': os.environ['MEDIA_S3_BUCKET'],
        'access_key': os.environ['MEDIA_S3_ACCESS_KEY'],
        'secret_key': os.environ['MEDIA_S3_SECRET_KEY'],
        'endpoint_url': os.environ.get('MEDIA_S3_ENDPOINT') or None,
        'region_name': os.environ.get('MEDIA_S3_REGION', 'auto'),
        'default_acl': None, 'querystring_auth': True, 'file_overwrite': False,
        'object_parameters': {'CacheControl': 'max-age=3600'},
    }}
elif ON_VERCEL:
    raise ImproperlyConfigured('Configure MEDIA_S3_BUCKET and credentials for persistent category image uploads.')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_FAILURE_VIEW = 'store.views.csrf_failure'
DATA_UPLOAD_MAX_MEMORY_SIZE = 100_000
