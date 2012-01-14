from django.contrib import admin

from correspondence.models import Letter

for model in (Letter,):
    admin.site.register(model)

