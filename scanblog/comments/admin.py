from django.contrib import admin

from comments.models import Comment

class CommentAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'removed', 'created']
    list_filter = ['removed', 'created']
admin.site.register(Comment, CommentAdmin)

