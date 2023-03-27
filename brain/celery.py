from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brain.settings')

app = Celery('brain', include=[
    'api.background_tasks.rate_logging',
    'api.background_tasks.logger',
    'api.background_tasks.emails',
    'api.background_tasks.business_central',
    'api.background_tasks.webhooks.tracking_status_change'
])

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object(settings)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
