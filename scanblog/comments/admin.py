from django.contrib import admin

from comments.models import Comment, CommentRemoval, RemovalReason

class CommentAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'removed', 'created']
    list_filter = ['removed', 'created']
admin.site.register(Comment, CommentAdmin)

class CommentRemovalAdmin(admin.ModelAdmin):
    list_display = ['comment', 'date', 'reason']
    list_filter = ['reason']
admin.site.register(CommentRemoval, CommentRemovalAdmin)

class RemovalReasonAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['default_web_message', 'default_comment_author_message',
            'default_post_author_message']
admin.site.register(RemovalReason, RemovalReasonAdmin)


