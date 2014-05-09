import datetime

from django.db import models
from django.db.models import Q

class SiteBannerManager(models.Manager):
    def current(self):
        now = datetime.datetime.now()
        return self.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now),
                start_date__lte=now,
        ).order_by('-start_date')

class SiteBanner(models.Model):
    html = models.TextField(verbose_name='HTML')
    start_date = models.DateTimeField(default=datetime.datetime.now)
    end_date = models.DateTimeField(blank=True, null=True)

    objects = SiteBannerManager()

    def is_current(self):
        return self.start_date < datetime.datetime.now() and (
               (self.end_date is None) or
               self.end_date < datetime.datetime.now()
        )

    def __unicode__(self):
        return self.html[0:20]

    class Meta:
        ordering = ['-start_date']
