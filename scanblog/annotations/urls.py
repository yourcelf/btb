from django.conf.urls.defaults import *

from annotations.views import Notes, ReplyCodes

note_id = "(?P<note_id>\d+)"

urlpatterns = patterns('correspondence.views',
    url(r'^notes.json(/{0})?$'.format(note_id), Notes.as_view()),
    url(r'^reply_codes.json', ReplyCodes.as_view()),
)
