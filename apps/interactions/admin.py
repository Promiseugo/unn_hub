from django.contrib import admin
from .models import Reaction, Comment


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'reaction_type', 'content_type', 'object_id', 'created_at']
    list_filter = ['reaction_type', 'content_type']
    search_fields = ['user__username']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'body_preview', 'content_type', 'object_id', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'content_type']
    search_fields = ['user__username', 'body']
    actions = ['deactivate_comments']

    def body_preview(self, obj):
        return obj.body[:60] + ('…' if len(obj.body) > 60 else '')
    body_preview.short_description = 'Comment'

    def deactivate_comments(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_comments.short_description = 'Deactivate selected comments'
