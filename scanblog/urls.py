from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.views.static import serve
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Admin
    url(r'^admin/', include(admin.site.urls), name='admin'),

    # Moderator
    url(r'^annotations/', include('annotations.urls')),
    url(r'^correspondence/', include('correspondence.urls')),
    url(r'^moderation/', include('moderation.urls')),
    url(r'^scanning/', include('scanning.urls')),
    url(r'^tasks/', include('djcelery.urls')),
    url(r'^{0}/(?P<path>.*)$'.format(settings.MEDIA_URL[1:-1]), 'btb.views.private_media'),
    # Public
    url(r'^notifications/', include('subscriptions.urls')),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^people/', include('profiles.urls')),
    url(r'^about/', include('about.urls')),
    url(r'^comments/', include('comments.urls')),
    url(r'^r/', include('urlcrypt.urls')),
    url(r'^$',  'btb.views.home', name='home'),
    url(r'', include('blogs.urls')),
)

if settings.DEBUG:
    # Serve public media.
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % settings.PUBLIC_MEDIA_URL[1:-1],
            'django.views.static.serve',
            {'document_root': settings.PUBLIC_MEDIA_ROOT,
             'show_indexes': True}),
    )
