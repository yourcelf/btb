from django.conf.urls.defaults import *

post_id = "(?P<post_id>\d+)"
author_id = "(?P<author_id>\d+)"
slug = "(?P<slug>[-a-z0-9]*)"
revision_id = "(?P<revision_id>\d+)"

urlpatterns = patterns('blogs.views',
    # Post lists
    url(r'^blogs/$', 'all_posts_list', name='blogs.home'),
    url(r'^blogs/tag/(?P<tag>.+)/$', 'tagged_post_list', name='blogs.tagged_posts'),
    url(r'^blogs/{0}/{1}/?$'.format(author_id, slug), 'author_post_list', name='blogs.blog_show'),

    url(r'^blogs/feed/$', 'all_posts_feed', name='blogs.all_posts_feed'),
    url(r'^blogs/feed/{0}/$'.format(author_id), 'author_post_feed', name='blogs.blog_feed'),
    url(r'^blogs/feed/comments/$', 'all_comments_feed', name='blogs.all_comments_feed'),
    url(r'^blogs/feed/{0}/$'.format(slug), 'org_post_feed', name='blogs.org_feed'),
    url(r'^blogs/feed/{0}/unfiltered$'.format(slug), 'org_post_feed', 
        kwargs={'filtered': False},
        name='blogs.org_feed_unfiltered'),
    url(r'^blogs/tag/(?P<tag>.+)/feed$', 'tagged_post_feed', name='blogs.tagged_posts_feed'),

    # Org has to come after feed, so that it doesn't consume 'feed' and 'tag' as slugs.
    url(r'^blogs/{0}/$'.format(slug), 'org_post_list', name='blogs.org_post_list'),

    url(r'^blogs/{0}/{1}/feed/$'.format(author_id, slug), 'legacy_author_post_feed'),

    # Individual posts
    url(r"^posts/{0}/{1}/?$".format(post_id, slug), 'post_detail', name='blogs.post_show'),
    url(r"^posts/commentfeed/{0}$".format(post_id), 'post_comments_feed', name='blogs.post_comments_feed'),
    url(r"^posts/tag/{0}$".format(post_id), 'save_tags', name='blogs.tag_post'),
    url(r"^posts/taglist$", 'post_tag_list', name='blogs.post_tag_list'),

    # Post actions
    url(r"^posts/more_pages/{0}$".format(post_id), 'more_pages', name='blogs.more_pages'),
    url(r"^posts/pagepicker/$", 'page_picker', name='blogs.page_picker'),

    # Editing posts from the web
    url(r'^posts/manage$', 'manage_posts', name='blogs.manage_posts'),
    url(r'^posts/edit/{0}?$'.format(post_id), 'edit_post', name='blogs.edit_post'),
    url(r'^posts/delete/{0}?$'.format(post_id), 'delete_post', name='blogs.delete_post'),
)
