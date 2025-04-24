from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone

# Create models

class Category(models.Model):
    # Basic category information
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

class Item(models.Model):
    # Equipment item details
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    condition = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_maintained = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Maintenance(models.Model):
    # Maintenance scheduling and tracking
    item = models.ForeignKey('Item', related_name='maintenance_records', on_delete=models.CASCADE)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    maintenance_date = models.DateTimeField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ], default='SCHEDULED')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Maintenance for {self.item.name} on {self.maintenance_date}"

    def save(self, *args, **kwargs):
        if self.maintenance_date and not timezone.is_aware(self.maintenance_date):
            self.maintenance_date = timezone.make_aware(self.maintenance_date)
        if not self.id:  # New instance
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-maintenance_date']
