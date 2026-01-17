from django.contrib import admin
from .models import Experience

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('role', 'company', 'period', 'is_current', 'order')
    list_editable = ('order', 'is_current')
    search_fields = ('role', 'company', 'description')
    list_filter = ('is_current', 'company')
