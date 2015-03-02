# Django settings for skupstina.rs. subdomain

COUNTRY_CODE = 'rs'
PARLIAMENT_CODE = 'skupstina'
PARLIAMENT_NAME = 'Народна скупштина Републике Србије'
LANGUAGE_CODE = 'sr'
GA_PROPERTY_ID = '??'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
