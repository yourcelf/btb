from django import template
from django.conf import settings
from django.contrib.sites.models import Site

def public_url(private_url):
    return "%s%s" % (settings.PUBLIC_MEDIA_URL,
            private_url[len(settings.MEDIA_URL):])

def site_url(relative):
    if relative.startswith("http"):
        return relative
    return "http://%s%s" % (Site.objects.get_current().domain, relative)

register = template.Library()
register.filter('public_url', public_url)
register.filter('site_url', site_url)
