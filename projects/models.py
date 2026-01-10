from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField() # Short description/tagline
    overview = models.TextField(blank=True, null=True) # Detailed project overview
    date = models.CharField(max_length=100, blank=True, null=True)
    tech_stack = models.JSONField(default=list, blank=True)
    screenshots = models.JSONField(default=list, blank=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    github = models.URLField(max_length=500, blank=True, null=True)
    figma = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    order = models.IntegerField(default=0)
    
    # Premium Features
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    role = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    key_features = models.JSONField(default=list, blank=True)
    
    # Context & Purpose
    CONTEXT_CHOICES = [
        ('college', 'College Project'),
        ('freelance', 'Freelance Work'),
        ('personal', 'Personal Experiment'),
        ('hackathon', 'Hackathon'),
        ('professional', 'Professional/Job'),
    ]
    built_during = models.CharField(max_length=50, choices=CONTEXT_CHOICES, default='personal')
    
    # Technical Metrics
    lighthouse_performance = models.PositiveIntegerField(default=0, help_text="0-100")
    lighthouse_seo = models.PositiveIntegerField(default=0, help_text="0-100")
    lighthouse_accessibility = models.PositiveIntegerField(default=0, help_text="0-100")
    test_coverage = models.PositiveIntegerField(default=0, help_text="Percentage (e.g., 95)")
    languages_distribution = models.JSONField(default=dict, blank=True, help_text='e.g., {"Python": 60, "JS": 40}')
    
    # Project Status & Availability
    is_live = models.BooleanField(default=False) # In market or used by users
    is_app_available = models.BooleanField(default=False)
    app_link = models.URLField(max_length=500, blank=True, null=True)
    api_docs_link = models.URLField(max_length=500, blank=True, null=True)
    is_web_available = models.BooleanField(default=True)
    is_backend_by_me = models.BooleanField(default=True)
    has_figma = models.BooleanField(default=False)
    
    # Media
    logo = models.URLField(max_length=500, blank=True, null=True)
    main_image = models.URLField(max_length=500, blank=True, null=True)
    
    # Team & Relations
    has_team = models.BooleanField(default=False)
    team_members = models.JSONField(default=list, blank=True) # [{"name": "...", "github": "..."}]
    related_projects = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # GitHub Stats
    github_stars = models.IntegerField(default=0)
    github_forks = models.IntegerField(default=0)
    github_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'id']
