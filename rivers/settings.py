"""
Django settings for rivers project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
from django.conf import global_settings


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '!o+bjv@=p*9#3l*01d)z-nj3v-nfuu+d*d@ufgf9ulesk-!yem'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
# install django-bootstrap3
# install pandas-datareader
INSTALLED_APPS = (
    # pip install psycopg2
    # pip install django-bootstrap3
    'adminplus',  # pip install django-adminplus
    # 'django_admin_bootstrapped',  # pip install django-admin-bootstrapped
    # 'bootstrap3_datetime',  # pip install django-bootstrap3-datetimepicker
    'django_extensions',  # pip install django-extensions
    # pip install F:\python\pip\QuantLib_Python-1.6.1-cp27-none-win_amd64.whl
    # conda install -c https://conda.anaconda.org/anaconda pandas-datareader

    # 'bootstrap_admin',  # always before django.contrib.admin
    'flat',
    #'test_without_migrations',

    # 'django.contrib.admin',
    'django.contrib.admin.apps.SimpleAdminConfig',  # adminplus replace
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin.widgets',

    'base',
    'data',
    'statement',

    # research
    'research.algorithm',
    'research.strategy',

    # opinion
    'opinion',
    #'opinion.review',
    #'opinion.market',
    #'opinion.personal',
    #'opinion.plan',
    #'opinion.stock',
    #'opinion.technical',

    # subtool
    'subtool',

    # broker
    'broker.ib',
    'broker.tda',

    # portfolio
    'portfolio',

    # statement
)

# for django-admin-bootsrapped
DAB_FIELD_RENDERER = 'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'rivers.urls'

WSGI_APPLICATION = 'rivers.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'rivers',
        'USER': 'admin',
        'PASSWORD': 'qwer1234',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        # 'CONN_MAX_AGE': 60
    }
}
# DATABASE_ROUTERS = ['rivers.router.DataRouter']

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'

USE_I18N = True
USE_L10N = False
USE_TZ = True
DATE_FORMAT = 'Y-m-d'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)


# fixtures
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'fixtures')]

# cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'TIMEOUT': 3600
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s: "%(message)s"',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'nothing': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

# HDF5 Store
SERVER_DIR = 'S:/'
DB_DIR = 'T:/'
FILES_DIR = os.path.join(DB_DIR, 'files')
EARNING_DIR = os.path.join(FILES_DIR, 'fidelity', 'earning')
DIVIDEND_DIR = os.path.join(FILES_DIR, 'fidelity', 'dividend')
STATEMENT_DIR = os.path.join(FILES_DIR, 'statement')
THINKBACK_DIR = os.path.join(FILES_DIR, 'thinkback')
QUOTE_DIR = os.path.join(DB_DIR, 'quote')
RESEARCH_DIR = os.path.join(DB_DIR, 'research')
CLEAN_DIR = TEMP_DIR = os.path.join(DB_DIR, 'temp')
TREASURY_DIR = os.path.join(DB_DIR, 'treasury.h5')
SPY_DIR = os.path.join(QUOTE_DIR, 'spy.h5')

IB_STATEMENT_DIR = os.path.join(FILES_DIR, 'statement', 'ib')
TDA_STATEMENT_DIR = os.path.join(FILES_DIR, 'statement', 'tda')

CSV_DIR = os.path.join(DB_DIR, 'csv')

# for test only
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'default.db')

    }
    DATABASES['quote'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'quote.db')
    }

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        # 'DEBUG': True,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request'
            ]
        },
    },
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(DB_DIR, 'media')

# testing
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
if TESTING:
    # print('=========================')
    # print('In TEST Mode - Disable Migrations')
    # print('=========================')


    class DisableMigrations(object):
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return "notmigrations"


    MIGRATION_MODULES = DisableMigrations()