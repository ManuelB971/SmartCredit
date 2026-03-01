"""
Development settings for Smart Crédit project.
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Email - Console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS - Allow all in development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
]

# Logging - More verbose
LOGGING['root']['level'] = 'DEBUG'
