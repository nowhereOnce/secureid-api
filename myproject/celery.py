import os
from celery import Celery

# Establece el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Usamos el prefijo CELERY_ en settings.py para las configuraciones
app.config_from_object('django.conf:settings', namespace='CELERY')

# Busca tareas automáticamente en todas tus apps (como identity/tasks.py)
app.autodiscover_tasks()