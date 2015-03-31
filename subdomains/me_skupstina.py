# Django settings for skupstina.me. subdomain

COUNTRY_CODE = 'me'
PARLIAMENT_CODE = 'skupstina'
PARLIAMENT_NAME = 'Skupština Crne Gore'
LANGUAGE_CODE = 'sr_ME'
GA_PROPERTY_ID = '23'

# requires LemmaGen plugin for ElasticSearch
# https://github.com/vhyza/elasticsearch-analysis-lemmagen
ELASTICSEARCH_ANALYZERS = {
    'serbian_lemmagen': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['stopwords_sr', 'lemmagen_sr', 'lowercase', 'stopwords_sr', 'remove_duplicities'],
    },
}
ELASTICSEARCH_TOKENIZERS = {}
ELASTICSEARCH_FILTERS = {
    'stopwords_sr': {
        'type': 'stop',
        'stopwords_path': 'sr/sr.stop',
        'ignore_case': True
    },
    'lemmagen_sr': {
        'type': 'lemmagen',
        'lexicon': 'sr'
    },
    'remove_duplicities': {
        'type': 'unique',
        'only_on_same_position': True
    },
}
ELASTICSEARCH_USE_ANALYZER = 'serbian_lemmagen'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
