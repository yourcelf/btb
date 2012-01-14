from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {"template": "about/index.html"}, name="about"),
    url(r'^copyright/$', direct_to_template, {"template": "about/copyright.html"}, name="about.copyright"),
    url(r'^faq/$', direct_to_template, {"template": "about/faq.html"}, name="about.faq"),
    url(r'^resources/$', direct_to_template, {"template": "about/resources.html"}, name="about.resources"),
    url(r'^guidelines/$', direct_to_template, {"template": "about/guidelines.html"}, name="about.community_guidelines"),
    url(r'^terms/$', direct_to_template, {"template": "about/terms.html"}, name="about.terms"),
    url(r'^privacy/$', direct_to_template, {"template": "about/privacy.html"}, name="about.privacy"),
    url(r'^dmca/$', direct_to_template, {"template": "about/dmca.html"}, name="about.dmca"),
    url(r'^join/$', direct_to_template, {"template": "about/get_involved.html"}, name="about.get_involved"),
)
