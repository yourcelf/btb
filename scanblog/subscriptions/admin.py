from django.contrib import admin

from subscriptions.models import *

for model in (NotificationBlacklist, Subscription, DocumentNotificationLog):
    admin.site.register(model)

