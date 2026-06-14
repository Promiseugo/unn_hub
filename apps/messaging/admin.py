from django.contrib import admin
from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'body', 'original_body', 'moderation_status', 'moderation_reasons', 'created_at', 'is_read')


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
    list_display = ('id', 'subject', 'updated_at')
    filter_horizontal = ('participants',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'moderation_status', 'is_read', 'created_at')
    list_filter = ('moderation_status', 'is_read')
    search_fields = ('body', 'original_body', 'sender__email', 'thread__subject')
    readonly_fields = ('created_at', 'updated_at')
