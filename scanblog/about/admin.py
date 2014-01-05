from django.contrib import admin

from about.models import SiteBanner

class SiteBannerAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'start_date', 'end_date', 'is_current']
    search_fields = ['html']
admin.site.register(SiteBanner, SiteBannerAdmin)
