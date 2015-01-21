# Django settings for nrsr.sk subdomain

from sayit_parldata_eu.settings import *  # noqa

DATABASES['default']['NAME'] = 'sayit_sk_nrsr'
LANGUAGE_CODE = 'sk'
MEDIA_ROOT += '/sk/nrsr'
WSGI_APPLICATION = 'subdomains.sk_nrsr.wsgi.application'
GOOGLE_ANALYTICS_ACCOUNT += '-??'
