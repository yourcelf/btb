import re

from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext as _

from scanning.templatetags.public_url import public_url, site_url
from scanning.models import Transcription

class Atom1FeedWithBase(Atom1Feed):
    """ 
    Atom1 feed that expresses the xml:base attribute allowing relative URIs 
    """
    def __init__(self, *args, **kwargs):
        self.site_base = kwargs['site_base']
        super(Atom1FeedWithBase, self).__init__(*args, **kwargs)

    def root_attributes(self):
        attr = super(Atom1FeedWithBase, self).root_attributes()
        attr['xml:base'] = self.site_base
        return attr

class Atom1FeedWithImages(Atom1FeedWithBase):
    def add_item_elements(self, handler, item):
        super(Atom1FeedWithImages, self).add_item_elements(handler, item)
        if item['images']:
            handler.addQuickElement(u"images", u"\n".join(item['images']))
        handler.addQuickElement(u"transcription",
                item.get('transcription', u''),
                {u'status': item.get('transcription_status', u'missing')})

def _feed(request, title, klass=Atom1FeedWithBase):
    site = Site.objects.get_current()
    feed_uri = request.build_absolute_uri()
    feed = klass(
            title=u"%s: %s" % (site.name, title),
            link=re.sub("\/feed$", '', feed_uri),
            description=title,
            feed_url=feed_uri,
            site_base="http://%s/" % request.get_host(),
    )
    return feed

def posts_feed(request, context):
    feed = _feed(request, title=context['title'])

    for post in context['posts'][:10]:
        descr = render_to_string("blogs/_post_feed.html", {
                'post': post,
            }, context_instance=RequestContext(request))

        try:
            author_name = force_unicode(post.author.profile)
            author_link = post.author.profile.get_absolute_url()
        except AttributeError:
            author_name = None
            author_link = None

        feed.add_item(
            title=post.title or "Untitled",
            #HACK -- making URLs absolute
            # make an absolute link to get a valid TAG URI fails if a port is
            # included with domain (see Django bug #8758).
            link=feed.site_base + post.get_absolute_url()[1:],
            description=descr,
            author_name=author_name,
            author_link=author_link,
            pubdate=post.date_written,
        )

    response = HttpResponse(mimetype=feed.mime_type)
    feed.write(response, 'utf-8')
    return response

def full_posts_feed(request, context):
    feed = _feed(request, title=context['title'], klass=Atom1FeedWithImages)
    for post in context['posts'][:10]:
        profile = post.author.profile
        descr = render_to_string("blogs/_full_post_feed.html", {
            "post": post,
            "profile": profile,
        }, context_instance=RequestContext(request))

        try:
            tx = post.transcription
            tx_current = tx.current()
        except (Transcription.DoesNotExist, AttributeError):
            tx = None
            tx_current = None
        if tx and tx_current:
            tx_body = tx_current.body
            tx_status = "complete" if tx.complete else "partial"
        else:
            tx_body = ""
            tx_status = "missing"

        feed.add_item(
            title=post.get_title(),
            #HACK -- making URLs absolute
            # make an absolute link to get a valid TAG URI fails if a port is
            # included with domain (see Django bug #8758).
            link=feed.site_base + post.get_absolute_url()[1:],
            description=descr,
            author_name=profile.display_name,
            author_link=profile.get_absolute_url(),
            pubdate=post.date_written,
            images=[site_url(public_url(p.image.url)) for p in post.documentpage_set.all()],
            transcription=tx_body,
            transcription_status=tx_status
        )

    response = HttpResponse(mimetype=feed.mime_type)
    feed.write(response, 'utf-8')
    return response

def all_comments_feed(request, comments):
    feed = _feed(request, title=_("All comments on %s" % Site.objects.get_current().name))
    for comment in comments:
        descr = render_to_string("comments/_comment.html", {
                'comment': comment,
            }, context_instance=RequestContext(request))
        feed.add_item(
            title=_("Comment"),
            link=feed.site_base + comment.document.get_absolute_url()[1:] + "#comments",
            description=descr,
            author_name=force_unicode(comment.user.profile),
            author_link=comment.user.profile.get_absolute_url(),
            pubdate=comment.created,
        )
    response = HttpResponse(mimetype=feed.mime_type)
    feed.write(response, 'utf-8')
    return response

def post_comments_feed(request, obj):
    feed = _feed(request, title=_("Comments on '%s'") % force_unicode(obj))
    comments = obj.comments.filter(removed=False).order_by('-created')
    for comment in comments:
        descr = render_to_string("comments/_comment.html", {
                'comment': comment
            }, context_instance=RequestContext(request))
        feed.add_item(
            title=_("Comment"),
            #HACK -- making URLs absolute
            link=feed.site_base + obj.get_absolute_url()[1:] + "#comments",
            description=descr,
            author_name=force_unicode(comment.user.profile),
            author_link=comment.user.profile.get_absolute_url(),
            pubdate=comment.created,
        )

    response = HttpResponse(mimetype=feed.mime_type)
    feed.write(response, 'utf-8')
    return response
