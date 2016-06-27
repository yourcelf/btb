from default_settings import *
from btb.log_filter import skip_unreadable_post


DEBUG = TEMPLATE_DEBUG = True
THUMBNAIL_DEBUG = DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DISABLE_NOTIFICATIONS = False
DISABLE_ADMIN_NOTIFICATIONS = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'W^X~>p2j+u9XmNfNyt<9;ffaIVo{2vsfI-?_o8z893V8t$<[7\\'

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#        'NAME': os.path.join(BASE_DIR, 'deploy', 'dev.db'),  # Or path to database file if using sqlite3.
#        'USER': '',                      # Not used with sqlite3.
#        'PASSWORD': '',                  # Not used with sqlite3.
#        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
#    }
#}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'btb',  # Or path to database file if using sqlite3.
        'USER': 'btb',                      # Not used with sqlite3.
        'PASSWORD': 'btb',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

ADMINS = (
    ("You", "you@example.com"),
)
MANAGERS = ADMINS

# Email for messages sent from the server, sent to admin/managers.
SERVER_EMAIL = "you@example.com"
# From email for notifications and user-facing stuff.
DEFAULT_FROM_EMAIL = SERVER_EMAIL

# http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=Gentium_download
# Be sure to change this to the exact location
TEXT_IMAGE_FONT = "/usr/share/fonts/truetype/gentium/GenR102.ttf"

# You'll want to change these as needed...
NICE_CMD = "/usr/bin/nice"
PDFTK_CMD = '/usr/bin/pdftk'
RUBBER_PIPE_CMD = '/usr/bin/rubber-pipe'
PDFINFO_CMD = '/usr/bin/pdfinfo'
CONVERT_CMD = '/usr/bin/convert'
#WKHTMLTOPDF_CMD = os.path.join(BASE_DIR, 'bin', 'wkhtmltopdf-i386')
# Selenium for running tests. Depending on the current state of firefox
# binaries/selenium libraries, it may be necessary to pin to older versions
# that work properly together.
# An oldy-but-goody is Firefox 10.0 with Selenium 2.20.0.
#SELENIUM_FIREFOX_BIN = os.path.join(BASE_DIR, "bin", "firefox", "firefox")

# Whether or not to allow new user sign ups
REGISTRATION_OPEN = True
# Whether or not to allow new comments
COMMENTS_OPEN = True
# Whether or not to allow transcriptions
TRANSCRIPTION_OPEN = True

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
            'filename': os.path.join(BASE_DIR, 'deploy', 'django.log'),
            'maxBytes': '16777216', # 16megabytes
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'filters': ['require_debug_false', 'skip_unreadable_posts'],
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'log_file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'skip_unreadable_posts': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_unreadable_post
        }
    }
}
SOUTH_TESTS_MIGRATE = False
MAILBOX_FORWARDING = {
    "username": "<your username>",
    "password": "<your password>",
}

# Uncomment the following to enable django debug toolbar. You'll need to
# install it first with e.g. `pip install django-debug-toolbar`
#if DEBUG:
#   MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#   INSTALLED_APPS += ('debug_toolbar',)
