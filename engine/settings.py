import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-@uav7p8ckab#8#t77kj#gcm*vo)9+eib2^-+-@uyxwn194+!rj'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',
    'widget_tweaks',
    'dpanel',
]


LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
ROOT_URLCONF = 'engine.urls'


AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dpanel.middleware.static.StaticFilesMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'dpanel.context.context',
            ],
        },
    },
]

WSGI_APPLICATION = 'engine.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "dpanel.db",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'statics',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('ar', _('Arabic')),
    ('en', _('English')),
]

LOCALE_PATHS = (
    BASE_DIR / "locale",
)

COOKIE_NAME = 'dpanel'
LANGUAGE_COOKIE_NAME = 'dpanel_lang'
LANGUAGE_COOKIE_SECURE = True


MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

SERVER_FOLDER = '/var/server'
DPANEL_FOLDER = f'{SERVER_FOLDER}/dpanel'
VENV_FOLDER = f'{SERVER_FOLDER}/venv'
SSL_FOLDER = f'{SERVER_FOLDER}/ssl'
BACKUP_FOLDER = f'{SERVER_FOLDER}/backup'
WWW_FOLDER = '/var/www'
NGINX_FOLDER = '/etc/nginx'
UWSGI_FOLDER = '/etc/uwsgi'