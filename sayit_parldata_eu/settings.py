import os
import sys
import yaml
from django.conf import global_settings

# Path to here is something like
# /home/projects/sayit/sayit_parldata_eu/settings.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, 'sayit_parldata_eu'))
SUBDOMAINS_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, 'subdomains'))
VIRTUALENV_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '..', '.virtualenvs', 'sayit'))

# Load private settings not included in the public repository
config_file = os.path.join(PROJECT_ROOT, 'conf', 'private.yml')
with open(config_file) as f:
    config = yaml.load(f)

DEBUG = False
TEMPLATE_DEBUG = DEBUG
try:
    import debug_toolbar  # noqa
    DEBUG_TOOLBAR = True
except:
    DEBUG_TOOLBAR = False

ADMINS = (
    ('Jaro Semančík', 'jaroslav_semancik@yahoo.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': config.get('SAYIT_DB_USER'),
        'PASSWORD': config.get('SAYIT_DB_PASS'),
        'HOST': config.get('SAYIT_DB_HOST'),
        'PORT': config.get('SAYIT_DB_PORT'),
    }
}
if 'PARLIAMENT_CODE' in globals():
    DATABASES['default']['NAME'] = 'sayit_%s_%s' % (COUNTRY_CODE, PARLIAMENT_CODE)

ALLOWED_HOSTS = ['.sayit.parldata.eu']

SECRET_KEY = config.get('DJANGO_SECRET_KEY')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/var/www/sayit.parldata.eu/uploads'
if 'PARLIAMENT_CODE' in globals():
    MEDIA_ROOT += '/%s/%s' % (COUNTRY_CODE, PARLIAMENT_CODE)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# All uploaded files world-readable
FILE_UPLOAD_PERMISSIONS = 0o644

# List of callables that know how to import templates from various sources.
loaders = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)
if not DEBUG:
    loaders = (('django.template.loaders.cached.Loader', loaders),)

TEMPLATE_LOADERS = loaders

MIDDLEWARE_CLASSES = [
    'sayit_parldata_eu.middleware.PatchCacheHeadersMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
##    'django.contrib.sessions.middleware.SessionMiddleware',
    # Use only LANGUAGE_CODE setting instead of language negotiation
    # 'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
##    'django.contrib.auth.middleware.AuthenticationMiddleware',
##    'django.contrib.messages.middleware.MessageMiddleware',
    'speeches.middleware.InstanceMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = ('127.0.0.1',)

ROOT_URLCONF = 'sayit_parldata_eu.urls'

LOGIN_REDIRECT_URL = '/'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sayit_parldata_eu.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'templates'),
)
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    "django.core.context_processors.request",
    "sayit_parldata_eu.context_processors.exposed_settings",
)
SETTINGS_EXPOSED_TO_TEMPLATES = (
    'PARLIAMENT_NAME',
    'GOOGLE_ANALYTICS_ACCOUNT',
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
##    'django.contrib.sessions',
##    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
##    'django.contrib.admin',
##    'django.contrib.admindocs',
    'haystack',
    'elasticstack',
    'django_select2',
    'django_bleach',
    'easy_thumbnails',
    'popolo',
    'instances',
    'speeches',
    'sayit_parldata_eu',
]

try:
    import nose  # noqa
    INSTALLED_APPS.append('django_nose')
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    NOSE_PLUGINS = ['speeches.tests.nose_plugins.SkipMigrations']
except ImportError:
    # This is only present in 1.6+, but you shouldn't be running the tests
    # without installing the test requirements anyway
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'

if DEBUG_TOOLBAR:
    INSTALLED_APPS.append('debug_toolbar')

# Caching
if DEBUG:
    cache = {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
    CACHE_MIDDLEWARE_SECONDS = 0
else:
    cache = {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/www/sayit.parldata.eu/cache',
        'TIMEOUT': None,
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
        },
    }
if 'PARLIAMENT_CODE' in globals() and 'LOCATION' in cache:
    cache['LOCATION'] += '/%s/%s' % (COUNTRY_CODE, PARLIAMENT_CODE)
CACHES = {
    'default': cache
}

# Log WARN and above to stderr; ERROR and above by email when DEBUG is False.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'WARN',
            'propagate': True,
        },
        'speeches': {
            'handlers': ['mail_admins', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'pyelasticsearch': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': True,
        },
        'requests.packages.urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': True,
        },
    }
}

# Pagination related settings
PAGINATION_DEFAULT_WINDOW = 2

APPEND_SLASH = False

# Select2
AUTO_RENDER_SELECT2_STATICS = False

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/var/www/sayit.parldata.eu/collected_static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "static"),
)

if 'test' not in sys.argv:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Django-bleach configuration
BLEACH_ALLOWED_TAGS = [
    'a', 'abbr', 'b', 'i', 'u', 'span', 'sub', 'sup', 'br',
    'p',
    'ol', 'ul', 'li',
    'table', 'caption', 'tr', 'th', 'td',
]
BLEACH_ALLOWED_ATTRIBUTES = {
    '*': ['id', 'title'],  # class, style
    'a': ['href'],
    'li': ['value'],
}

# Easy-thumbnails configuration
# Class attribute so as not to activate and get caught in a circle
from easy_thumbnails.conf import Settings

_processors = []
for processor in Settings.THUMBNAIL_PROCESSORS:
    # Before the default scale_and_crop, insert our face_crop
    if processor == 'easy_thumbnails.processors.scale_and_crop':
        _processors.append('speeches.thumbnail_processors.face_crop')
    _processors.append(processor)

THUMBNAIL_PROCESSORS = tuple(_processors)

# Haystack search settings
SEARCH_INDEX_NAME = DATABASES['default']['NAME']
if 'test' in sys.argv:
    SEARCH_INDEX_NAME += '_test'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'elasticstack.backends.ConfigurableElasticSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': SEARCH_INDEX_NAME,
    },
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# ElasticSearch indexing settings
# Default ES settings
ELASTICSEARCH_INDEX_SETTINGS = {
    'settings': {
        "analysis": {
            "analyzer": {
                "ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "lowercase",
                    "filter": ["haystack_ngram"]
                },
                "edgengram_analyzer": {
                    "type": "custom",
                    "tokenizer": "lowercase",
                    "filter": ["haystack_edgengram"]
                }
            },
            "tokenizer": {
                "haystack_ngram_tokenizer": {
                    "type": "nGram",
                    "min_gram": 3,
                    "max_gram": 15,
                },
                "haystack_edgengram_tokenizer": {
                    "type": "edgeNGram",
                    "min_gram": 2,
                    "max_gram": 15,
                    "side": "front"
                }
            },
            "filter": {
                "haystack_ngram": {
                    "type": "nGram",
                    "min_gram": 3,
                    "max_gram": 15
                },
                "haystack_edgengram": {
                    "type": "edgeNGram",
                    "min_gram": 2,
                    "max_gram": 15
                }
            }
        }
    }
}
# Add language specific settings
if 'ELASTICSEARCH_ANALYZERS' in globals():
    ELASTICSEARCH_INDEX_SETTINGS['settings']['analysis']['analyzer'].update(ELASTICSEARCH_ANALYZERS)
if 'ELASTICSEARCH_TOKENIZERS' in globals():
    ELASTICSEARCH_INDEX_SETTINGS['settings']['analysis']['tokenizer'].update(ELASTICSEARCH_TOKENIZERS)
if 'ELASTICSEARCH_FILTERS' in globals():
    ELASTICSEARCH_INDEX_SETTINGS['settings']['analysis']['filter'].update(ELASTICSEARCH_FILTERS)
if 'ELASTICSEARCH_USE_ANALYZER' in globals():
    ELASTICSEARCH_DEFAULT_ANALYZER = ELASTICSEARCH_USE_ANALYZER

if 'GA_PROPERTY_ID' in globals():
    GOOGLE_ANALYTICS_ACCOUNT = '%s-%s' % (config.get('GOOGLE_ANALYTICS_ACCOUNT'), GA_PROPERTY_ID)
