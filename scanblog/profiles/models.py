import os
import datetime
import itertools
import string
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.conf import settings

from scanning.models import Document
from comments.models import Comment
from btb.utils import OrgManager, OrgQuerySet

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
        return self.filter(user__is_active=False, blogger=False)

    def inactive_bloggers(self):
        return self.filter(user__is_active=False, blogger=True)

    def active_and_inactive_commenters(self):
        return self.filter(blogger=False)

    def commenters(self):
        """ They are not in prison. """
        return self.active().filter(blogger=False)

    def bloggers(self): 
        """ They are in prison. """
        return self.active().filter(blogger=True)

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
        return self.bloggers().select_related('user').filter(
                Q(user__documents_authored__status="published", 
                  user__documents_authored__type="profile") |
                Q(user__documents_authored__status="published",
                  user__documents_authored__type="post")
              ).distinct().order_by('display_name')

    def enrolled(self):
        """ They have returned a consent form. """
        return self.bloggers().filter(consent_form_received=True)

    def enrolled_in_contact(self):
        """ They have returned a consent form, and we haven't lost contact. """
        return self.enrolled().filter(lost_contact=False)

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
        return self.none()

    def recently_active(self, days=2*365):
        """
        All bloggers with whom we haven't lost contact, are enrolled or have
        been invited, and have sent us something within the last N days.
        """
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        return self.bloggers().filter(
                lost_contact=False
            ).filter(
                Q(consent_form_received=True) |
                Q(user__received_letters__type="consent_form")
            ).filter(
                user__documents_authored__created__gte=cutoff
            ).distinct()

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True)
    display_name = models.CharField(max_length=50)
    show_adult_content = models.BooleanField(
        default=False,
        help_text=_('Show posts and comments that have been marked as adult?')
    )

    blogger = models.BooleanField(default=False)
    managed = models.BooleanField(default=False)
    lost_contact = models.BooleanField(default=False)

    blog_name = models.CharField(blank=True, default="", max_length=255)
    comments_disabled = models.BooleanField(default=False)
    mailing_address = models.TextField(blank=True, default="")
    special_mail_handling = models.TextField(blank=True, default="")

    consent_form_received = models.BooleanField(default=False)

    objects = ProfileManager()

    class QuerySet(OrgQuerySet):
        orgs = ["user__organization"]

    def light_dict(self):
        return {
            'id': self.pk,
            'username': self.user.username,
            'email': self.user.email,
            'is_active': self.user.is_active,
            'date_joined': self.user.date_joined.isoformat(),
            'blogger': self.blogger,
            'managed': self.managed,
            'lost_contact': self.lost_contact,
            'comments_disabled': self.comments_disabled,
            'blog_name': self.blog_name,
            'display_name': self.display_name,
            'mailing_address': self.mailing_address,
            'special_mail_handling': self.special_mail_handling,
            'consent_form_received': self.consent_form_received,
            'blog_url': self.get_blog_url(),
            'profile_url': self.get_absolute_url(),
            'edit_url': self.get_edit_url(),
            'is_public': self.is_public(),
        }

    def to_dict(self):
        scans_authored = getattr(self, "user__scans_authored", None)
        dct = self.light_dict()
        dct.update({
            u'organizations': [o.light_dict() for o in self.user.organization_set.all()],
            u'invited': Profile.objects.invited().filter(pk=self.pk).exists(),
            u'waitlisted': Profile.objects.waitlisted().filter(pk=self.pk).exists(),
            u'waitlistable': Profile.objects.waitlistable().filter(pk=self.pk).exists(),
            u'scans_authored': scans_authored,
            u'has_public_profile': self.has_public_profile(),
        })
        return dct
            
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

    def get_bare_blog_url(self):
        return reverse('blogs.blog_show', args=[self.pk, ""])

    def get_blog_slug(self):
        return slugify(self.display_name)

    def full_address(self):
        return "\n".join((
            self.display_name,
            self.mailing_address
        ))

    def is_public(self):
        return self.user.is_active and ((not self.blogger) or self.consent_form_received)

    def has_public_profile(self):
        return Document.objects.filter(author__pk=self.pk, type="profile",
                                       status="published").exists()

    def has_blog_posts(self):
        return Document.objects.filter(author__pk=self.pk, type="post",
                                       status="published").exists()

    def set_random_password(self):
        """
        Set a random password on our associated user object.  Does not save the user.
        """
        chars = set(string.ascii_uppercase + string.digits)
        char_gen = (c for c in itertools.imap(os.urandom, itertools.repeat(1)) if c in chars)
        self.user.set_password(''.join(itertools.islice(char_gen, None, 32)))

    def all_published_posts_as_latex_list(self):
        from correspondence.utils import tex_escape
        posts = self.user.documents_authored.public().order_by('date_written')
        parts = [ur'\begin{itemize}']
        for post in posts:
            if post.in_reply_to:
                try:
                    orig = posts.get(reply_code=post.in_reply_to)
                except Document.DoesNotExist:
                    title = post.get_title()
                else:
                    title = u'{} (in reply to {})'.format(
                        post.get_title(),
                        orig.get_title()
                    )
            else:
                title = post.get_title()

            parts.append(ur'  \item %s (\emph{%s})' % (
                tex_escape(title), 
                post.date_written.strftime('%Y-%m-%d')
            ))
        parts.append(ur'\end{itemize}')
        return u"\n".join(parts)


class OrganizationManager(OrgManager):
    def public(self):
        return self.filter(public=True)

class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    personal_contact = models.CharField(max_length=255, blank=True)
    public = models.BooleanField(
        default=False,
        help_text="Check to make this organization appear in the 'Groups' tab"
    )
    custom_intro_packet = models.FileField(upload_to=settings.UPLOAD_TO + "/org_intro_packets",
            help_text="Leave blank to use the default packet, formatted with your address.",
            blank=True, null=True)
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

    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    moderators = models.ManyToManyField(settings.AUTH_USER_MODEL,
        related_name="organizations_moderated",
        blank=True
    )

    objects = OrganizationManager()

    class QuerySet(OrgQuerySet):
        orgs = [""]

    def to_dict(self):
        dct = self.light_dict()
        dct['moderators'] = [u.profile.light_dict() for u in self.moderators.select_related('profile').all()]
        dct['members'] = [u.profile.light_dict() for u in self.members.select_related('profile').all()]
        dct['about'] = self.about
        dct['footer'] = self.footer
        dct['mailing_address'] = self.mailing_address
        dct['personal_contact'] = self.personal_contact
        if self.custom_intro_packet:
            dct['custom_intro_packet_url'] = self.custom_intro_packet.url
        else:
            dct['custom_intro_packet_url'] = None
        if self.outgoing_mail_handled_by:
            dct['outgoing_mail_handled_by'] = self.outgoing_mail_handled_by.light_dict()
        else:
            dct['outgoing_mail_handled_by'] = {}
        return dct

    def light_dict(self):
        return {
            u'id': self.pk,
            u'slug': self.slug,
            u'name': self.name,
            u'public': self.public,
            u'mailing_address': self.mailing_address,
        }

    def members_count(self):
        return self.members.count()

    def moderators_list(self):
        return ", ".join(unicode(u.profile) for u in self.moderators.all())

    def get_absolute_url(self):
        return reverse("profiles.profile_list", kwargs={'org_slug': self.slug})

    def __unicode__(self):
        return self.name

class AffiliationManager(OrgManager):
    def public(self): return self.all().public()
    def private(self): return self.all().private()

class Affiliation(models.Model):
    """
    Affiliations are like a "super tag" for posts, which:
     1. can append additional HTML to the top of list and detail views
     2. is limited to use by particular org's.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True,
            help_text="Use this to identify this affiliation when editing documents.")
    logo = models.ImageField(upload_to="public/uploads/affiliations/",
            blank=True, null=True)
    list_body = models.TextField(
            help_text="HTML for the top of the group page.")
    detail_body = models.TextField(
            help_text="HTML to append to individual posts for this group.")
    organizations = models.ManyToManyField(Organization,
            help_text="Which organizations are allowed to mark posts"
                      " as belonging to this affiliation?")
    public = models.BooleanField(
            default=False,
            help_text="If false, the affiliation won't be listed publicly.")

    order = models.IntegerField(
            default=0,
            help_text="Use to set the order for the list of affiliations on"
                      " the categories view. Lower numbers come first.")
    created = models.DateTimeField(default=datetime.datetime.now)
    modified = models.DateTimeField(blank=True)

    objects = AffiliationManager()

    class QuerySet(OrgQuerySet):
        orgs = ["organizations"]

        def public(self):
            return self.filter(public=True)
        def private(self):
            return self.filter(public=False)
    
    class Meta:
        ordering = ['order', '-created']

    def to_dict(self):
        return {
            u'id': self.pk,
            u'title': self.title,
            u'slug': self.slug,
            u'logo_url': self.logo.url if self.logo else None,
            u'list_body': self.list_body,
            u'detail_body': self.detail_body,
            u'organizations': [o.light_dict() for o in self.organizations.all()],
            u'public': self.public,
            u'order': self.order,
        }

    def total_num_responses(self):
        return self.document_set.count()

    def get_absolute_url(self):
        return reverse("blogs.show_affiliation", args=[self.slug])

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super(Affiliation, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.slug

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
