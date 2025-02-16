import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SimpleCore.settings")

app = Celery("SimpleCore")

# Load task modules from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks from registered apps
app.autodiscover_tasks()

app.conf.task_routes = {
    'core.tasks.handle_new_order': {
        'queue': lambda args, kwargs: f"market_{args[0]['market']}"
    }
}

app.conf.worker_concurrency = 1
