from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from .models import Project
from .ai_services import ai_magic_fill

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'built_during', 'is_live', 'is_featured', 'category', 'views', 'order')
    list_editable = ('built_during', 'is_featured', 'is_live', 'order', 'category')
    search_fields = ('title', 'description', 'role', 'category')
    list_filter = ('built_during', 'is_featured', 'is_live', 'category', 'is_backend_by_me', 'has_team')
    readonly_fields = ('github_updated_at', 'views')
    
    change_form_template = "admin/projects/project/change_form.html"
    
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
        ('GitHub Statistics', {
            'fields': ('github_stars', 'github_forks', 'github_updated_at'),
            'description': 'View or manually update GitHub statistics.'
        }),
    )


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/ai-magic-fill/', self.admin_site.admin_view(self.ai_magic_fill_view), name='projects-ai-magic-fill'),
        ]
        return custom_urls + urls

    def ai_magic_fill_view(self, request, object_id):
        project = self.get_object(request, object_id)
        if not project:
            self.message_user(request, "Project not found.", level='error')
            return HttpResponseRedirect("../../")
            
        if not project.github:
            self.message_user(request, "GitHub URL is required for AI Magic Fill. Please add it and save first.", level='error')
        else:
            data, error_msg = ai_magic_fill(project.github)
            if data:
                project.overview = data.get('overview', project.overview)
                project.tech_stack = data.get('tech_stack', project.tech_stack)
                project.key_features = data.get('key_features', project.key_features)
                project.category = data.get('category', project.category)
                project.role = data.get('role', project.role)
                project.lighthouse_performance = data.get('lighthouse_performance', project.lighthouse_performance)
                project.lighthouse_seo = data.get('lighthouse_seo', project.lighthouse_seo)
                project.lighthouse_accessibility = data.get('lighthouse_accessibility', project.lighthouse_accessibility)
                project.save()
                self.message_user(request, f"✨ AI Magic Fill successful for '{project.title}'! All fields have been updated based on the repository content.")
            else:
                self.message_user(request, f"AI Magic Fill failed: {error_msg}", level='error')
        
        return HttpResponseRedirect("../change/")

