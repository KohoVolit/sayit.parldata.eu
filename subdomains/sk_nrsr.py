# Django settings for nrsr.sk. subdomain

COUNTRY_CODE = 'sk'
PARLIAMENT_CODE = 'nrsr'
PARLIAMENT_NAME = 'Národná rada Slovenskej republiky'
LANGUAGE_CODE = 'sk'
GA_PROPERTY_ID = '19'

ELASTICSEARCH_ANALYZERS = {
    'slovak_hunspell': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['stopwords_SK', 'sk_SK', 'lowercase', 'stopwords_SK', 'remove_duplicities'],
    },
}
ELASTICSEARCH_TOKENIZERS = {
}
ELASTICSEARCH_FILTERS = {
    'stopwords_SK': {
        'type': 'stop',
        'stopwords_path': 'hunspell/sk_SK/sk_SK.stop',
        'ignore_case': True
    },
    'sk_SK': {
        'type': 'hunspell',
        'locale': 'sk_SK',
        'dedup': True,
        'recursion_level': 0
    },
    'remove_duplicities': {
        'type': 'unique',
        'only_on_same_position': True
    },
}
ELASTICSEARCH_USE_ANALYZER = 'slovak_hunspell'


# load project settings while respecting the above
import os
project_settings = os.path.join(
    os.path.dirname(__file__), '..', 'sayit_parldata_eu', 'settings.py')
exec(open(project_settings).read())
