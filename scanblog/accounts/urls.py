from django.conf.urls.defaults import *
from django.views.generic.base import TemplateView

from accounts.views import OptionalEmailRegistrationView

urlpatterns = patterns('accounts.views',
        url(r'^login/$', 'login', name='auth_login'),
        url(r'^logout/$', 'logout', name='auth_logout'),
        url(r'^password/change/(?P<user_id>\d+)/$', 'change_password', name='mod_change_password'),
        url(r'^check_username_availability$', 'check_username_availability', name='accounts.check_username_availability'),

        url(r'^welcome/$', 'welcome', name='accounts-post-registration'),
        url(r'^register/$', OptionalEmailRegistrationView.as_view(), name='registration_register'),
        url(r'^register/closed/$',
            TemplateView.as_view(template_name='registration/registration_closed.html'),
            name='registration_disallowed'),
        (r'', include('registration.auth_urls')),
)
