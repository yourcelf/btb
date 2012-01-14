from django.contrib import admin
from btb.models import MailDrop

class MailDropAdmin(admin.ModelAdmin):
    list_display = ('description', 'address', 'id')
    search_fields = ('description', 'address')
admin.site.register(MailDrop, MailDropAdmin)
