"""
This module was created and tested with Python 3.11.

Celery configuration for the project.
"""
import os
from celery import Celery

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Use CELERY_ settings in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps (e.g. identity/tasks.py)
app.autodiscover_tasks()
