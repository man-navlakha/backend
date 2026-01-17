from django.db import models

class Experience(models.Model):
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    period = models.CharField(max_length=255, blank=True, null=True) # e.g., "Aug 2023 - Oct 2023"
    location = models.CharField(max_length=255, blank=True, null=True)
    
    start_date = models.CharField(max_length=100, blank=True, null=True) # kept for backward compatibility
    end_date = models.CharField(max_length=100, blank=True, null=True)
    is_current = models.BooleanField(default=False)
    
    description = models.TextField(blank=True, null=True)
    responsibilities = models.JSONField(default=list, blank=True)
    technologies = models.JSONField(default=list, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    
    logo = models.URLField(max_length=500, blank=True, null=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.role} at {self.company}"

    class Meta:
        ordering = ['order', '-id']
