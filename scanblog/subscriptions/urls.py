from django.conf.urls.defaults import *

user_id = "(?P<user_id>\d+)"

urlpatterns = patterns('subscriptions.views',
    url(r'^settings/?$', 'notice_settings',
        name='subscriptions.settings'),
    url(r'^unsubscribe$', 'unsubscribe_all_from_email',
        name='subscriptions.unsubscribe'),

    url(r'^subscribe/tag/(?P<tag_name>.*)$', 'subscribe_to_tag',
        name='subscriptions.tag'),
    url(r'^subscribe/author/(?P<author_id>\d+)$', 'subscribe_to_author',
        name='subscriptions.author'),
    url(r'^subscribe/org/(?P<org_id>\d+)$', 'subscribe_to_org',
        name='subscriptions.org'),
    url(r'^subscribe/document/(?P<document_id>\d+)$', 'subscribe_to_document',
        name='subscriptions.document'),

    # Notification addendum
    url(r'^toggle_notice/(?P<notice_id>\d+)$', 'ajax_set_notice_seen',
        name='notification_ajax_set_notice_seen'),
    url(r'^delete_notice/(?P<notice_id>\d+)$', 'ajax_delete_notice',
        name='notification_ajax_delete_notice'),
    url(r'^delete_all_notices$', 'ajax_delete_all_notices',
        name='notification_ajax_delete_all_notices'),

    # Defer to notifications if not found.
    url(r'', include('notification.urls')),
)
