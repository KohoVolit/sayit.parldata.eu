# Django settings for sejm.pl subdomain

import os

from sayit_parldata_eu.settings import *  # noqa

# manual settings
LANGUAGE_CODE = 'pl'
GOOGLE_ANALYTICS_ACCOUNT += '-??'

# automatically derived settings
_, parl = os.path.dirname(__file__).rsplit('/', 1)
country_code, parliament_code = parl.split('_', 1)
parliament_code = parliament_code.replace('_', '-')

DATABASES['default']['NAME'] = 'sayit_' + parl
MEDIA_ROOT += '/%s/%s' % (country_code, parliament_code)
CACHES['default']['LOCATION'] += '/%s/%s' % (country_code, parliament_code)
WSGI_APPLICATION = 'subdomains.%s.wsgi.application' % parl
