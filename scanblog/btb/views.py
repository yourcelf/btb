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
    comments = Comment.objects.excluding_boilerplate_and_responses().filter(
            comment_doc__isnull=True
        ).order_by('-created')[0:5]
    return render(request, "home.html", {
        'featured': featured,
        'comments': comments,
    })

@permission_required("scanning.change_scan")
def private_media(request, path):
    if "thumbnail" in request.GET:
        im = get_thumbnail(path, request.GET['thumbnail'])
        path = im.name
    if settings.X_SENDFILE_ENABLED:
        response = HttpResponse()
        response['X-Sendfile'] = os.path.join(settings.MEDIA_ROOT, path)
        return response
    elif settings.X_ACCEL_REDIRECT_ENABLED:
        response = HttpResponse()
        del response['Content-Type'] # let nginx infer content type
        response['X-Accel-Redirect'] = "/private_media_serve/{}".format(path)
        return response
    return serve(request, path=path, document_root=settings.MEDIA_ROOT)
