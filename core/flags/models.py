from django.db import models

class Flag(models.Model):
    """Model for storing feature flags."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    default = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        db_table = 'core_feature_flags'
        ordering = ['name']

    def __str__(self):
        return self.name 