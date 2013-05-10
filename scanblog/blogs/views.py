# -*- coding: utf-8 -*-
import logging
import json
import math

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.html import escape
from django import forms

from annotations.models import Tag
from scanning.models import Document, DocumentPage
from comments.models import Comment
from comments.forms import CommentForm
from blogs import feeds
from profiles.models import Profile, Organization, Affiliation
from campaigns.models import Campaign

#
# Displaying posts
#
def _paginate(request, qs, count=10):
    p = Paginator(qs, count)
    try:
        page = p.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        raise Http404
    page_links = []
    prev_i = 0
    for i in p.page_range:
        if abs(i - page.number) < 5 or i < 5 or i > p.num_pages - 5:
            if i - prev_i != 1:
                page_links.append("<span class='page-links-break'>...</span> ")
            if i == page.number:
                page_links.append("<span class='current-page'>{0}</span> ".format(i))
            else:
                page_links.append("<a href='?page={0}'>{0}</a> ".format(i))
            prev_i = i

    # XXX failsafe for missing highlight bug.  Ideally, this would never get invoked.
    for post in page.object_list:
        if isinstance(post, Document) and post.type == "post" and not post.body and not post.highlight:
            post.status = "unknown"
            post.save()
            logger = logging.getLogger('django.request')
            logger.error("Post {id} missing highlight.  http://betweenthebars.org/moderation/#/process/document/{id}".format(id=post.pk))
            return _paginate(request, qs, count)

    return {'page': page, 'page_links': page_links}

def author_post_list(request, author_id=None, slug=None):
    # We do show adult posts when looking at individual user's blog; but
    # they're masked in the template.
    posts = Document.objects.public().filter(
            type="post",
            author__pk=author_id,
    )
    try:
        author = User.objects.filter(pk=author_id).select_related('profile')[0]
    except IndexError:
        raise Http404

    if posts.count() == 0:
        raise Http404

    if author.profile.get_blog_slug() != slug:
        return redirect(author.profile.get_blog_url())

    context = _paginate(request, posts)
    try:
        context['author'] = context['page'].object_list[0].author
    except IndexError:
        raise Http404
    context['org'] = author.organization_set.get()
    context['feed_author'] = author
    context.update(get_nav_context())
    context['related'] = {
        'title': "Most recent posts from this author:",
        'items': DocumentPage.objects.filter(order=0,
                    document__author__pk=author.id,
                    document__status="published",
                    document__type="post",
            ).select_related(
                    'document'
            ).order_by('-document__created')[:6]
    }


    return render(request, "blogs/author_post_list.html", context)



def get_nav_context():
    tags = list(Tag.objects.filter(post_count__gte=2).order_by('name'))
    tags.append({
        'post_count': Document.objects.public().filter(type='post').exclude(tags__isnull=False).count()
    })
    # Sort tags into columns.
    columns = []
    logger = logging.getLogger("django.request")
    if tags:
        per_column = max(5, int(math.ceil(len(tags) / 5.)))
        for i in range(0, len(tags), per_column):
            columns.append([])
            for j in range(0, per_column):
                if i + j < len(tags):
                    columns[-1].append(tags[i + j])
    nav_context = {
        'tag_columns': columns,
        'recent_titles': Document.objects.safe().filter(type='post')[:5],
        'recent_authors': Profile.objects.bloggers_with_posts().order_by('-latest_post')[:10],
        'recent_comments': Comment.objects.excluding_boilerplate().order_by('-modified')[:5],
        'campaigns': Campaign.objects.filter(public=True),
        'affiliations': Affiliation.objects.filter(public=True),
    }
    return nav_context

def blogs_front_page(request):
    return posts_by_date(request, template="blogs/blogs_front_page.html")

def posts_by_date(request, template="blogs/all_posts_list.html"):
    """
    Show a list of posts by date
    """
    posts = Document.objects.safe_for_user(request.user).filter(
            type="post"
    )
    context = _paginate(request, posts)
    pnum = context['page'].number
    context.update(get_nav_context())
    context['related'] = {
            'items': DocumentPage.objects.filter(
                        order=0,
                        document__status="published",
                        document__type="post",
                        document__author__profile__consent_form_received=True,
                        document__author__is_active=True,
                        document__adult=False,
                ).select_related(
                        'document'
                ).order_by(
                    '-document__date_written'
                )[pnum*10:pnum*10+7]
    }
    return render(request, template, context)

def show_campaign(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug, public=True)
    posts = Document.objects.safe_for_user(request.user).filter(
            in_reply_to=campaign.reply_code
    )
    context = _paginate(request, posts)
    pnum = context['page'].number
    context.update(get_nav_context())
    context['campaign'] = campaign
    context['related'] = {
        'items': DocumentPage.objects.filter(
                    order=0,
                    document__status="published",
                    document__in_reply_to=campaign.reply_code,
                    document__author__profile__consent_form_received=True,
                    document__author__is_active=True,
                    document__adult=False,
            ).select_related(
                'document'
            ).order_by(
                '-document__date_written'
            )[pnum*10:pnum*10+7]
    }
    return render(request, "blogs/show_campaign.html", context)

def show_affiliation(request, slug):
    affiliation = get_object_or_404(Affiliation, slug=slug, public=True)
    posts = Document.objects.safe_for_user(request.user).filter(affiliation=affiliation)
    context = _paginate(request, posts)
    pnum = context['page'].number
    context.update(get_nav_context())
    context['affiliation'] = affiliation
    context['related'] = {
        'items': DocumentPage.objects.filter(
                    order=0,
                    document__status="published",
                    document__affiliation=affiliation,
                    document__author__profile__consent_form_received=True,
                    document__author__is_active=True,
                    document__adult=False,
            ).select_related(
                'document'
            ).order_by(
                '-document__date_written'
            )[pnum*10:pnum*10+7]
    }
    return render(request, "blogs/show_affiliation.html", context)

def org_post_list(request, slug):
    """
    Show posts per org.
    """
    org = get_object_or_404(Organization, slug=slug, public=True)
    posts = Document.objects.safe_for_user(request.user).filter(
            type="post",
            author__organization=org
    ).distinct()
    context = _paginate(request, posts)
    context['org'] = org
    pnum = context['page'].number
    context.update(get_nav_context())
    context['related'] = {
        'items': DocumentPage.objects.filter(
                    order=0,
                    document__status="published",
                    document__type="post",
                    document__author__profile__consent_form_received=True,
                    document__author__is_active=True,
                    document__author__organization=org,
                    document__adult=False,
            ).distinct().select_related(
                    'document'
            ).order_by(
                '-document__date_written'
            )[pnum*10:pnum*10+7]
    }
    return render(request, "blogs/org_post_list.html", context)

def tagged_post_list(request, tag):
    if tag:
        posts = Document.objects.public().filter(type="post", tags__name=tag.lower())
    else:
        posts = Document.objects.public().filter(type='post', tags__isnull=True)
    context = _paginate(request, posts)
    pnum = context['page'].number
    if tag:
        context['tag'] = get_object_or_404(Tag, name=tag.lower())
        context['related'] = {
            'title': u"Other posts tagged with “%s”" % tag,
            'items': DocumentPage.objects.filter(
                        order=0,
                        document__tags__name=tag.lower(),
                        document__status="published",
                        document__type="post",
                        document__author__profile__consent_form_received=True,
                        document__author__is_active=True,
                        document__adult=False,
                ).distinct().select_related(
                        'document'
                ).order_by(
                    '-document__date_written'
                )[pnum*10:pnum*10+7]
        }
    else:
        context['tag'] = None
        context['related'] = {
            'title': u"Other uncategorized posts",
            'items': DocumentPage.objects.filter(
                        order=0,
                        document__tags__isnull=True,
                        document__status="published",
                        document__type="post",
                        document__author__profile__consent_form_received=True,
                        document__author__is_active=True,
                        document__adult=False,
                ).distinct().select_related(
                        'document'
                ).order_by(
                    '-document__date_written'
                )[pnum*10:pnum*10+7]
        }
    context.update(get_nav_context())
    return render(request, "blogs/tag_post_list.html", context)

def all_comments_list(request):
    context = _paginate(request,
            Comment.objects.excluding_boilerplate().order_by('-created'))
    context.update(get_nav_context())
    return render(request, "blogs/all_comments_list.html", context)

def post_detail(request, post_id=None, slug=None):
    try:
        post = Document.objects.public().get(type="post", pk=post_id)
    except Document.DoesNotExist:
        raise Http404
    if post.get_slug() != slug:
        return redirect(post.get_absolute_url())

    #
    # Comment processing
    #

    # Session pending_comment is set if an unauthenticated user tries to
    # comment.
    pending_comment = request.session.pop('pending_comment', None)
    if pending_comment and pending_comment['comment'] and \
            pending_comment['path'] == request.path:
        form = CommentForm({
            'comment': pending_comment['comment']
        })
    else:
        form = CommentForm(request.POST or None)
    if form.is_valid():
        if request.user.is_authenticated():
            # Use get_or_create to avoid duplicates
            comment, created = Comment.objects.get_or_create(
                document=post,
                comment=form.cleaned_data['comment'],
                user=request.user,
            )
            if created:
                comment.document = post
            #XXX: akismet?
            return redirect("%s#c%s" % (request.path, comment.pk))
        else:
            request.session['pending_comment'] = {
                'comment': form.cleaned_data['comment'],
                'path': request.path,
            }
            messages.info(request, 
                          "To post a reply, you need to log in or sign up.")
            request.session['after_login'] = request.path
            return redirect_to_login(request.path)

    # Document pages
    if post.body:
        # No pages for textual posts.  XXX This is largely untested, and
        # should probably be removed.
        documentpages = []
        remaining = None
        documentpage_count = 0
    else:
        # Pagination for long posts
        try:
            max_page = (int(request.GET.get('minorder', 0)) +
                    settings.SCAN_PAGES_PER_PAGE)
        except ValueError:
            max_page = settings.SCAN_PAGES_PER_PAGE
        pages = post.documentpage_set.all()
        documentpage_count = pages.count()
        documentpages = pages[0:max_page]
        remaining = max(0, documentpage_count - max_page)

    related_items = list(DocumentPage.objects.filter(order=0,
                    document__author__pk=post.author_id,
                    document__status="published",
                    document__type="post",
            ).exclude(
                    document__pk=post.pk
            ).select_related(
                    'document'
            ).order_by('-document__created')[:6])

    related = {
        'more': post.author.profile.get_blog_url() if len(related_items) == 6 else None,
        'title': "Other posts by this author",
        'items': related_items,
    }

    context = get_nav_context()
    context.update({
            'post': post,
            'org': post.author.organization_set.get(),
            'documentpages': documentpages,
            'documentpage_count': documentpage_count,
            'remaining': remaining,
            'comments': post.comments.with_mailed_annotation(),
            'comment_form': form,
            'related': related,
        })
    return render(request, "blogs/post_detail.html", context)

def more_pages(request, post_id):
    try:
        min_order = int(request.GET['minorder'])
    except (ValueError, KeyError):
        raise Http404
    try:
        post = Document.objects.safe_for_user(request.user).filter(
                type="post", pk=post_id)[0]
    except IndexError:
        raise Http404

    # NOTE: We used to serve 'more' pages 6 at a time, but are currently
    # serving all remaining pages with 1 click.
    documentpage_count = post.documentpage_set.count()
    return render(request, "blogs/_post_pagegroup.html", {
        'post': post,
        'documentpage_count': documentpage_count,
        'documentpages': post.documentpage_set.all()[min_order:],
        'remaining': 0,
    })

def post_tag_list(request):
    term = request.GET.get("term", "")
    vals = Tag.objects.filter(name__icontains=term).values_list('name', flat=True)
    response = HttpResponse(mimetype="application/json")
    response.write(json.dumps(list(vals)))
    return response

@permission_required("scanning.tag_post")
def save_tags(request, post_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    post = get_object_or_404(Document, pk=post_id, type='post')
    names = [t.strip().lower() for t in request.POST.get("tags").split(",") if t.strip()]
    tags = []
    for name in names:
        tag = Tag.objects.get(name=name)
        tags.append(tag)
    post.tags = tags
    return HttpResponse("success")
        

#
# Feeds
#

def _choose_feed(request, context):
    if request.GET.get('full'):
        return feeds.full_posts_feed(request, context)
    return feeds.posts_feed(request, context)

def all_posts_feed(request):
    return _choose_feed(request, {
        'title': "Recent posts from all authors",
        'posts': Document.objects.safe().filter(type="post")
    })

def campaign_feed(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug, public=True)
    return _choose_feed(request, {
        'title': campaign.title,
        'posts': Document.objects.safe().filter(in_reply_to_id=campaign.reply_code_id)
    })

def affiliation_feed(request, slug):
    affiliation = get_object_or_404(Affiliation, slug=slug, public=True)
    return _choose_feed(request, {
        'title': affiliation.title,
        'posts': Document.objects.safe().filter(affiliation=affiliation),
    })

def org_post_feed(request, slug, filtered=True):
    org = get_object_or_404(Organization, slug=slug, public=True)
    docs = Document.objects.public().filter(
            author__organization=org,
            type="post"
     ).distinct()
    if filtered:
        docs = docs.filter(adult=False)
    return _choose_feed(request, {
        'title': "Recent posts from %s" % org.name,
        'posts': docs,
    })

def all_comments_feed(request):
    comments = Comment.objects.excluding_boilerplate().exclude(
            comment_doc__isnull=False).order_by('-created')[0:10]
    return feeds.all_comments_feed(request, comments)

def post_comments_feed(request, post_id):
    document = get_object_or_404(Document, pk=post_id)
    return feeds.post_comments_feed(request, document)

def tagged_post_feed(request, tag):
    return _choose_feed(request, {
        'title': "%s posts" % escape(tag.capitalize()),
        'posts': Document.objects.public().filter(tags__name=tag.lower(), type='post')
    })
def legacy_author_post_feed(request, author_id, slug):
    # We're stripping out author slugs from feed URLs, so feed readers don't
    # get borked if the display name changes.
    return redirect("blogs.author_post_feed", author_id)

def author_post_feed(request, author_id):
    try:
        author = Profile.objects.enrolled().filter(pk=author_id)[0].user
    except IndexError:
        raise Http404
    posts = author.documents_authored.public().filter(type="post")
    return _choose_feed(request, {
        'title': "Posts by %s" % unicode(author.profile),
        'posts': posts,
    })

def page_picker(request):
    context = get_nav_context()
    context['PUBLIC_MEDIA_URL'] = settings.PUBLIC_MEDIA_URL
    return render(request, "blogs/page_picker.html", context)

#
# Textual posts, edited by author
#

def _assert_can_manage_posts(request):
    if not (request.user.profile.blogger and (not request.user.profile.managed)):
        raise PermissionDenied

class PostForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea, required=True)
    status = forms.ChoiceField(choices=(('unknown', 'Draft'), ('published', 'Publish')))
    class Meta:
        model = Document
        fields = ('title', 'body', 'status')

@login_required
def edit_post(request, post_id=None):
    _assert_can_manage_posts(request)
    if post_id:
        post = get_object_or_404(Document, pk=post_id, author=request.user)
    else:
        post = Document(author=request.user, editor=request.user, type="post")
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid() and not post.scan_id:
        post = form.save()
        tag_names = [t.lower().strip() for t in request.POST.getlist('tags')]
        tag_objs = [Tag.objects.get_or_create(name=name)[0] for name in tag_names if name]
        post.tags = set(tag_objs)
        if post.status == "published":
            messages.info(request, "Post saved and published.")
            return redirect("blogs.post_show", post_id=post.pk, slug=post.get_slug())
        else:
            messages.info(request, "Post saved as a draft.")
            return redirect("blogs.manage_posts")
    return render(request, "blogs/edit_post.html", {
        'post': post,
        'form': form,
    })

@login_required
def manage_posts(request):
    _assert_can_manage_posts(request)
    posts = Document.objects.filter(type='post', author=request.user)
    return render(request, "blogs/manage_posts.html", {
        'posts': posts,
    })

@login_required
def delete_post(request, post_id):
    _assert_can_manage_posts(request)
    post = get_object_or_404(Document, pk=post_id, author=request.user)
    if request.method == 'POST':
        post.full_delete()
        messages.info(request, "Post deleted.")
        return redirect("blogs.manage_posts")
    return render(request, "blogs/delete_post.html", {
        'post': post,
    })
