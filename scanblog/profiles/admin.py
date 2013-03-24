from django.contrib import admin

from profiles.models import *

for model in (Profile,):
    admin.site.register(model)

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'public', 'members_count', 'moderators_list')
    list_filter = ('public',)
    search_fields = ('name', 'about', 'footer')
    filter_horizontal = ('moderators', 'members')
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Organization, OrganizationAdmin)

class AffiliationAdmin(admin.ModelAdmin):
    model = Affiliation
    list_display = ('title', 'public', 'created', 'total_num_responses')
    prepopulated_fields = {"slug": ("title",)}
    exclude = ('modified', 'created')
admin.site.register(Affiliation, AffiliationAdmin)
