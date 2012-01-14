from django import template
register = template.Library()

from correspondence import utils
from django.contrib.sites.models import Site

@register.filter
def tex_escape(value):
    return utils.tex_escape(value)

@register.filter
def absolute_url(relative):
    return "http://%s%s" % (Site.objects.get_current().domain, relative)
