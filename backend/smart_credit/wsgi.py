"""
WSGI config for Smart Crédit project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_credit.settings.production')

application = get_wsgi_application()
