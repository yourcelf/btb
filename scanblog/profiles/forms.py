from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from profiles.models import Profile
from scanning.forms import ScanUploadForm

class UserForm(forms.ModelForm):
    email = forms.EmailField(label=_('* E-mail address'), required=True,
            help_text=_("Required. We never share or make e-mail addresses public."))
    class Meta:
        model = User
        exclude = ('username', 'password', 'is_staff', 'is_active',
                'is_superuser', 'last_login', 'date_joined', 'groups',
                'user_permissions', 'first_name', 'last_name')

class UserFormNoEmail(UserForm):
    email = forms.EmailField(label=_('E-mail address'), required=False)

def get_profile_form(editor):
    exclude_list = ['user']
    if not editor.has_perm('profiles.change_profile'):
        exclude_list += [
            'mailing_address', 
            'special_mail_handling',
            'blogger', 
            'managed', 
            'consent_form_received'
        ]
    if not editor.has_perm('blogs.change_own_post'):
        exclude_list.append('blog_name')

    class ProfileForm(forms.ModelForm):
        display_name = forms.CharField(label=_("* Display name"), help_text=_("Required."))
        class Meta:
            model = Profile
            exclude = exclude_list

    return ProfileForm

class ProfileUploadForm(ScanUploadForm):
    file = forms.FileField(label="Profile PDF", help_text="If you wish, you can upload a one page 8.5x11 PDF scan to display as your profile.", required=False)
