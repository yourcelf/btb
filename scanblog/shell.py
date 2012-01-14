#
# Useful things to import when using manage.py shell
#
# Usage:
#
# % python manage.py shell
# >>> from shell import *
# >>> # Now you have all these useful things at your disposal.
#
from pprint import pprint

from django.core.cache import cache
from django.contrib.auth.models import *
from django.db.models import *

from annotations.models import *
from comments.models import *
from profiles.models import *
from blogs.models import *
from scanning.models import *
from correspondence.models import *
from moderation.models import *
from notification.models import *
from subscriptions.models import *
