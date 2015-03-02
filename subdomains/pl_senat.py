# Django settings for senat.pl. subdomain

COUNTRY_CODE = 'pl'
PARLIAMENT_CODE = 'senat'
PARLIAMENT_NAME = 'Senat Rzeczypospolitej Polskiej'
LANGUAGE_CODE = 'pl'
GA_PROPERTY_ID = '??'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
