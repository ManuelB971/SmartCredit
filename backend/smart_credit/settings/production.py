"""
Production settings for Smart Crédit project.
"""

from .base import *

DEBUG = False
ALLOWED_HOSTS = ['smartcredit.fr', 'www.smartcredit.fr']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net'),
    'style-src': ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net'),
}

# Production database
DATABASES['default']['HOST'] = os.getenv('DB_HOST', 'prod-db-host')
DATABASES['default']['USER'] = os.getenv('DB_USER')
DATABASES['default']['PASSWORD'] = os.getenv('DB_PASSWORD')

# Email - Real SMTP in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# CORS - Restrict in production
CORS_ALLOWED_ORIGINS = [
    'https://smartcredit.fr',
    'https://www.smartcredit.fr',
]

# Logging - Less verbose
LOGGING['root']['level'] = 'WARNING'
