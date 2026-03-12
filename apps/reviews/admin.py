from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'rating', 'content_type', 'object_id', 'created_at')
    list_filter = ('rating', 'content_type')
    search_fields = ('reviewer__email', 'comment')
    ordering = ('-created_at',)
