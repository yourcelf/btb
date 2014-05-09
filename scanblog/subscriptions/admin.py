from django.contrib import admin

from subscriptions.models import *

for model in (NotificationBlacklist, Subscription, MailingListInterest):
    admin.site.register(model)
