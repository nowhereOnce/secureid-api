"""
This module was created and tested with Python 3.11.
"""

from django.apps import AppConfig


class IdentityConfig(AppConfig):
    """
    Configuration for the Identity application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'identity'
