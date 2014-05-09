from django.contrib import admin

from correspondence.models import Letter, StockResponse

for model in (Letter, StockResponse):
    admin.site.register(model)

