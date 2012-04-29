import json

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.core import paginator
from django.db.models import Count
from django.http import Http404
from djcelery.models import TaskMeta

from scanning.models import Document, Scan, DocumentPage, EditLock
from scanning import tasks as scanning_tasks
from profiles.models import Profile, Organization
from annotations.models import Tag
from django.contrib.auth.models import User
from correspondence.models import Letter
from comments.models import Comment
from btb.utils import dthandler

@permission_required("scanning.add_scan")
def home(request):
    """
    Single page app for scanning/moderation.
    """
    orgs = Organization.objects.org_filter(request.user)
    return render(request, "moderation/home.html", {
        'document_states': Document.STATES,
        'organizations_json': json.dumps(
            [o.to_dict() for o in orgs]
        )
    })

#TODO  better permission here
@permission_required("correspondence.manage_correspondence")
def manage_tasks(request):
    tasks = TaskMeta.objects.all().order_by('-date_done')
    status = request.GET.get("status", "")
    if status:
        tasks = tasks.filter(status=status)
    p = paginator.Paginator(tasks, 10)
    try:
        page = p.page(request.GET.get('page', 1))
    except (ValueError, paginator.EmptyPage):
        page = p.page(1)
    return render(request, "moderation/manage_tasks.html", { 
        'page': page,
        'status': status
    })

@login_required
def wait_for_processing(request, task_id):
    return render(request, 
            "moderation/wait_for_processing.html", 
            { 'task_id': task_id, })

def _date_aggregate(queryset, date_field, precision='week'):
    return queryset.extra(
            select={precision: """DATE_TRUNC('%s', %s)""" % (precision, date_field)}
        ).values(
            precision
        ).annotate(count=Count('pk')).order_by(precision)

#TODO: better permission here
@permission_required("correspondence.manage_correspondence")
def stats(request):
    just_profiles = set()
    just_posts = set()
    posts_and_profiles = set()
    with_profiles = set(Profile.objects.bloggers_with_profiles())
    with_posts = set(Profile.objects.bloggers_with_posts())
    for p in with_posts:
        if p not in with_profiles:
            just_posts.add(p)
        else:
            posts_and_profiles.add(p)
    for p in with_profiles:
        if p not in with_posts:
            just_profiles.add(p)
    enrolled = set(Profile.objects.enrolled())
    not_published = enrolled - with_profiles - with_posts

    waitlisted = Profile.objects.waitlisted().count() 
    waitlistable = Profile.objects.waitlistable().count()
    invited = Profile.objects.invited().count()

    stats = {
        'users': {
            'counts': {
                'name': 'All users',
                'size': Profile.objects.count(),
                'children': [
                    {
                        'name': 'Total active users',
                        'size': Profile.objects.active().count(),
                        'children': [
                            {
                                'name': 'Commenters',
                                'size': Profile.objects.commenters().count(),
                            },
                            {
                                'name': 'Bloggers',
                                'size': Profile.objects.bloggers().count(),
                                'children': [
                                    {
                                        'name': 'Not enrolled',
                                        'size': waitlisted + waitlistable + invited,
                                        'children': [
                                            {
                                                'name': 'Waitlisted',
                                                'size': Profile.objects.waitlisted().count()
                                            },
                                            {
                                                'name': 'Waitlistable',
                                                'size': Profile.objects.waitlistable().count(),
                                            },
                                            {
                                                'name': 'Invited',
                                                'size': Profile.objects.invited().count(),
                                            },
                                        ],
                                    },
                                    {
                                        'name': 'Enrolled',
                                        'size': Profile.objects.enrolled().count(),
                                        'children': [
                                            {
                                                'name': 'Just profiles',
                                                'size': len(just_profiles),
                                            },
                                            {
                                                'name': 'Just posts',
                                                'size': len(just_posts),
                                            },
                                            {
                                                'name': 'With both posts and profiles',
                                                'size': len(posts_and_profiles),
                                            },
                                            {
                                                'name': 'Nothing published',
                                                'size': len(not_published),
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'name': 'Total inactive users',
                        'size': Profile.objects.inactive().count(),
                        'children': [
                            {
                                'name': 'Commenters, inactive',
                                'size': Profile.objects.inactive_commenters().count(),
                            }, 
                            {
                                'name': 'Bloggers, inactive',
                                'size': Profile.objects.inactive_bloggers().count(),
                            }
                        ]
                    }
                ]
            },
            'time_series': {
                'waitlist': list(_date_aggregate(Profile.objects.bloggers(), 'date_joined')),
                'enrolled': list(_date_aggregate(Letter.objects.filter(type='signup_complete'), 'sent')),
                'commenters': list(_date_aggregate(Profile.objects.commenters(), 'date_joined')),
            },
        },
        'documents': {
            'time_series': {
                'posts': list(_date_aggregate(Document.objects.public().filter(type="post"), 'date_written')),
                'profiles': list(_date_aggregate(Document.objects.public().filter(type="profile"), 'date_written')),
                'requests': list(_date_aggregate(Document.objects.filter(type="request"), 'date_written')),
            },
            'post_impact': list(Profile.objects.enrolled().annotate(
                    count=Count('user__documents_authored')
                ).values('count', 'display_name')),
            'page_impact': list(Profile.objects.enrolled().annotate(
                    count=Count('user__documents_authored__documentpage')
                ).values('count', 'display_name')),
            'posts': {
                'total': Document.objects.filter(type="post").count(),
                'published': Document.objects.public().filter(type="post").count(),
                'ready_to_publish': Document.objects.ready().filter(type="post").count(),
            },
            'profiles': {
                'total': Document.objects.filter(type="profile").count(),
                'published': len(with_profiles),
                'ready_to_publish': Document.objects.ready().filter(type="profile").count(),
            },
        },
        'letters': {
            'time_series': {
                'letter': list(_date_aggregate(Letter.objects.sent().filter(type='letter'), 'sent')),
                'consent form': list(_date_aggregate(Letter.objects.sent().filter(type='consent_form'), 'sent')),
                'signup complete': list(_date_aggregate(Letter.objects.sent().filter(type='signup_complete'), 'sent')),
                'first post': list(_date_aggregate(Letter.objects.sent().filter(type='first_post'), 'sent')),
                #'printout': list(_date_aggregate(Letter.objects.sent().filter(type='printout'), 'sent')),
                'comments': list(_date_aggregate(Letter.objects.sent().filter(type='comments'), 'sent')),
                'waitlist': list(_date_aggregate(Letter.objects.sent().filter(type='waitlist'), 'sent')),
                'other': list(_date_aggregate(Letter.objects.sent().filter(type=''), 'sent')),
            },
            'impact': list(
                Profile.objects.active().annotate(
                    count=Count('user__received_letters')
                ).filter(count__gt=0).values('count', 'display_name')
            )
        },
        'comments': {
            'total': Comment.objects.public().count(),
            'time_series': {
                'comments posted': list(_date_aggregate(Comment.objects.public(), '"comments_comment"."created"')),
            },
            'by_user': list(User.objects.annotate(
                    count=Count('comment')
                ).filter(
                    count__gt=0
                ).values('count', 'username')),
            'impact': list(
                User.objects.annotate(count=Count('comment')).filter(count__gt=0).values('count', 'username'),
            )
        }

    }
    return render(request, "moderation/stats.html", {
        'stats': json.dumps(stats, default=dthandler)
    })

@permission_required("scanning.add_scan")
def page_picker(request):
    pages = DocumentPage.objects.filter(
            document__status="published",
            document__author__is_active=True,
            document__author__profile__blogger=True,
            document__author__profile__consent_form_received=True)
        
    return render(request, "moderation/page_picker.html", {
        'pages': pages,
    })
 
@permission_required("scanning.tag_posts")
def tagparty(request):
    return render(request, "moderation/tagparty.html", {
        'tags': Tag.objects.all(),
    })

@permission_required("scanning.tag_posts")
def tagparty_next(request):
    try:
        doc = Document.objects.public().order_by('created').filter(
                type="post",
                tags__isnull=True,
                editlock__isnull=True,
        )[0]
    except IndexError:
        raise Http404

    lock = EditLock.objects.create(user=request.user, document=doc)
    scanning_tasks.expire_editlock.apply_async(args=[lock.id], countdown=60*5)

    return redirect(doc.get_absolute_url())

