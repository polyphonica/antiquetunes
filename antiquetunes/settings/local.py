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

# Disable password hashing for faster tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

INTERNAL_IPS = ['127.0.0.1']
