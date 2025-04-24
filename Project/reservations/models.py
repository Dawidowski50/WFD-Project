from django.db import models
from django.utils import timezone
from django.conf import settings
from inventory.models import Item
from django.contrib.auth import get_user_model

# Get the custom user model
User = get_user_model()

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Reservation #{self.id} by {self.user.username}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.start_date and not timezone.is_aware(self.start_date):
            self.start_date = timezone.make_aware(self.start_date)
        if self.end_date and not timezone.is_aware(self.end_date):
            self.end_date = timezone.make_aware(self.end_date)
        if not self.id:  # New instance
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

class ReservationItem(models.Model):
    # Links items to reservations
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.item.name} x{self.quantity} for Reservation #{self.reservation.id}"

    class Meta:
        unique_together = ['reservation', 'item']

    def save(self, *args, **kwargs):
        if not self.id:  # New instance
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
