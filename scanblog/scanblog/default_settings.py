# -*- coding: utf-8 -*-
import os.path
from btb.log_filter import skip_unreadable_post
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TEST_RUNNER = 'btb.test_runner.BtbTestRunner'

#
# Locale
#
TIME_ZONE = 'US/Eastern'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True

#
# Filesystem
#

# Uploaded files.  

# We want .url for vanilla storage to point to a public MEDIA_URL, but the
# MEDIA_ROOT to by default be private.

# These refer to private media only.
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = '/private_media/'
UPLOAD_TO = "uploads"
FILE_UPLOAD_PERMISSIONS = 0664

# Serve PUBLIC_MEDIA_ROOT with webserver, at PUBLIC_MEDIA_URL.  Symlinks for
# anything public will be added to this directory, so it should be on the same
# filesystem as PRIVATE_MEDIA_ROOT.
PUBLIC_MEDIA_ROOT = os.path.join(MEDIA_ROOT, "public")
PUBLIC_MEDIA_URL = '/media/'

# Static files (js, css, etc).  Before deployment, these live in 'static' (or
# individual apps' static dirs).  When we deply to production, we use django's
# staticfiles to collect them into 'site_static'.
STATIC_ROOT = os.path.join(BASE_DIR, "site_static")
STATIC_URL = '/static/'

#ADMIN_MEDIA_PREFIX = '/static/admin/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
COMPRESS_PRECOMPILERS = (
    ('text/javascript', 'cat'), # this shouldn't be necessary, but is
    ('text/css', 'cat'), # this shouldn't be necessary, but is
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/x-sass', 'sass --compass -I "%s"' % (os.path.join(BASE_DIR, "static", "css"))),
)

#
# Other stuff
#

# Make this unique, and don't share it with anybody.  Override it in
# settings.py.
SECRET_KEY = 'W^X~>p2j+u9XmNfNyt<9;ffaIVo{2vsfI-?_o8z893V8t$<[7\\'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'pagination.middleware.PaginationMiddleware',
)

ROOT_URLCONF = 'scanblog.urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "templates"),
)
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",

    "btb.context_processors.site",
    "notification.context_processors.notification",
)

INSTALLED_APPS = (
    # btb includes
    'about',
    'accounts',
    'annotations',
    'blogs',
    'btb',
    'comments',
    'correspondence',
    'moderation',
    'profiles',
    'subscriptions',
    'scanning',
    'campaigns',

    # django internal apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party dependencies
    'registration',
    'djcelery',
    'django_bcrypt',
    'compressor',
    'sorl.thumbnail',
    'notification',
    'pagination',
    'urlcrypt',
    'south',
)

LOGGING = {
    "version": 1,
    "disable_existing_lggers": False,
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            'filters': ['require_debug_false'],
            "class": "django.utils.log.AdminEmailHandler",
            'filters': ['require_debug_false', 'skip_unreadable_posts'],
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'skip_unreadable_posts': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_unreadable_post,
        }
    }
}

AUTHENTICATION_BACKENDS = (
    'scanblog.accounts.backends.CaseInsensitiveAuthenticationBackend',
)

CONTACT_EMAIL = "contact@betweenthebars.org"
MAIL_DROP_ID = 1
LOGIN_URL = "/accounts/login"
#TODO: Go to something else after login.
LOGIN_REDIRECT_URL = "/people/show"
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = "[BetweenTheBars.org] "

REGISTRATION_OPEN = True
COMMENTS_OPEN = True
TRANSCRIPTION_OPEN = True

CACHE_MIDDLEWARE_SECONDS = 60 * 10

# django-registration
ACCOUNT_ACTIVATION_DAYS = 2

# Allows sending of very large files in low memory with apache; doesn't work
# with devserver.
X_SENDFILE_ENABLED = False

UPLOAD_LIMIT = 20971520 # 20MB
SCAN_PAGES_PER_PAGE = 6

# Celery async processing
import djcelery
djcelery.setup_loader()
BROKER_URL = "amqp://guest:guest@localhost:5672/"
CELERY_TRACK_STARTED = True
#CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERY_RESULT_BACKEND = 'amqp'

TEXT_IMAGE_FONT = "/usr/share/fonts/truetype/gentium/GenR102.ttf"

INTERNAL_IPS = ('127.0.0.1',)

# External Commands
NICE_CMD = "/usr/bin/nice"
PDFTK_CMD = "/usr/bin/pdftk"
PDFIMAGES_CMD = "/usr/bin/pdfimages"
PDFTOTEXT_CMD = "/usr/bin/pdftotext"
CONVERT_CMD = "/usr/bin/convert"


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
THUMBNAIL_CACHE = 'default'

AUTHENTICATION_BACKENDS = (
    'urlcrypt.auth_backends.UrlCryptBackend',
    'django.contrib.auth.backends.ModelBackend',
)

DISABLE_NOTIFICATIONS = False
DISABLE_ADMIN_NOTIFICATIONS = False
THUMBNAIL_BACKEND = "btb.utils.SameDirThumbnailBackend"
THUMBNAIL_PREFIX = "cache/"

MAX_READY_TO_PUBLISH_DAYS = 6
PUBLISHING_HOURS = (7, 23)
SELENIUM_FIREFOX_BIN = "/usr/bin/firefox"
