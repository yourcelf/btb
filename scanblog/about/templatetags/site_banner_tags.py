from django import template

from about.models import SiteBanner

register = template.Library()

@register.inclusion_tag('about/_site_banner.html')
def site_banner():
    try:
        banner = list(SiteBanner.objects.current())[0]
    except IndexError:
        banner = None
    return {'banner': banner}

