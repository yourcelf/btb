from django.conf.urls.defaults import *

post_id = "(?P<post_id>\d+)"
author_id = "(?P<author_id>\d+)"
slug = "(?P<slug>[^/]*)"
revision_id = "(?P<revision_id>\d+)"

urlpatterns = patterns('blogs.views',
    # Post lists
    url(r'^blogs/$', 'group_post_list', name='blogs.home'),
    url(r'^blogs/tag/(?P<tag>.+)/$', 'tagged_post_list', name='blogs.tagged_posts'),
    url(r'^blogs/{0}/{1}/?$'.format(author_id, slug), 'author_post_list', name='blogs.blog_show'),
    url(r'^blogs/feed/$', 'group_post_feed', name='blogs.all_posts_feed'),
    url(r'^blogs/{0}/{1}/feed/$'.format(author_id, slug), 'legacy_author_post_feed'),
    url(r'^blogs/feed/{0}/$'.format(author_id), 'author_post_feed', name='blogs.blog_feed'),
    url(r'^blogs/tag/(?P<tag>.+)/feed$', 'tagged_post_feed', name='blogs.tagged_posts_feed'),


    # Individual posts
    url(r"^posts/{0}/{1}/?$".format(post_id, slug), 'post_detail', name='blogs.post_show'),
    url(r"^posts/commentfeed/{0}$".format(post_id), 'post_comments_feed', name='blogs.post_comments_feed'),
    url(r"^posts/tag/{0}$".format(post_id), 'save_tags', name='blogs.tag_post'),
    url(r"^posts/taglist$", 'post_tag_list', name='blogs.post_tag_list'),

    # Post actions
    url(r"^posts/more_pages/{0}$".format(post_id), 'more_pages', name='blogs.more_pages'),
)
