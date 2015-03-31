# Django settings for kuvendi.kv. subdomain

COUNTRY_CODE = 'kv'
PARLIAMENT_CODE = 'kuvendi'
PARLIAMENT_NAME = 'Kuvendit të Kosovës'
LANGUAGE_CODE = 'sq'
GA_PROPERTY_ID = '25'

ELASTICSEARCH_ANALYZERS = {}
ELASTICSEARCH_TOKENIZERS = {}
ELASTICSEARCH_FILTERS = {}
ELASTICSEARCH_USE_ANALYZER = 'standard'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
