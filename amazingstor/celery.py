import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amazingstor.settings")

app = Celery("amazingstor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'kill_old_carts': {
        'task': 'carts.tasks.kill_old_carts',
        'schedule': crontab(minute='*/1'),

    },

}
