from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import Item, Maintenance  # Import Item and Maintenance

# Create your models here.

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        
        if creating or 'role' in kwargs.get('update_fields', []):
            # Update user status without triggering signals
            User = self.user.__class__
            User.objects.filter(pk=self.user.pk).update(
                is_staff=self.role in ['staff', 'manager', 'admin'],
                is_superuser=self.role == 'admin'
            )

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'userprofile'):
        # Only create profile if it doesn't exist
        role = 'admin' if instance.is_superuser else 'staff' if instance.is_staff else 'customer'
        UserProfile.objects.create(user=instance, role=role)

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.item.name} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        if not self.total_cost and self.start_date and self.end_date and self.item:
            # Calculate the number of days
            days = (self.end_date - self.start_date).days + 1
            # Calculate total cost
            self.total_cost = self.item.daily_rate * days
        super().save(*args, **kwargs)
