# Django settings for sejm.pl. subdomain

COUNTRY_CODE = 'pl'
PARLIAMENT_CODE = 'sejm'
PARLIAMENT_NAME = 'Sejm Rzeczypospolitej Polskiej'
LANGUAGE_CODE = 'pl'
GA_PROPERTY_ID = '??'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
