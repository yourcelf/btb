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

#class AuthorFilter(admin.SimpleListFilter):
#    title = 'Author'
#    parameter_name = 'author_id'
#
#    def lookups(self, request, model_admin):
#        qs = model_admin.queryset(request)
#        return sorted(qs.filter(author__profile__blogger=True).order_by().values_list(
#                    'author_id', 'author__profile__display_name'
#                ).distinct(), key=lambda a: a[1])
#
#    def queryset(self, request, queryset):
#        if self.value():
#            return queryset.filter(author_id=self.value())
#        return queryset

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['get_title', 'author', 'status', 'created']
    search_fields = ['title', 'author__profile__display_name',
                     'body', 'transcription__revisions__body']
    date_hierarchy = 'created'
    list_filter = ['type', 'status', 'author__profile__managed']#, AuthorFilter]
admin.site.register(Document, DocumentAdmin)

admin.site.register(DocumentPage)
admin.site.register(Transcription)
