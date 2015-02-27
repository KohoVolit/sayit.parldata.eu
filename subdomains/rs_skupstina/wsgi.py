import os

_, parl = os.path.dirname(__file__).rsplit('/', 1)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "subdomains.%s.settings" % parl)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
