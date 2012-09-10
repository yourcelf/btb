from django.contrib import admin

from campaigns.models import Campaign

class CampaignAdmin(admin.ModelAdmin):
    model = Campaign
    list_display = ('title', 'public', 'created', 'ended', 'num_responses')
admin.site.register(Campaign, CampaignAdmin)
