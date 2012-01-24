from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.contrib.contenttypes import generic

from scanning.models import Document
from comments.models import Comment
from btb.utils import OrgManager, OrgQuerySet, EmptyOrgQuerySet

class ProfileManager(OrgManager):
    """
    For statuses based on letters (e.g. invited, waitlisted, etc.), any letter,
    whether sent or not, considers the status fulfilled.  That is, one is
    "invited" if an Letter(type='invited') has been created for the person,
    whether or not it was sent.  Creating a Letter is a contract to send it.

    This differs from the v1 implementation.
    """
    def active(self):
        """ Everyone that hasn't been removed. """
        return self.filter(user__is_active=True)

    def inactive(self):
        """ They have been removed for whatever reason. """
        return self.filter(user__is_active=False)

    def inactive_commenters(self):
        return self.filter(user__is_active=False, in_prison=False)

    def inactive_bloggers(self):
        return self.filter(user__is_active=False, in_prison=True)

    def commenters(self):
        """ They are not in prison. """
        return self.active().filter(in_prison=False)

    def bloggers(self): 
        """ They are in prison. """
        return self.active().filter(in_prison=True)

    def bloggers_with_posts(self):
        return self.bloggers().select_related('user').filter(
                user__documents_authored__status="published",
                user__documents_authored__type="post",
            ).annotate(
                authored_posts_count=models.Count('user__documents_authored'),
                latest_post=models.Max(
                    'user__documents_authored__date_written'
                ),
            ).order_by('display_name')

    def bloggers_with_profiles(self):
        return self.bloggers().select_related('user').filter(
                user__documents_authored__status="published",
                user__documents_authored__type="profile",
            ).annotate(
                authored_posts_count=models.Count('user__documents_authored'),
                latest_post=models.Max(
                    'user__documents_authored__date_written'
                ),
            ).order_by('display_name')

    def bloggers_with_just_profiles(self):
        return self.bloggers().select_related('user').filter(
                user__documents_authored__status="published",
                user__documents_authored__type="profile",
            ).exclude(
                user__documents_authored__type="post",
                user__documents_authored__status="published",
            ).order_by('display_name')

    def bloggers_with_published_content(self):
        return sorted(list(self.bloggers_with_posts()) +
                      list(self.bloggers_with_just_profiles()), 
                key=lambda p: p.display_name)


    def enrolled(self):
        """ They have returned a consent form. """
        return self.bloggers().filter(consent_form_received=True)

    #
    # Letter-based statuses
    #

    def invitable(self):
        """
        No invitation letter has been created for them.
        """
        return self.bloggers().filter(
                    consent_form_received=False
                ).exclude(
                    user__received_letters__type="consent_form"
                )

    def invited(self):
        """ 
        An invitation letter has been created, but not returned.
        """
        return self.bloggers().filter(
                    consent_form_received=False
                ).filter(
                    user__received_letters__type="consent_form"
                )

    def waitlistable(self):
        """
        They have not been sent a consent form or waitlist postcard, and we
        haven't received a consent form.
        """
        return self.bloggers().filter(
                    consent_form_received=False,
                ).exclude(
                    user__received_letters__type="waitlist",
                ).exclude(
                    user__received_letters__type="consent_form",
                )

    def waitlisted(self):
        """ 
        No invitation letter has been created, and a waitlist postcard has been
        created.
        """
        return self.bloggers().filter(
                    consent_form_received=False
                ).filter(
                    user__received_letters__type="waitlist"
                ).exclude(
                    user__received_letters__type="consent_form"
                )

    def needs_signup_complete_letter(self):
        return self.enrolled().exclude(user__received_letters__type="signup_complete")

    def needs_first_post_letter(self):
        return (
                self.enrolled().filter(user__documents_authored__status="published")
        ).exclude(user__received_letters__type="first_post")

    def needs_comments_letter(self):
        # Couldn't figure out how to make this a flat ORM query.  Using two
        # queries and custom SQL instead.
        pks = Comment.objects.unmailed().values_list('document__author__pk', flat=True)
        if pks:
            where = '"{0}"."{1}" in ({2})'.format(
                    Profile._meta.db_table,
                    Profile.user.field.get_attname_column()[0],
                    ",".join("%s" for i in pks),
            )
            return self.enrolled().extra(
                where=[where],
                params=pks
            )
        return EmptyOrgQuerySet(self.model)

class Profile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    display_name = models.CharField(max_length=50)
    show_adult_content = models.BooleanField(
        help_text=_('Show posts and comments that have been marked as adult?')
    )

    in_prison = models.BooleanField()
    blog_name = models.CharField(blank=True, default="", max_length=255)
    mailing_address = models.TextField(blank=True, default="")
    special_mail_handling = models.TextField(blank=True, default="")

    consent_form_received = models.BooleanField()

    objects = ProfileManager()

    class QuerySet(OrgQuerySet):
        orgs = ["user__organization"]

    def to_dict(self):
        scans_authored = getattr(self, "user__scans_authored", None)
        return {
            'id': self.pk,
            'username': self.user.username,
            'email': self.user.email,
            'is_active': self.user.is_active,
            'date_joined': self.user.date_joined.isoformat(),
            'in_prison': self.in_prison,
            'blog_name': self.blog_name,
            'display_name': self.display_name,
            'mailing_address': self.mailing_address,
            'special_mail_handling': self.special_mail_handling,
            'consent_form_received': self.consent_form_received,
            'organizations': [o.to_dict() for o in self.user.organization_set.all()],
            'invited': Profile.objects.invited().filter(pk=self.pk).exists(),
            'waitlisted': Profile.objects.waitlisted().filter(pk=self.pk).exists(),
            'waitlistable': Profile.objects.waitlistable().filter(pk=self.pk).exists(),
            'blog_url': self.get_blog_url(),
            'profile_url': self.get_absolute_url(),
            'edit_url': self.get_edit_url(),
            'scans_authored': scans_authored,
            'has_public_profile': self.has_public_profile(),
            'is_public': self.is_public(),
        }
            
    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.username
        super(Profile, self).save(*args, **kwargs)
        # Since profile status (active/license) can impact publicness of
        # documents, we need to bump the documents if we save profiles.
        for doc in self.user.documents_authored.all():
           doc.set_publicness()

    def __unicode__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse('profiles.profile_show', args=[self.pk])

    def get_user_edit_url(self):
        return reverse('profiles.profile_edit', args=[self.pk])

    def get_edit_url(self):
        return "%s#/users/%s" % (reverse('moderation.home'), self.pk)

    def get_blog_url(self):
        return reverse('blogs.blog_show', args=[self.pk, self.get_blog_slug()])

    def get_blog_slug(self):
        return slugify(self.display_name)

    def full_address(self):
        return "\n".join((
            self.display_name,
            self.mailing_address
        ))

    def is_public(self):
        return self.user.is_active and ((not self.in_prison) or self.consent_form_received)

    def has_public_profile(self):
        return Document.objects.filter(author__pk=self.pk, type="profile",
                                       status="published").exists()

    def has_blog_posts(self):
        return Document.objects.filter(author__pk=self.pk, type="post",
                                       status="published").exists()

class OrganizationManager(OrgManager):
    def public(self):
        return self.filter(public=True)

class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    personal_contact = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    public = models.BooleanField(
        help_text="Check to make this organization appear in the 'Groups' tab"
    )

    mailing_address = models.TextField()
    outgoing_mail_handled_by = models.ForeignKey('self', blank=True, null=True)

    about = models.TextField(
        blank=True,
        help_text="Main text that will appear on the groups page.",
    )
    footer = models.TextField(
        blank=True,
        help_text="Additional text that will appear at the bottom of each post by a member of this organization.",
    )

    members = models.ManyToManyField(User, blank=True)
    moderators = models.ManyToManyField(User,
        related_name="organizations_moderated",
        blank=True
    )

    objects = OrganizationManager()

    class QuerySet(OrgQuerySet):
        orgs = [""]

    def to_dict(self):
        return {
            'id': self.pk,
            'name': self.name,
            'public': self.public,
            'mailing_address': self.mailing_address,
        }

    def members_count(self):
        return self.members.count()

    def moderators_list(self):
        return ", ".join(unicode(u.profile) for u in self.moderators.all())

    def get_absolute_url(self):
        return reverse("profiles.org_detail", kwargs={'org_slug': self.slug})

    def __unicode__(self):
        return self.name

@receiver(post_save, sender=User)
def create_profile(sender, instance=None, **kwargs):
    """
    Creates a profile on the User's save signal, so we know every user has one.
    Add the user to the "readers" group.
    """
    if instance is None:
        return
    profile, created = Profile.objects.get_or_create(user=instance)
    readers, created = Group.objects.get_or_create(name="readers")
    profile.user.groups.add(readers)
