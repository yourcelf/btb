from django.conf.urls import *

from campaigns.views import CampaignsJSON

urlpatterns = patterns('campaigns.views',
    url(r'^campaigns.json$', CampaignsJSON.as_view()), 
)
