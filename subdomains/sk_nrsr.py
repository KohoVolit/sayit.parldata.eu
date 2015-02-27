# Django settings for nrsr.sk. subdomain

COUNTRY_CODE = 'sk'
PARLIAMENT_CODE = 'nrsr'
LANGUAGE_CODE = 'sk'
GA_PROPERTY_ID = '??'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
