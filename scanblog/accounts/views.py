"""
This app is a simple extension of built in auth_views which overrides login and
logout to provide messages on successful login/out.
"""

from django.contrib.auth import views as auth_views
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required

from btb.utils import can_edit_user
from accounts.forms import OptionalEmailForm
from registration.backends.simple.views import RegistrationView

def login(request, *args, **kwargs):
    kwargs['extra_context'] = {
        'reg_form': OptionalEmailForm(auto_id="regid_%s")
    }
    response = auth_views.login(request, *args, **kwargs)
    return response

def logout(request, *args, **kwargs):
    messages.success(request, _("Successfully logged out."))
    response = auth_views.logout(request, *args, **kwargs)
    return response

def check_username_availability(request):
    username = request.GET.get('username', None)
    if not username:
        response = HttpResponse('{"result": null}')

    if User.objects.filter(username=username).exists():
        response = HttpResponse('{"result": "taken"}')
    else:
        response = HttpResponse('{"result": "available"}')
    response['Content-Type'] = "application/json"
    return response

def change_password(request, user_id):
    """
    Change the password of the user with the given user_id.  Checks for
    permission to change users.
    """
    if not can_edit_user(request.user, user_id):
        raise PermissionDenied

    if request.user.id == int(user_id):
        Form = PasswordChangeForm
    else:
        Form = SetPasswordForm

    user = User.objects.get(id=user_id)

    if request.POST:
        form = Form(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Password changed successfully."))
            return HttpResponseRedirect(reverse("profiles.profile_edit", args=[user_id]))
    else:
        form = Form(request.user)

    return render(request, "registration/password_change_form.html", {
        'form': form,
        'change_user': user,
    })

@login_required
def welcome(request):
    return render(request, 'registration/welcome.html')

class OptionalEmailRegistrationView(RegistrationView):
    form_class = OptionalEmailForm

    def get_success_url(self, user):
        if 'after_login' in self.request.session:
            return self.request.session.pop('after_login')
        return reverse("accounts-post-registration")
