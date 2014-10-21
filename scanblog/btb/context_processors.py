from django.conf import settings
from django.contrib.sites.models import Site

def site(request):
    site = Site.objects.get_current()
    site.email = settings.SITE_EMAIL
    return {
        'site': site,
        'scheme': 'http://',
        'base_url': 'http://%s' % site.domain,
        'comments_open': settings.COMMENTS_OPEN,
        'transcription_open': settings.TRANSCRIPTION_OPEN,
    }
