from django.contrib import admin
from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'body', 'created_at', 'is_read')


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
    list_display = ('id', 'subject', 'updated_at')
    filter_horizontal = ('participants',)
