import json
import datetime
from collections import defaultdict

from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.sites.models import Site
from django.db.models import Count
from django.db import transaction

from btb.utils import JSONView, can_edit_user, can_edit_profile, \
        permission_required_or_deny, args_method_decorator
from profiles.models import Profile, Organization, Affiliation
from profiles.forms import get_profile_form, UserFormNoEmail, ProfileUploadForm
from scanning.models import Scan, Document, TranscriptionRevision
from scanning.tasks import process_scan_to_profile, move_scan_file
from annotations.models import Note
from comments.models import Comment, Favorite

class Not200Exception(Exception):
    pass

def list_profiles(request):
    return render(request, "profiles/profiles_list.html", {
        'authors': Profile.objects.bloggers_with_published_content()
    })

def list_orgs(request, org_slug):
    if org_slug is None:
        org = {
            'name': Site.objects.get_current().name,
            'slug': '',
        }
        profiles = sorted(
             # NB: Exclude doesn't get the right result here; but the
             # unexpected could happen if someone is in multiple groups, one or
             # more of which is public.
             (list(Profile.objects.bloggers_with_posts().filter(
                    user__organization__public=False)) +
              list(Profile.objects.bloggers_with_just_profiles().filter(
                    user__organization__public=False))
             ),
             key=lambda p: p.display_name
        )
    elif org_slug == "join":
        org = {
            'name': 'Join',
            'slug': org_slug,
        }
        profiles = []
    else:
        org = get_object_or_404(Organization, slug=org_slug, public=True)
        profiles = sorted(
                (list(
                    Profile.objects.bloggers_with_posts().filter(
                        user__organization=org
                    )
                 ) + list(
                    Profile.objects.bloggers_with_just_profiles().filter(
                        user__organization=org
                    )
                 )
                ), key=lambda p: p.display_name)
    return render(request, "profiles/groups_list.html", {
        'orgs': list(Organization.objects.public()),
        'chosen_org': org,
        'profiles': profiles,
    })


@login_required
def delete(request, user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        raise Http404

    if request.user.id != user_id and not (
            request.user.has_perm("auth.delete_user") and \
            can_edit_user(request.user, user_id)):
        raise PermissionDenied


    to_delete = User.objects.get(id=user_id)

    if request.method != 'POST':
        return render(request, "profiles/confirm_delete_self.html")
    # POST
    delete_comments = request.POST.get('delete_comments', False)
    if delete_comments:
        from comments.models import Comment, Favorite
        Comment.objects.filter(user=request.user).delete()
        Favorite.objects.filter(user=request.user).delete()

    u = to_delete
    u.username = "withdrawn-%i" % u.pk
    u.is_active = False
    u.is_staff = False
    u.is_superuser = False
    u.first_name = ""
    u.last_name = ""
    u.password = ""
    u.groups.clear()
    u.save()

    p = u.profile
    p.display_name = "(withdrawn)"
    p.blog_name = ""
    p.mailing_address = ""
    p.special_mail_handling = ""
    p.show_adult_content = False
    p.save()
    for scan in Scan.objects.filter(author=u):
        scan.full_delete()

    deleter = "self" if request.user == u else request.user.username
    Note.objects.create(
        text="User account deleted by %s." % deleter,
        user=p.user,
        resolved=datetime.datetime.now(),
        creator=request.user,
        important=True,
    )

    if request.user == u:
        logout(request)

    messages.add_message(request, messages.INFO, "User account successfully deleted.")
    return redirect("home")

@login_required
def show_own_profile(request):
    return redirect('profiles.profile_show', request.user.id)

def show_profile(request, user_id):
    try:
        profile = Profile.objects.enrolled().filter(pk=user_id)[0]
    except IndexError:
        try:
            profile = Profile.objects.active_and_inactive_commenters().filter(
                    pk=user_id
            )[0]
        except IndexError:
            raise Http404
    can_edit = can_edit_profile(request.user, profile.pk)
    try:
        document = Document.objects.filter(
                author=profile.user, type="profile", 
                status="published").order_by('-modified')[0]
    except IndexError:
        document = None
    try:
        org = profile.user.organization_set.get()
    except Organization.DoesNotExist:
        org = None
    return render(request, "profiles/profile_detail.html", {
            'document': document,
            'favorites': profile.user.favorite_set.select_related(
                'document', 'comment'),
            'transcription_revisions': profile.user.transcriptionrevision_set.select_related(
                'transcription', 'transcription__document').all(),
            'comments': profile.user.comment_set.public().select_related(
                'document', 'document__author', 'document__author__profile'),
            'profile': profile,
            'org': org,
            'can_edit': can_edit,
        })

@login_required
def edit_own_profile(request):
    return redirect("profiles.profile_edit", request.user.id)

@login_required
def remove_scan(request, user_id):
    if not can_edit_profile(request.user, user_id):
        raise PermissionDenied
   
    profile = Profile.objects.get(pk=user_id)
    docs = profile.user.documents_authored.filter(type="profile").order_by("-modified")

    if request.method == 'POST':
        for doc in docs:
            doc.scan.full_delete()
        messages.success(request, "Scan removed.")
        return redirect("profiles.profile_edit", profile.pk)

    return render(request, "profiles/confirm_delete_scan.html", {
        'profile': profile,
    })

@login_required
def edit_profile(request, user_id=None):
    edit_profile = can_edit_profile(request.user, user_id)
    edit_user = can_edit_user(request.user, user_id)
    if not edit_profile and not edit_user:
        raise PermissionDenied

    user = get_object_or_404(User, pk=user_id)
    try:
        document = Document.objects.filter(type="profile", status="published",
                                           author=user).order_by('-modified')[0]
    except IndexError:
        document = None

    # XXX Could probably simplify the permissions backflips by assuming that an
    # editor using this interface either has permissions to edit both
    # profile/user, or neither.
    
    user_form = None
    profile_form = None
    scan_upload_form = None
    ProfileForm = get_profile_form(request.user)
    if request.method == 'POST':
        if edit_profile:
            profile_form = ProfileForm(request.POST, instance=user.profile)
            scan_upload_form = ProfileUploadForm(request.POST, request.FILES)
        if edit_user:
            user_form = UserFormNoEmail(request.POST, instance=user)

        if (not profile_form or profile_form.is_valid()) and \
                (not user_form or user_form.is_valid()) and \
                (not scan_upload_form or scan_upload_form.is_valid()):

            if profile_form:
                profile_form.save()
            if user_form:
                user_form.save()
            if scan_upload_form and 'file' in request.FILES:
                pdf = move_scan_file(uploaded_file=request.FILES['file'])
                scan = Scan.objects.create(
                    uploader=user, 
                    author=user,
                    pdf=pdf
                )
                task_id = process_scan_to_profile.delay(
                    scan.pk, 
                    reverse('profiles.profile_show', args=[user_id]),
                )
                return redirect('moderation.wait_for_processing', task_id=task_id)
            messages.success(request, _("Changes saved."))
            return redirect('profiles.profile_show', user_id)
    else:
        if edit_profile:
            profile_form = ProfileForm(instance=user.profile)
            scan_upload_form = ProfileUploadForm()
        if edit_user:
            user_form = UserFormNoEmail(instance=user)

    return render(request, "profiles/profile_edit.html", {
            'document': document,
            'profile_form': profile_form,
            'user_form': user_form,
            'scan_upload_form': scan_upload_form,
            'profile': user.profile,
            'can_edit_profile': edit_profile,
            'can_edit_user': edit_user,
        })

#
# User JSON CRUD for backbone.
#
class UsersJSON(JSONView):
    @permission_required_or_deny("auth.change_user")
    def get(self, request, obj_id=None):
        tf = lambda key: request.GET.get(key) in ("true", "1")

        if tf('in_org'):
            profiles = Profile.objects.org_filter(request.user).select_related('user')
        else:
            profiles = Profile.objects.select_related('user')
        
        obj_id = obj_id or request.GET.get("id", None)
        if obj_id:
            return self.paginated_response(request, profiles.filter(pk=obj_id))

        if 'sort' in request.GET:
            sorting = request.GET.get('sort').split(",")
        else:
            sorting = ('-user__is_active', 'display_name')
        if 'q' in request.GET:
            val = request.GET.get('q')
            for word in val.split():
                if word.startswith('-'):
                    word = word[1:]
                    profiles = profiles.exclude(
                                display_name__icontains=word
                            ).exclude(
                                user__username__icontains=word
                            ).exclude(
                                mailing_address__icontains=word
                            )
                    try:
                        pk = int(word)
                        profiles = profiles.exclude(pk__exact=pk)
                    except ValueError:
                        pass
                else:
                    filt = profiles.filter(display_name__icontains=word) | \
                           profiles.filter(user__username__icontains=word) | \
                           profiles.filter(mailing_address__icontains=word)
                    try:
                        pk = int(word)
                        profiles = filt | profiles.filter(pk__exact=pk)
                    except ValueError:
                        profiles = filt
        if request.GET.get("is_active", "null") != "null":
            profiles = profiles.filter(user__is_active=tf('is_active'))
        if request.GET.get("blogger", "null") != "null":
            profiles = profiles.filter(blogger=tf('blogger'))
        if request.GET.get("managed", "null") != "null":
            profiles = profiles.filter(managed=tf('managed'))
        if request.GET.get("lost_contact", "null") != "null":
            profiles = profiles.filter(lost_contact=tf("lost_contact"))
        if request.GET.get("consent_form_received", "null") != "null":
            profiles = profiles.filter(consent_form_received=tf('consent_form_received'))
        if request.GET.get("in_org", "null") != "null" and tf("in_org"):
            profiles = profiles.org_filter(request.user)

        profiles = profiles.annotate(Count('user__scans_authored', distinct=True),)
        profiles = profiles.order_by(*sorting)
        return self.paginated_response(request, profiles)

    @permission_required_or_deny("auth.add_user")
    def post(self, request, obj_id=None):
        missing = set()
        params = json.loads(request.body)
        for key in ("display_name", "mailing_address", "blogger", "managed", 
                    "email", "blog_name", "org_id"):
            if not key in params:
                missing.add(key)
        if missing:
            return HttpResponseBadRequest("Missing required params: {0}".format(", ".join(missing)))

        try:
            org = Organization.objects.org_filter(request.user, pk=params['org_id']).get()
        except Organization.DoesNotExist:
            raise PermissionDenied

        user = User()
        user.username = request.POST.get(
            "username", 
            slugify(params["display_name"])
        )[:30]

        # Ensure a unique username
        base = user.username
        i = 0
        while User.objects.filter(username=user.username).exists():
            suffix = str(i)
            user.username = base[0:min(30 - len(suffix), len(base))] + suffix
            i += 1
        user.save()

        p = user.profile
        p.display_name = params["display_name"]
        p.mailing_address = params["mailing_address"]
        p.blog_name = params["blog_name"]
        p.blogger = params["blogger"]
        p.managed = params["managed"]
        p.lost_contact = params.get("lost_contact", False)
        p.save()

        org.members.add(user)

        return self.json_response(user.profile.to_dict())

    @permission_required_or_deny("auth.change_user")
    def put(self, request, obj_id):
        params = json.loads(request.body)
        user = Profile.objects.org_filter(request.user).get(pk=params['id']).user
        dirty = False
        for param in ('is_active', 'username', 'email'):
            if param in params:
                if params[param] != getattr(user, param):
                    dirty = True
                    setattr(user, param, params[param])

        for param in ('display_name', 'mailing_address', 
                'special_mail_handling', 'consent_form_received', 
                'blogger', 'managed', 'lost_contact', 'blog_name'):
            if param in params:
                if params[param] != getattr(user.profile, param):
                    dirty = True
                    setattr(user.profile, param, params[param])
        if dirty:
            user.save()
            user.profile.save()
        return self.json_response(user.profile.to_dict())

    @permission_required_or_deny("auth.delete_user")
    def delete(self, request, obj_id):
        pass

class OrganizationsJSON(JSONView):
    @permission_required_or_deny("profiles.change_organization")
    def get(self, request):
        orgs = Organization.objects.org_filter(request.user)
        if "id" in request.GET:
            return self.get_by_id(request, orgs)
        return self.paginated_response(request, orgs, dict_method='light_dict')

    @permission_required_or_deny("profiles.add_organization")
    def post(self, request):
        return self.update_attrs(request, Organization(), json.loads(request.body))

    @permission_required_or_deny("profiles.change_organization")
    def put(self, request):
        dest_attrs = json.loads(request.body)
        try:
            org = Organization.objects.org_filter(request.user).get(
                    pk=dest_attrs.get('id'))
        except Organization.DoesNotExist:
            raise Http404
        return self.update_attrs(request, org, dest_attrs)

    @permission_required_or_deny("profiles.delete_organization")
    def delete(self, request):
        attrs = json.loads(request.body)
        if attrs['id'] == 1:
            return HttpResponseBadRequest(json.dumps({
                "error": "Can't delete default organization."
            }))
        if not 'destination_organization' in attrs:
            return HttpResponseBadRequest(json.dumps({
                "error": "Missing parameters: destination_organization"
            }))
        try:
            org = Organization.objects.org_filter(request.user).get(
                    pk=attrs['id'])
            dest_org = Organization.objects.org_filter(request.user).get(
                    pk=attrs['destination_organization'])
        except Organization.DoesNotExist:
            raise Http404
        for member in org.members.all():
            member.organization_set.clear()
            dest_org.members.add(member)
        org.delete()
        return self.json_response(dest_org.to_dict())

    def update_attrs(self, request, org, dest_attrs):
        try:
            with transaction.atomic():
                res = self._update_attrs(request, org, dest_attrs)
                if res.status_code != 200:
                    raise Not200Exception()
        except Not200Exception:
            pass
        return res

    def _update_attrs(self, request, org, dest_attrs):
        required = set(["name", "slug", "members", "moderators"])
        missing = sorted(list(required - set(dest_attrs.keys())))
        if missing:
            return HttpResponseBadRequest(json.dumps({
                "error": "Missing attrs: {0}".format(", ".join(missing))
            }))

        for key in ["about", "footer", "personal_contact", "public",
                    "name", "mailing_address"]:
            setattr(org, key, dest_attrs.get(key, ''))
        if org.slug != dest_attrs['slug']:
            taken = True
            try:
                Organization.objects.get(slug=dest_attrs['slug'])
            except Organization.DoesNotExist:
                taken = False
            if taken:
                return HttpResponseBadRequest(json.dumps({
                    "error": "Slug not unique."
                }))
            else:
                org.slug = dest_attrs['slug']
        if dest_attrs.get('outgoing_mail_handled_by'):
            if org.outgoing_mail_handled_by_id != dest_attrs['outgoing_mail_handled_by']['id']:
                try:
                    mail_org = Organization.objects.org_filter(request.user).get(
                            pk=dest_attrs['outgoing_mail_handled_by']['id']
                    )
                except Organization.DoesNotExist:
                    raise PermissionDenied
                org.outgoing_mail_handled_by = mail_org
        else:
            org.outgoing_mail_handled_by = None
        # We'll want to roll this back if there are errors below.
        org.save()

        # Update members
        extra, missing = self._update_related_set(org,
                "members",
                "organization_set",
                dest_attrs,
                Profile.objects.org_filter(request.user).filter(managed=True),
                clobber=True)
        if extra:
            # We make heavy reliance on commit_on_success and the wrapper which
            # rolls back 400's to ensure we don't leave users without an
            # Organization.
            try:
                replacement = Organization.objects.org_filter(request.user).get(
                        pk=dest_attrs.get('replacement_org'))
            except Organization.DoesNotExist:
                return HttpResponseBadRequest(json.dumps({
                    "error": "Must specify replacement org if removing users"
                }))
            replacement.members.add(*[User.objects.get(pk=pk) for pk in extra])

        # Update moderators
        extra, missing = self._update_related_set(org,
                "moderators",
                "organizations_moderated",
                dest_attrs,
                Profile.objects.commenters())
        if org.moderators.count() == 0:
            return HttpResponseBadRequest(json.dumps({
                "error": "At least one moderator required."
            }))
        # Update membership in the "moderators" group.
        moderator_group = Group.objects.get(name='moderators')
        for pk in extra:
            orgs = Organization.objects.filter(moderators__pk=pk).count()
            if orgs == 0:
                User.objects.get(pk=pk).groups.remove(moderator_group)
        for pk in missing:
            User.objects.get(pk=pk).groups.add(moderator_group)
        return self.json_response(org.to_dict())

    def _update_related_set(self, org, org_key, user_key, dest_attrs, qs, clobber=False):
        """
        org: the organization
        key: the related manager's name.
        dest_attrs: the desired new attributes for the org as a dict, with the
            org manager as a key.
        qs: the queryset from which to find related objects to add.
        """
        current_pks = set(getattr(org, org_key).values_list('id', flat=True))
        desired_pks = set([m['id'] for m in dest_attrs[org_key]])
        extra = current_pks - desired_pks
        missing = desired_pks - current_pks
        for pk in extra:
            try:
                profile = qs.get(pk=pk)
            except ObjectDoesNotExist:
                raise PermissionDenied
            getattr(profile.user, user_key).remove(org)
        for pk in missing:
            try:
                profile = qs.get(pk=pk)
            except ObjectDoesNotExist:
                raise PermissionDenied
            if clobber:
                getattr(profile.user, user_key).clear()
            getattr(profile.user, user_key).add(org)
        return extra, missing


class AffiliationsJSON(JSONView):
    @permission_required_or_deny("profiles.change_affiliation")
    def get(self, request):
        affiliations = Affiliation.objects.org_filter(request.user)
        if "id" in request.GET:
            return self.get_by_id(request, affiliations)
        if "slug" in request.GET:
            affiliations = affiliations.filter(slug__iexact=request.GET.get("slug"))
        return self.paginated_response(request, affiliations)

    @permission_required_or_deny("profiles.change_affiliation")
    def put(self, request):
        attrs = json.loads(request.body)
        try:
            aff = Affiliation.objects.org_filter(request.user).get(pk=attrs['id'])
        except Affiliation.DoesNotExist:
            raise Http404
        return self.update_attrs(request, aff, attrs)

    @permission_required_or_deny("profiles.add_affiliation")
    def post(self, request):
        attrs = json.loads(request.body)
        aff = Affiliation()
        return self.update_attrs(request, aff, attrs)

    @permission_required_or_deny("profiles.delete_affiliation")
    def delete(self, request):
        attrs = json.loads(request.body)
        try:
            aff = Affiliation.objects.org_filter(request.user).get(pk=attrs.get('id'))
        except Affiliation.DoesNotExist:
            raise Http404
        aff.delete()
        return self.json_response({"status": "success"})

    def update_attrs(self, request, aff, attrs):
        try:
            with transaction.atomic():
                res = self._update_attrs(request, aff, attrs)
                if res.status_code != 200:
                    raise Not200Exception()
        except Not200Exception:
            pass
        return res

    def error(self, msg):
        return HttpResponseBadRequest(json.dumps({"error": msg}))

    def _update_attrs(self, request, aff, attrs):
        missing = []
        for key in ['title', 'slug', 'list_body', 'detail_body',
                    'public', 'order', 'organizations']:
            if key not in attrs:
                missing.append(key)
        if missing:
            return self.error("Missing parameters: {0}".format(", ".join(missing)))

        for key in ['title', 'list_body', 'detail_body', 'public', 'order']:
            setattr(aff, key, attrs[key])
        if Affiliation.objects.filter(slug=attrs['slug']).exclude(pk=aff.pk).exists():
            return self.error("Slug not unique.")
        aff.slug = attrs['slug']
        orgs = []
        for org_dict in attrs['organizations']:
            try:
                org = Organization.objects.org_filter(request.user).get(pk=org_dict.get('id'))
            except Organization.DoesNotExist:
                return self.error(
                    "Organization {0} not found or not allowed.".format(org_dict.get('id'))
                )
            orgs.append(org)
        if not orgs:
            return self.error("No organization specified.")
        aff.save()
        aff.organizations = orgs
        return self.json_response(aff.to_dict())

class CommenterStatsJSON(JSONView):
    @permission_required_or_deny("auth.change_user")
    def get(self, request):
        try:
            profile = Profile.objects.commenters().select_related('user').get(
                    user_id=request.GET.get('user_id'))
        except Profile.DoesNotExist:
            raise Http404

        comments = list(profile.user.comment_set.values_list(
            'created', 'document__author__pk', 'document__author__profile__display_name'
        ))
        txs = list(profile.user.transcriptionrevision_set.values_list(
            'modified',
            'transcription__document__author__pk',
            'transcription__document__author__profile__display_name',
        ))
        favorites = list(profile.user.favorite_set.values_list(
            'created',
            'document__author__pk',
            'document__author__profile__display_name',
            'comment__document__author__pk',
            'comment__document__author__profile__display_name',
        ))

        percentages = {
            'comments': len(comments) * 100. / (Comment.objects.public().count() or 1),
            'favorites': len(favorites) * 100. / (Favorite.objects.count() or 1),
            'transcriptions': len(txs) * 100. / (TranscriptionRevision.objects.count() or 1),
        }
        users = {}
        relationships = defaultdict(lambda: {
            "comments": 0, "transcriptions": 0, "favorites": 0, "total": 0
        })
        for created, author_pk, author_name in comments:
            relationships[author_pk]['comments'] += 1
            relationships[author_pk]['total'] += 1
            users[author_pk] = author_name
        for modified, author_pk, author_name in txs:
            relationships[author_pk]['transcriptions'] += 1
            relationships[author_pk]['total'] += 1
            users[author_pk] = author_name
        for created, author_pk_1, author_name_1, author_pk_2, author_name_2 in favorites:
            author_pk = author_pk_1 or author_pk_2
            author_name = author_name_1 or author_name_2
            relationships[author_pk]['favorites'] += 1
            relationships[author_pk]['total'] += 1
            users[author_pk] = author_name

        return self.json_response({
            "joined": profile.user.date_joined.isoformat(),
            "can_tag": profile.user.has_perm("scanning.tag_post"),
            "last_login": profile.user.last_login.isoformat(),
            "activity": {
                'comments': [c[0] for c in comments],
                'favorites': [f[0] for f in favorites],
                'transcriptions': [t[0] for t in txs],
            },
            "percentages": percentages,
            "relationships": sorted(relationships.items(), key=lambda d: d[1]['total'], reverse=True),
            "users": users,
        })

    @permission_required_or_deny("auth.change_user")
    def post(self, request):
        attrs = json.loads(request.body)
        try:
            profile = Profile.objects.commenters().select_related('user').get(user_id=attrs['user_id'])
        except (KeyError, Profile.DoesNotExist):
            raise Http404
        if attrs.get('can_tag', None) is not None:
            perm = Permission.objects.get_by_natural_key("tag_post", "scanning",  "document")
            if attrs['can_tag'] in ('true', '1', 1):
                profile.user.user_permissions.add(perm)
            else:
                profile.user.user_permissions.remove(perm)
            return self.json_response({"status": "ok"})
        return HttpResponseBadRequest("No recognized attributes")
