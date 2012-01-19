from django.conf.urls.defaults import *

from profiles.views import UsersJSON, OrganizationsJSON
from btb.views import sopastrike

user_id = "(?P<user_id>\d+)"
org_slug = "(?P<org_slug>[-a-z]+)"

urlpatterns = patterns('profiles.views',
    url(r'^users.json(/(?P<obj_id>\d+))?$', UsersJSON.as_view()),
    url(r'^organizations.json$', OrganizationsJSON.as_view()),
    url(r'^$', 'list_profiles', name='profiles.profile_list'),
    url(r'^groups$', 'list_orgs', name='profiles.org_list'),
    url(r'^groups/{0}$'.format(org_slug), 'org_detail', 
        name='profiles.org_detail'),
    url(r'^show$', 'show_own_profile', name='profiles.own_profile_show'),
    url(r'^edit$', 'edit_own_profile', name='profiles.own_profile_edit'),
    url(r'^edit/{0}$'.format(user_id), 'edit_profile', name='profiles.profile_edit'),
    url(r'^show/{0}$'.format(user_id), 'show_profile', name='profiles.profile_show'),
    url(r'^delete/{0}$'.format(user_id), 'delete', name='profiles.delete'),
    url(r'^remove_scan/{0}$'.format(user_id), 'remove_scan', name='profiles.remove_scan'),
)
