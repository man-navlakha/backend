from django.contrib import admin
from .models import Experience

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('role', 'company_name', 'start_date', 'end_date', 'is_current', 'order')
    list_editable = ('order', 'is_current')
    search_fields = ('role', 'company_name', 'description')
    list_filter = ('is_current', 'company_name')
