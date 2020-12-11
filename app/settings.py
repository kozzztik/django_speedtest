DELAY = 0
SYNC_RECEIVERS_COUNT = 100
ASYNC_RECEIVERS_COUNT = 0
DEBUG = False

INSTALLED_APPS = ('app.app.App',)
MIDDLEWARE = ()
ROOT_URLCONF = 'app.urls'
SECRET_KEY = 'nosecrets'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
    }
}
