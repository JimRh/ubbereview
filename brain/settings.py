import logging
import os
import sys

_DJANGO_SECRET_KEY = os.environ['APIDJANGOKEY']
DATA_KEY = os.environ['APIDATAKEY']
GOOGLE_API_KEY = os.environ['APIGOOGLEAPIKEY']
TWO_SHIP_API_KEY = os.environ['APITWOSHIPAPIKEY']
TAXJAR_API_KEY = os.environ["APITAXJARAPIKEY"]
OPEN_EXCHANGE_API_KEY = os.environ["APIOPENEXCHANGERATE"]

SKYLINE_BASE_URL = os.environ.get('APISKYLINEAPIURL', 'https://merged5t_training.skyres.ca:50443')
TWO_SHIP_BASE_URL = os.environ.get('API2SHIPAPIURL', 'https://api.2ship.com')
WESTJET_BASE_URL = os.environ.get('APIWESTJETAPIURL', 'http://test.westjetcargo.com/webapi/v1')
CANADA_POST_BASE_URL = os.environ.get('CANADAPOSTENDPOINTURL', 'https://ct.soa-gw.canadapost.ca/rs/soap')
CANADA_POST_PICKUP_BASE_URL = os.environ.get('APICANADAPOSTPICKUPENDPOINTURL', 'https://ct.soa-gw.canadapost.ca/ad/soap')
CANADA_POST_PICKUP_REQUEST_BASE_URL = os.environ.get('APICANADAPOSTPICKUPREQUESTENDPOINTURL', 'https://ct.soa-gw.canadapost.ca/enab/soap')
DAYROSS_BASE_URL = os.environ.get('APIDAYROSSAPIURL', 'https://staging.dayrossgroup.com/public')
MANITOULIN_URL = os.environ.get('APIMANITOULINURL', 'https://staging1.mtdirect.ca/')
FEDEX_BASE_URL = os.environ.get('APIFEDEXENDPOINTURL', 'https://wsbeta.fedex.com/web-services')
PURO_BASE_URL = os.environ.get('APIPUROENDPOINTURL', "https://devwebservices.purolator.com")
ACTION_EXPRESS_BASE_URL = os.environ.get('APIACTIONENDPOINTURL', "https://secure.ontime360.com/sites/Actiontransportationgroup1/api")
CARGOJET_BASE_URL = os.environ.get('APICARGOJETENDPOINTURL', "https://airways.cargojet.com/ords/mtce/booking")
YRC_REST_BASE_URL = os.environ.get('APIYRCRESTAPIURL', 'https://api.yrc.com')
YRC_SOAP_BASE_URL = os.environ.get('APIYRCSOAPAPIURL', 'https://api.yrc.com')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGODEBUG', 'true').lower() == 'true'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'api', 'fixtures', 'tests'),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = _DJANGO_SECRET_KEY

ALLOWED_HOSTS = [
    "172.105.5.81",
    "api.ubbe.com",
    "139.177.196.69",
    "betaapi.ubbe.com",
    "localhost",
    "127.0.0.1",
    # "172.105.28.215"
]

INTERNAL_IPS = [
    "127.0.0.1"
]

CORS_ORIGIN_ALLOW_ALL = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'oauth2_provider',
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    'api.apps.ApiConfig',
    'website.apps.WebsiteConfig',
    'apps.books.apps.BooksConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'brain.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },

    },
]

WSGI_APPLICATION = 'brain.wsgi.application'

if "test" in sys.argv:
    print("Running test configuration\n")
    PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
    logging.disable(logging.CRITICAL)

if DEBUG:
    print("Debugging mode: \033[1;32mACTIVE\033[0;0m")
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
else:
    print("Debugging mode: \033[1;31mINACTIVE\033[0;0m")

DEBUG_TOOLBAR_PANELS = [
    # 'ddt_request_history.panels.request_history.RequestHistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('APIDATABASE', 'Brain'),
        'USER': os.environ.get('APIUSER', 'root'),
        'PASSWORD': os.environ.get('APIPASSWORD', 'root'),
        'HOST': os.environ.get('APIHOST', 'localhost'),
        'PORT': os.environ.get('APIPORT', '3306')
    } if not DEBUG else {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3'
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
ADMINS = [
    ("Kenneth Carmichael", "kcarmichael@bbex.com"),
]

SERVER_EMAIL = "no-reply@ubbe.com"

DEFAULT_FROM_EMAIL = "no-reply@ubbe.com"

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-ca'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# LOGIN_REDIRECT_URL =
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'Login'

OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'super': 'Super Scope'},
    'REFRESH_TOKEN_EXPIRE_SECONDS': 31536000
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    "EXCEPTION_HANDLER": "apps.common.utilities.exceptions.ubbe_exception_handler"
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
    'SECURITY_DEFINITIONS': {
        'Oauth2': {
            'type': 'oauth2',
            'authorizationUrl': '/o/authorize',
            'tokenUrl': '/o/token/',
            'flow': 'passwordCredentials',
            'username': 'gobox',
            'password': 'InnerWorkings',
            'scopes': {
                'read write': 'read write',
            }
        }
    },
    'OAUTH2_REDIRECT_URL': 'http://127.0.0.1:8000/static/drf-yasg/swagger-ui-dist/oauth2-redirect.html',
    'OAUTH2_CONFIG': {
        'clientId': 'IqqgtbulOE1NbJAACY37A4orz1wIcSwfODnAzMBf',
        'clientSecret': 'EGR2k50qPWEO5ZHcOANwNxL1yNjKqubXEPLtMOS3MPKPFVY3IxrZjFBRdpjkx1g0TkddrVQKItokJxmQtIVXEysNJV2slrXx2rIkYS1pWw2xxhcvs24DoLAtdAuImytL',
        'appName': 'ubbe Api',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "KEY_PREFIX": "api"
    }
}

CACHE_TTL = 60 * 15
ONE_HOUR_CACHE_TTL = 60 * 60
FIVE_HOURS_CACHE_TTL = 5 * 60 * 60
TWENTY_FOUR_HOURS_CACHE_TTL = 24 * 60 * 60

# Celery application definition
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

EMAIL_HOST = os.environ.get('SMTPSERVER', 'localhost')
EMAIL_PORT = int(os.environ.get('SMTPPORT', '25'))
EMAIL_HOST_USER = os.environ.get('SMTPUSER', '')

if not EMAIL_HOST_USER:
    raise KeyError('SmtpUser could not be found in section \'Email\', does it exist?')
EMAIL_HOST_PASSWORD = os.environ.get('SMTPPASSWORD', '')

if not EMAIL_HOST_PASSWORD:
    raise KeyError('SmtpPassword could not be found in section \'Email\', does it exist?')
smtp_ssl = os.environ.get('SMTPSSL', '')
smtp_tls = os.environ.get('SMTPTLS', '')

if smtp_ssl and smtp_tls:
    raise KeyError('SmtpSSL and SmtpTLS cannot both be set in section\'Email\'')
elif smtp_ssl == '1':
    EMAIL_USE_SSL = True
elif smtp_tls == '1':
    EMAIL_USE_TLS = True
del smtp_ssl
del smtp_tls
LOGGER_TO_EMAIL = os.environ.get('LOGGERTOEMAIL', '')

if not LOGGER_TO_EMAIL:
    raise KeyError('SmtpUser could not be found in section \'Email\', does it exist?')
LOGGER_FROM_EMAIL = os.environ.get('LOGGERFROMEMAIL', '')

if not LOGGER_FROM_EMAIL:
    raise KeyError('SmtpUser could not be found in section \'Email\', does it exist?')
SHIPMENT_REQUEST_EMAIL = os.environ.get('APISHIPMENTREQUESTEMAIL', '')

if not SHIPMENT_REQUEST_EMAIL:
    raise KeyError('ShipmentRequestEmail could not be found in section \'Email\', does it exist?')
SKYLINE_PICKUP_REQUEST_EMAIL = os.environ.get('APISKYLINEPICKUPREQUESTEMAIL', '')

if not SKYLINE_PICKUP_REQUEST_EMAIL:
    raise KeyError('SkylinePickupRequestEmail could not be found in section \'Email\', does it exist?')
PICKUP_REQUEST_EMAIL = os.environ.get('APIPICKUPREEQUESTEMAIL', '')

if not SKYLINE_PICKUP_REQUEST_EMAIL:
    raise KeyError('PickupRequestEmail could not be found in section \'Email\', does it exist?')

B13A_FILING_EMAIL = os.environ.get('apiB13AFilingEmail', 'developer@bbex.com')

BC_URL = os.environ.get('APIBCJOBS', '')

BC_JOBS_URL = os.environ.get('APIBCJOBS', '')

if not BC_JOBS_URL:
    raise KeyError('BcURL could not be found in section \'BusinessCentral\', does it exist?')

BC_CUSTOMERS_URL = os.environ.get('APIBCCUSTOMERS', '')

if not BC_CUSTOMERS_URL:
    raise KeyError('BcURL could not be found in section \'BusinessCentral\', does it exist?')

BC_JOB_LIST_URL = os.environ.get('APIBCJOBLIST', '')

if not BC_JOB_LIST_URL:
    raise KeyError('apiBCJobList could not be found in section \'BusinessCentral\', does it exist?')

BC_ITEMS_URL = os.environ.get('APIBCITEMS', '')

if not BC_ITEMS_URL:
    raise KeyError('BcURL could not be found in section \'BusinessCentral\', does it exist?')

BC_VENDORS_URL = os.environ.get('APIBCVENDORS', '')

if not BC_VENDORS_URL:
    raise KeyError('BcURL could not be found in section \'BusinessCentral\', does it exist?')

BC_USER = os.environ.get('APIBCUSER', '')

if not BC_USER:
    raise KeyError('BcUSER could not be found in section \'BusinessCentral\', does it exist?')

BC_PASS = os.environ.get('APIBCPASS', '')

if not BC_PASS:
    raise KeyError('BcPASS could not be found in section \'BusinessCentral\', does it exist?')
