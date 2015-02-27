# Django settings for kuvendi.kv. subdomain

COUNTRY_CODE = 'kv'
PARLIAMENT_CODE = 'kuvendi'
LANGUAGE_CODE = 'sq'
GA_PROPERTY_ID = '??'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
