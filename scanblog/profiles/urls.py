from django.conf.urls import *

from profiles.views import UsersJSON, OrganizationsJSON, AffiliationsJSON, CommenterStatsJSON
from django.contrib.auth import views as auth_views

user_id = "(?P<user_id>\d+)"
org_slug = "(?P<org_slug>[-a-z]+)"

urlpatterns = patterns('profiles.views',
    url(r'^users.json(/(?P<obj_id>\d+))?$', UsersJSON.as_view()),
    url(r'^organizations.json$', OrganizationsJSON.as_view()),
    url(r'^affiliations.json$', AffiliationsJSON.as_view()),
    url(r'^commenter_stats.json$', CommenterStatsJSON.as_view()),

    url(r'^show$', 'show_own_profile', name='profiles.own_profile_show'),
    url(r'^edit$', 'edit_own_profile', name='profiles.own_profile_edit'),
    url(r'^edit/{0}$'.format(user_id), 'edit_profile', name='profiles.profile_edit'),
    url(r'^show/{0}$'.format(user_id), 'show_profile', name='profiles.profile_show'),
    url(r'^delete/{0}$'.format(user_id), 'delete', name='profiles.delete'),
    url(r'^remove_scan/{0}$'.format(user_id), 'remove_scan', name='profiles.remove_scan'),
    url(r'^{0}?$'.format(org_slug), 'list_orgs', name='profiles.profile_list'),
    #url(r'^$', 'list_profiles', name='profiles.profile_list'),


    # Handling auth_views directly here, because the reverse names for
    # registration.auth_urls have changed (the "auth_" prefix is gone)
    # in Django 1.6.
    url(r'^login/$', auth_views.login, {'template_name': 'registration/login.html'},
        name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'registration/logout.html'},
        name='logout'),
    url(r'^password/change/$', auth_views.password_change,
        name='password_change'),
    url(r'^password/change/done/$', auth_views.password_change_done,
        name='password_change_done'),
    url(r'^password/reset/$', auth_views.password_reset,
        name='password_reset'),

    # Support old style base36 password reset links; remove in Django 1.7
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm_uidb36),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        name='password_reset_confirm'),

    url(r'^password/reset/complete/$', auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'^password/reset/done/$', auth_views.password_reset_done,
        name='password_reset_done'),

)
