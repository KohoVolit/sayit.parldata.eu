# Django settings for skupstina.rs. subdomain

COUNTRY_CODE = 'rs'
PARLIAMENT_CODE = 'skupstina'
PARLIAMENT_NAME = 'Народна скупштина Републике Србије'
LANGUAGE_CODE = 'sr'
GA_PROPERTY_ID = '22'

# requires ICU Analysis and LemmaGen plugins for ElasticSearch
# https://github.com/elastic/elasticsearch-analysis-icu
# https://github.com/vhyza/elasticsearch-analysis-lemmagen
ELASTICSEARCH_ANALYZERS = {
    'serbian_lemmagen': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['cyrillic-latin', 'stopwords_sr', 'lemmagen_sr', 'lowercase', 'stopwords_sr', 'remove_duplicities'],
    },
}
ELASTICSEARCH_TOKENIZERS = {}
ELASTICSEARCH_FILTERS = {
    'cyrillic-latin': {
        'type': 'icu_transform',
        'id': 'Cyrillic-Latin'
    },
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
