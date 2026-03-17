from .base import *  # noqa
import environ

env = environ.Env()

DEBUG = env.bool('DEBUG', default=False)

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://82.165.193.247:8006'])

DATABASES = {
    'default': env.db('DATABASE_URL')
}

# No SSL redirect — staging runs on plain HTTP without a domain
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Security headers still useful even on staging
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
