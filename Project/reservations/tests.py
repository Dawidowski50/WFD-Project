from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import UserProfile
from inventory.models import Category, Item
from reservations.models import Reservation, ReservationItem
from decimal import Decimal

User = get_user_model()

class ReservationTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        # Update the automatically created profile
        self.user.userprofile.role = 'customer'
        self.user.userprofile.save()
        
        # Create test category and item
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        self.item = Item.objects.create(
            name='Test Item',
            description='Test Description',
            category=self.category,
            daily_rate=Decimal('50.00'),
            condition='excellent',
            is_available=True
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass')

    def test_reserve_item(self):
        # Test GET request (should redirect to catalog)
        response = self.client.get(reverse('reserve_item', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('catalog'))

        # Test POST with valid dates
        start_date = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.post(reverse('reserve_item', args=[self.item.id]), {
            'start_date': start_date,
            'end_date': end_date
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('my_reservations'))
        self.assertTrue(Reservation.objects.filter(user=self.user).exists())

        # Test POST with invalid dates
        response = self.client.post(reverse('reserve_item', args=[self.item.id]), {
            'start_date': 'invalid',
            'end_date': 'invalid'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('catalog'))
        
    def test_cancel_reservation(self):
        # Create a test reservation
        start_date = timezone.now() + timedelta(days=1)
        end_date = timezone.now() + timedelta(days=3)
        days = (end_date - start_date).days + 1
        total_cost = self.item.daily_rate * Decimal(str(days))
        
        reservation = Reservation.objects.create(
            user=self.user,
            start_date=start_date,
            end_date=end_date,
            status='pending',
            total_cost=total_cost
        )
        
        ReservationItem.objects.create(
            reservation=reservation,
            item=self.item,
            quantity=1,
            price_per_day=self.item.daily_rate,
            subtotal=total_cost
        )
        
        # Test cancelling the reservation
        response = self.client.post(reverse('cancel_reservation', args=[reservation.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify reservation was cancelled
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'cancelled')
        
    def test_view_reservations(self):
        # Create some test reservations
        start_date = timezone.now() + timedelta(days=1)
        end_date = timezone.now() + timedelta(days=3)
        days = (end_date - start_date).days + 1
        total_cost = self.item.daily_rate * Decimal(str(days))
        
        reservation = Reservation.objects.create(
            user=self.user,
            start_date=start_date,
            end_date=end_date,
            status='pending',
            total_cost=total_cost
        )
        
        ReservationItem.objects.create(
            reservation=reservation,
            item=self.item,
            quantity=1,
            price_per_day=self.item.daily_rate,
            subtotal=total_cost
        )
        
        # Test viewing reservations
        response = self.client.get(reverse('my_reservations'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/my_reservations.html') 