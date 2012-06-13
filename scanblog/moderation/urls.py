from django.conf.urls.defaults import *

task_id = '(?P<task_id>[\w\d\-\.]+)'

urlpatterns = patterns('moderation.views', 
    url(r'^$', 'home', name='moderation.home'),
    url(r'^tasks/$', 'manage_tasks', name='moderation.manage_tasks'),
    url(r'^wait/{0}/'.format(task_id), 'wait_for_processing', name='moderation.wait_for_processing'),
    url(r'^stats/$', 'stats', name='moderation.stats'),
    url(r'^pagepicker/$', 'page_picker', name='moderation.page_picker'),

    # Local hash urls here for DRY, but will never trigger.
    url(r'^#/process/scan/(?P<scan_id>\d+)', 'home', name='moderation.edit_scan'),
    url(r'^#/process/document/(?P<scan_id>\d+)', 'home', name='moderation.edit_doc'),
    url(r'^tagparty/next/$', 'tagparty_next', name='moderation.tagparty_next'),
    url(r'^tagparty/$', 'tagparty', name='moderation.tagparty'),
)

