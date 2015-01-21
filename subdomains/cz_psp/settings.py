# Django settings for psp.cz subdomain

from sayit_parldata_eu.settings import *  # noqa

DATABASES['default']['NAME'] = 'sayit_cz_psp'
LANGUAGE_CODE = 'cz'
MEDIA_ROOT += '/cz/psp'
WSGI_APPLICATION = 'subdomains.cz_psp.wsgi.application'
GOOGLE_ANALYTICS_ACCOUNT += '-??'
