from django.contrib import admin

from scanning.models import PendingScan, Document, DocumentPage, Scan, ScanPage, Transcription

class ScanPageInline(admin.TabularInline):
    model = ScanPage
class ScanAdmin(admin.ModelAdmin):
    model = Scan
    inlines = [ScanPageInline]
admin.site.register(Scan, ScanAdmin)

class PendingScanAdmin(admin.ModelAdmin):
    model = PendingScan
    list_display = ('author', 'editor', 'code', 'created', 'completed')
    search_fields = ('code',)
admin.site.register(PendingScan, PendingScanAdmin)


admin.site.register(Transcription)
admin.site.register(Document)
admin.site.register(DocumentPage)
