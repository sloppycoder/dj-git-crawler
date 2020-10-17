import os

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")

# application = get_wsgi_application()
# just use gunicorn to serve static content, it's ok for small volumes
application = StaticFilesHandler(get_wsgi_application())