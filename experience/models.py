from django.db import models

class Experience(models.Model):
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.CharField(max_length=100) # e.g., "Jun 2023"
    end_date = models.CharField(max_length=100, blank=True, null=True) # e.g., "Aug 2023"
    is_current = models.BooleanField(default=False)
    
    description = models.TextField(blank=True, null=True)
    responsibilities = models.JSONField(default=list, blank=True)
    tech_stack = models.JSONField(default=list, blank=True)
    
    logo = models.URLField(max_length=500, blank=True, null=True)
    website = models.URLField(max_length=500, blank=True, null=True)
    
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.role} at {self.company_name}"

    class Meta:
        ordering = ['order', '-id']
