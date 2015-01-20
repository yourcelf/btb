from django.contrib import admin

from annotations.models import Note, Tag, ReplyCode

class ReplyCodeAdmin(admin.ModelAdmin):
    search_fields = ['code']
    list_filter = ['document__author']
admin.site.register(ReplyCode, ReplyCodeAdmin)

for model in (Note,Tag):
    admin.site.register(model)
