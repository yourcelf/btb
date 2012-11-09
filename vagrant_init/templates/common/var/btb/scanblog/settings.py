from default_settings import *

DEBUG = TEMPLATE_DEBUG = True
COMPRESS_ENABLED = not DEBUG
# Workaround for asset bug:
# https://github.com/jezdez/django_compressor/issues/226
#if not COMPRESS_ENABLED:
#    COMPRESS_ENABLED = True
#    COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter']
#    COMPRESS_JS_FILTERS = []

BCRYPT_ENABLED = False #Too slow for dev
THUMBNAIL_DEBUG = DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
DISABLE_NOTIFICATIONS = False
DISABLE_ADMIN_NOTIFICATIONS = False
ROOT_URLCONF = "urls"

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'W^X~>p2j+u9XmNfNyt<9;ffaIVo{2vsfI-?_o8z893V8t$<[7\\'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(SETTINGS_ROOT, 'deploy', 'dev.db'),  # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# http://antispam.typepad.com/info/get-api-key.html
TYPEPAD_ANTISPAM_API_KEY = "your typepad key"

ADMINS = (
    ("You", "you@example.com"),
)
MANAGERS = ADMINS

SERVER_EMAIL = "you@example.com"
DEFAULT_FROM_EMAIL = SERVER_EMAIL

# http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=Gentium_download
# Be sure to change this to the exact location
TEXT_IMAGE_FONT = "/usr/share/fonts/truetype/gentium/GenR102.ttf"

# You'll want to change these as needed...
NICE_CMD = "/usr/bin/nice"
PDFTK_CMD = '/usr/bin/pdftk'
WKHTMLTOPDF_CMD = os.path.join(SETTINGS_ROOT, 'bin', 'wkhtmltopdf')
RUBBER_PIPE_CMD = '/usr/bin/rubber-pipe'
PDFINFO_CMD = '/usr/bin/pdfinfo'
CONVERT_CMD = '/usr/bin/convert'

# Whether or not to allow new user sign ups
# REGISTRATION_OPEN = True
# Whether or not to allow new comments
# COMMENTS_OPEN = True
# Whether or not to allow transcriptions
# TRANSCRIPTION_OPEN = True

if DEBUG:
    pass
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)
    DEBUG_TOOLBAR_CONFIG = {
            'INTERCEPT_REDIRECTS': False,
    }
    DEBUG_TOOLBAR_PANELS = (
            'debug_toolbar.panels.version.VersionDebugPanel',
            'debug_toolbar.panels.timer.TimerDebugPanel',
            'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
            'debug_toolbar.panels.headers.HeaderDebugPanel',
            'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
            'debug_toolbar.panels.sql.SQLDebugPanel',
            'debug_toolbar.panels.template.TemplateDebugPanel',
            'debug_toolbar.panels.signals.SignalDebugPanel',
            'debug_toolbar.panels.logger.LoggingPanel',
            'debug_toolbar.panels.cache.CacheDebugPanel',
    )


# Whether or not to allow new user sign ups
REGISTRATION_OPEN = True
# Whether or not to allow new comments
COMMENTS_OPEN = True
# Whether or not to allow transcriptions
TRANSCRIPTION_OPEN = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'log_file':{
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(SETTINGS_ROOT, 'deploy', 'django.log'),
            'maxBytes': '16777216', # 16megabytes
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'log_file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
