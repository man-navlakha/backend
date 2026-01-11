from django.contrib import admin
from .models import Project
from .utils import update_all_project_stats

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'built_during', 'is_live', 'is_featured', 'category', 'views', 'order')
    list_editable = ('built_during', 'is_featured', 'is_live', 'order', 'category')
    search_fields = ('title', 'description', 'role', 'category')
    list_filter = ('built_during', 'is_featured', 'is_live', 'category', 'is_backend_by_me', 'has_team')
    readonly_fields = ('github_updated_at', 'views')
    
    filter_horizontal = ('related_projects',) # For easy multi-select
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'overview', 'date', 'role', 'category', 'built_during', 'status', 'is_featured', 'is_live', 'order')
        }),
        ('Performance & Quality', {
            'fields': (
                'lighthouse_performance', 'lighthouse_seo', 'lighthouse_accessibility', 
                'test_coverage', 'languages_distribution'
            ),
            'description': 'Show off your technical excellence with real benchmarks.'
        }),
        ('Availability & Tech', {
            'fields': ('is_app_available', 'app_link', 'api_docs_link', 'is_web_available', 'is_backend_by_me', 'has_figma'),
            'description': 'Toggles for showing platform availability and specialized links.'
        }),
        ('Team & Connections', {
            'fields': ('has_team', 'team_members', 'related_projects'),
            'description': 'Credit your team and link to similar work.'
        }),
        ('Impact & Performance', {
            'fields': ('views', 'key_features'),
        }),
        ('Media & Visuals', {
            'fields': ('logo', 'main_image', 'tech_stack', 'screenshots'),
            'description': 'The primary branding, main image, and gallery screenshots.'
        }),
        ('Links', {
            'fields': ('website', 'github', 'figma')
        }),
        ('GitHub Statistics (Auto-synced)', {
            'fields': ('github_stars', 'github_forks', 'github_updated_at'),
            'description': 'These fields are automatically updated from GitHub but can be adjusted here if needed.'
        }),
    )

    actions = ['sync_github_stats']

    @admin.action(description='🔄 Sync selected projects with GitHub')
    def sync_github_stats(self, request, queryset):
        # We can optimize this to only sync the selected ones, 
        # but for simplicity using the existing utility
        update_all_project_stats()
        self.message_user(request, "Successfully triggered GitHub sync for all projects.")
