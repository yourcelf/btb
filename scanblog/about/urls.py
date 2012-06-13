from django.conf.urls.defaults import *
from django.views.generic.base import TemplateView

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="about/index.html"),
        name="about"),
    url(r'^copyright/$', TemplateView.as_view(template_name="about/copyright.html"),
        name="about.copyright"),
    url(r'^faq/$', TemplateView.as_view(template_name="about/faq.html"),
        name="about.faq"),
    url(r'^resources/$', TemplateView.as_view(template_name="about/resources.html"),
        name="about.resources"),
    url(r'^guidelines/$', TemplateView.as_view(template_name="about/guidelines.html"),
        name="about.community_guidelines"),
    url(r'^terms/$', TemplateView.as_view(template_name="about/terms.html"),
        name="about.terms"),
    url(r'^privacy/$', TemplateView.as_view(template_name="about/privacy.html"),
        name="about.privacy"),
    url(r'^dmca/$', TemplateView.as_view(template_name="about/dmca.html"),
        name="about.dmca"),
    url(r'^join/$', TemplateView.as_view(template_name="about/get_involved.html"),
        name="about.get_involved"),
)
