import datetime

from django.db import models
from django.core.urlresolvers import reverse

from btb.utils import OrgQuerySet, OrgManager

class CampaignManager(OrgManager):
    def current(self):
        return self.all().current()

    def finished(self):
        return self.all().finished()

class Campaign(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    body = models.TextField()
    organizations = models.ManyToManyField('profiles.Organization',
            help_text="Which organizations are allowed to mark posts"
                      " as being part of this campaign?")
    reply_code = models.OneToOneField('annotations.ReplyCode')
    public = models.BooleanField()

    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(blank=True)
    ended = models.DateTimeField(null=True, blank=True)

    objects = CampaignManager()

    class QuerySet(OrgQuerySet):
        orgs = ["organizations" ]

        def current(self):
            return self.filter(ended__isnull=True)
        def finished(self):
            return self.filter(ended__isnull=False)

    class Meta:
        ordering = ['-created']

    def to_dict(self):
        return {
            u"id": self.pk,
            u"title": self.title,
            u"slug": self.slug,
            u"body": self.body,
            u"organizations": [o.light_dict() for o in self.organizations.all()],
            u"reply_code": unicode(self.reply_code.code),
            u"public": self.public,
            u"created": self.created,
            u"ended": self.ended,
        }

    def get_absolute_url(self):
        return reverse("blogs.show_campaign", args=[self.slug])

    def end(self):
        self.ended = datetime.datetime.now()

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        super(Campaign, self).save(*args, **kwargs)

    def responses(self):
        return self.reply_code.document_replies.all()

    def num_responses(self):
        return self.responses.count()

    def __unicode__(self):
        return self.slug
