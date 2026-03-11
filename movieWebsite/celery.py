from celery import Celery
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE","movieWebsite.settings")

app= Celery("movieWebsite")

app.config_from_object("django.conf:settings",namespace="CELERY")

# Only set up Redis if available
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    app.conf.update(BROKER_URL=redis_url,
                        CELERY_RESULT_BACKEND=redis_url)
else:
    # Use default in-memory broker for development
    app.conf.update(BROKER_URL='memory://',
                        CELERY_RESULT_BACKEND='db+sqlite:///celery.db')

app.autodiscover_tasks()