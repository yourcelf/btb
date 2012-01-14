from django.conf.urls.defaults import *

comment_id = "(?P<comment_id>\d+)"

urlpatterns = patterns('comments.views',
    url('comment/{0}/edit$'.format(comment_id), 'edit_comment', 
        name='comments.edit_comment'),
    url('comment/{0}/delete$'.format(comment_id), 'delete_comment', 
        name='comments.delete_comment'),
    url('comment/{0}/flag$'.format(comment_id), 'flag_comment', 
        name='comments.flag_comment'),
)
