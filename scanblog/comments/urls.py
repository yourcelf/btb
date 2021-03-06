from django.conf.urls import *

comment_id = "(?P<comment_id>\d+)"

urlpatterns = patterns('comments.views',
    url('^comment/{0}/edit$'.format(comment_id), 'edit_comment', 
        name='comments.edit_comment'),
    url('^comment/{0}/delete$'.format(comment_id), 'delete_comment', 
        name='comments.delete_comment'),
    url('^comment/{0}/flag$'.format(comment_id), 'flag_comment', 
        name='comments.flag_comment'),
    url('comment/{0}/spam$'.format(comment_id), 'spam_can_comment',
        name='comments.spam_can_comment'),
    url('comment/{0}/moderator_remove$'.format(comment_id), 'remove_comment',
        name='comments.moderator_remove'),
    url('comment/{0}/moderator_unremove$'.format(comment_id), 'unremove_comment',
        name='comments.moderator_unremove'),
    url('^mark_favorite.json$', 'mark_favorite',
        name='comments.mark_favorite'),
    url('^mark_favorite_after_login$', 'mark_favorite_after_login',
        name='comments.mark_favorite_after_login'),
    url('^unmark_favorite.json$', 'unmark_favorite',
        name='comments.unmark_favorite'),
    url('^list_favorites$', 'list_favorites',
        name='comments.list_favorites'),
)
