# Django settings for sejm.pl. subdomain

COUNTRY_CODE = 'pl'
PARLIAMENT_CODE = 'sejm'
PARLIAMENT_NAME = 'Sejm Rzeczypospolitej Polskiej'
LANGUAGE_CODE = 'pl'
GA_PROPERTY_ID = '21'

ELASTICSEARCH_ANALYZERS = {
    'polish_morfologik': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['stopwords_PL', 'morfologik_stem', 'lowercase', 'stopwords_PL', 'remove_duplicities'],
    },
}
ELASTICSEARCH_TOKENIZERS = {}
ELASTICSEARCH_FILTERS = {
    'stopwords_PL': {
        'type': 'stop',
        'stopwords_path': 'pl_PL/pl_PL.stop',
        'ignore_case': True
    },
    'remove_duplicities': {
        'type': 'unique',
        'only_on_same_position': True
    },
}
ELASTICSEARCH_USE_ANALYZER = 'polish_morfologik'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
