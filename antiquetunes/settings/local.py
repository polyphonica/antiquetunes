from .base import *  # noqa

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Show emails in console during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all hosts locally
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

INTERNAL_IPS = ['127.0.0.1']
