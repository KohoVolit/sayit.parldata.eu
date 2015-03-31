# Django settings for orszaggyules.hu. subdomain

COUNTRY_CODE = 'hu'
PARLIAMENT_CODE = 'orszaggyules'
PARLIAMENT_NAME = 'Országgyűlés'
LANGUAGE_CODE = 'hu_HU'
GA_PROPERTY_ID = '24'

ELASTICSEARCH_ANALYZERS = {
    'hungarian_lemmagen': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['stopwords_hu', 'lemmagen_hu', 'lowercase', 'stopwords_hu', 'remove_duplicities'],
    },
}
ELASTICSEARCH_TOKENIZERS = {}
ELASTICSEARCH_FILTERS = {
    'stopwords_hu': {
        'type': 'stop',
        'stopwords_path': 'hu_HU/hu_HU.stop',
        'ignore_case': True
    },
    'lemmagen_hu': {
        'type': 'lemmagen',
        'lexicon': 'hu'
    },
    'remove_duplicities': {
        'type': 'unique',
        'only_on_same_position': True
    },
}
ELASTICSEARCH_USE_ANALYZER = 'hungarian_lemmagen'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
