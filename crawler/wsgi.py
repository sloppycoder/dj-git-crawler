import os

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")

# application = get_wsgi_application()
# just use gunicorn to serve static content, it's ok for small volumes
application = StaticFilesHandler(get_wsgi_application())
