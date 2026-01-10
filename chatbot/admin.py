from django.contrib import admin
from .models import HiringRequest, ContactRequest

@admin.register(HiringRequest)
class HiringRequestAdmin(admin.ModelAdmin):
    # This determines which fields are shown in the main list view
    list_display = ('name', 'email', 'status', 'created_at')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'message')
    list_filter = ('status', 'created_at')
    fields = ('name', 'email', 'message', 'status', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    # This determines which fields are shown in the main list view for Contact Requests
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_editable = ('status',)
    # This allows you to search by these fields
    search_fields = ('name', 'email', 'subject', 'message')
    # This adds a filter sidebar
    list_filter = ('status', 'created_at')
    # This determines how the detail view looks (when you click on an item)
    # Showing all available details
    fields = ('name', 'email', 'subject', 'message', 'status', 'created_at')
    readonly_fields = ('created_at',)