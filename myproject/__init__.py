"""
This module was created and tested with Python 3.11.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
