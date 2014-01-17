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

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'created']
    search_fields = ['title', 'author__profile__display_name',
                     'body', 'transcription__revisions__body']
    date_hierarchy = 'created'
    list_filter = ['type', 'status', 'author', 'author__profile__managed']
admin.site.register(Document, DocumentAdmin)

admin.site.register(DocumentPage)
admin.site.register(Transcription)
