import json
import datetime

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Count

from btb.utils import args_method_decorator, JSONView, can_edit_user, can_edit_profile
from profiles.models import Profile, Organization
from profiles.forms import get_profile_form, UserFormNoEmail, ProfileUploadForm
from scanning.models import Scan, Document
from scanning.tasks import process_scan_to_profile, move_scan_file
from annotations.models import Note

INDEPENDENT_ORG = {
    'name': 'Independent',
    'slug': 'independent',
}

def list_profiles(request):
    return render(request, "profiles/profiles_list.html", {
        'authors': Profile.objects.bloggers_with_published_content()
    })

def list_orgs(request):
    return render(request, "profiles/groups_list.html", {
        'orgs': list(Organization.objects.public()) + [INDEPENDENT_ORG]
    })

def org_detail(request, org_slug):
    if org_slug == "independent":
        org = INDEPENDENT_ORG
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
    return render(request, "profiles/group_detail.html", {
        'orgs': list(Organization.objects.public()) + [INDEPENDENT_ORG],
        'chosen_org': org,
        'profiles': profiles,
    })

@login_required
def delete(request, user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        raise Http404

    #FIXME: org permission here
    if request.user.id != user_id and not request.user.has_perm("auth.delete_user"):
        raise PermissionDenied


    to_delete = User.objects.get(id=user_id)

    if request.method != 'POST':
        return render(request, "profiles/confirm_delete_self.html")
    # POST
    delete_comments = request.POST.get('delete_comments', False)
    if delete_comments:
        from comments.models import Comment
        Comment.objects.filter(user=request.user).delete()

    u = to_delete
    u.username = "withdrawn-%i" % u.pk
    u.is_active = False
    u.is_staff = False
    u.is_superuser = False
    u.first_name = ""
    u.last_name = ""
    u.email_address = ""
    u.password = ""
    u.groups = []
    u.save()

    p = u.profile
    p.display_name = "(withdrawn)"
    p.blog_name = ""
    p.mailing_address = ""
    p.special_mail_handling = ""
    p.story = ""
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
            profile = Profile.objects.commenters().filter(pk=user_id)[0]
        except IndexError:
            raise Http404
    can_edit = can_edit_profile(request.user, profile.pk)
    try:
        document = Document.objects.filter(
                author=profile.user, type="profile", 
                status="published").order_by('-modified')[0]
    except IndexError:
        document = None
    return render(request, "profiles/profile_detail.html", {
            'document': document,
            'profile': profile,
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
    #FIXME: org permission here
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
    @args_method_decorator(permission_required, "auth.change_user")
    def get(self, request, obj_id=None):
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
                                user__mailing_address__icontains=word
                            ).exclude(
                                pk__exact=word
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
        tf = lambda key: request.GET.get(key) == "true"
        if request.GET.get("is_active", "null") != "null":
            profiles = profiles.filter(user__is_active=tf('is_active'))
        if request.GET.get("in_prison", "null") != "null":
            profiles = profiles.filter(in_prison=tf('in_prison'))
        if request.GET.get("consent_form_received", "null") != "null":
            profiles = profiles.filter(consent_form_received=tf('consent_form_received'))
        if request.GET.get("in_org", "null") != "null":
            profiles = profiles.org_filter(request.user)

        profiles = profiles.annotate(Count('user__scans_authored', distinct=True),)
        profiles = profiles.order_by(*sorting)
        return self.paginated_response(request, profiles)

    @args_method_decorator(permission_required, "auth.add_user")
    def post(self, request, obj_id=None):
        missing = set()
        params = json.loads(request.raw_post_data)
        for key in ("display_name", "mailing_address", "in_prison", "email", "blog_name", "org_id"):
            if not key in params:
                missing.add(key)
        if missing:
            return HttpResponseBadRequest("Missing required params: {0}".format(", ".join(missing)))

        try:
            org = request.user.organizations_moderated.get(pk=params['org_id'])
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
        p.in_prison = params["in_prison"]
        p.save()

        org.members.add(user)

        return self.json_response(user.profile.to_dict())

    @args_method_decorator(permission_required, "auth.change_user")
    def put(self, request, obj_id):
        params = json.loads(request.raw_post_data)
        user = User.objects.select_related('profile').get(pk=params['id'])
        dirty = False
        for param in ('is_active', 'username', 'email'):
            if param in params:
                if params[param] != getattr(user, param):
                    dirty = True
                    setattr(user, param, params[param])

        for param in ('display_name', 'mailing_address', 
                'special_mail_handling', 'consent_form_received', 'in_prison',
                'blog_name'):
            if param in params:
                if params[param] != getattr(user.profile, param):
                    dirty = True
                    setattr(user.profile, param, params[param])
        if dirty:
            user.save()
            user.profile.save()
        return self.json_response(user.profile.to_dict())

    @args_method_decorator(permission_required, "auth.delete_user")
    def delete(self, request, obj_id):
        pass

class OrganizationsJSON(JSONView):

    @args_method_decorator(permission_required, "auth.change_user")
    def get(self, request):
        orgs = Organization.objects.org_filter(request.user)
        return self.json_response({
            'results': [o.to_dict() for o in orgs]
        })
