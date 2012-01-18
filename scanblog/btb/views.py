import os
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.views.static import serve
from django.conf import settings
from django.http import HttpResponse

from sorl.thumbnail import get_thumbnail

from scanning.models import Document
from comments.models import Comment

def home(request):
    featured = Document.objects.public().filter(
        type="post", 
        tags__name="featured"
    )[:7] # 7 fits just right on the front page.
    comments = Comment.objects.public().filter(
            comment_doc__isnull=True
        ).order_by('-created')[0:5]
    return render(request, "home.html", {
        'featured': featured,
        'comments': comments,
    })

@permission_required("scanning.change_scan")
def private_media(request, path):
    if "thumbnail" in request.GET:
        im = get_thumbnail(os.path.join(settings.MEDIA_ROOT, path), request.GET['thumbnail'])
        path = im.name
    return serve(request, path=path, document_root=settings.MEDIA_ROOT)


def sopastrike(request):
    with open(os.path.join(settings.SETTINGS_ROOT, "templates", "strike.html")) as fh:
        return HttpResponse(fh.read(), status=503)
