#!/usr/bin/env python
"""
Django manage.py script for Smart Crédit
"""

import os
import sys


def main():
    """Run administrative tasks."""
    # Add backend directory to Python path
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_credit.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
