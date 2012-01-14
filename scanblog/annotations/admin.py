from django.contrib import admin

from annotations.models import Note, Tag, ReplyCode

for model in (Note,Tag,ReplyCode):
    admin.site.register(model)
