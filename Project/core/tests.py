from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from inventory.models import Category, Item
from users.models import User
from core.models import UserProfile, Maintenance
from reservations.models import Reservation, ReservationItem

@override_settings(USE_TZ=True)
class MaintenanceAndReservationTest(TestCase):
    def setUp(self):
        # Create test users
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@manager.com',
            password='password',
            is_staff=True
        )
        # Update the automatically created UserProfile
        UserProfile.objects.filter(user=self.manager).update(role='manager')

        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password',
            is_staff=True
        )
        UserProfile.objects.filter(user=self.staff).update(role='staff')

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password'
        )
        # Customer UserProfile is created automatically with correct role

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
            condition='Excellent',
            is_available=True
        )

    def test_schedule_maintenance(self):
        # Login as manager
        self.client.login(username='manager', password='password')
        
        # Schedule maintenance with timezone-aware date
        maintenance_date = timezone.now() + timedelta(days=7)
        maintenance_data = {
            'item': self.item.id,
            'maintenance_date': maintenance_date.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Regular maintenance'
        }
        response = self.client.post(reverse('schedule_maintenance_new'), maintenance_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify maintenance record exists
        maintenance = Maintenance.objects.filter(item=self.item).first()
        self.assertIsNotNone(maintenance)
        self.assertTrue(maintenance.maintenance_date.tzinfo is not None)

    def test_schedule_maintenance_validation(self):
        self.client.login(username='manager', password='password')
        
        # Test past date with timezone-aware date
        maintenance_date = timezone.now() - timedelta(days=1)
        maintenance_data = {
            'maintenance_date': maintenance_date.strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Regular maintenance'
        }
        response = self.client.post(reverse('schedule_maintenance_item', kwargs={'item_id': self.item.id}), maintenance_data)
        self.assertEqual(response.status_code, 200)  # Returns form with error
        self.assertFalse(Maintenance.objects.filter(item=self.item).exists())

        # Test missing description with timezone-aware date
        maintenance_date = timezone.now() + timedelta(days=1)
        maintenance_data = {
            'maintenance_date': maintenance_date.strftime('%Y-%m-%d %H:%M:%S'),
            'description': ''
        }
        response = self.client.post(reverse('schedule_maintenance_item', kwargs={'item_id': self.item.id}), maintenance_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Maintenance.objects.filter(item=self.item).exists())

    def test_maintenance_permissions(self):
        # Test staff access to maintenance schedule
        self.client.login(username='staff', password='password')
        response = self.client.get(reverse('maintenance_schedule'))
        self.assertEqual(response.status_code, 200)

        # Test customer access (should be denied)
        self.client.login(username='customer', password='password')
        response = self.client.get(reverse('maintenance_schedule'))
        self.assertEqual(response.status_code, 403)

    def test_reserve_item(self):
        # Login as customer
        self.client.login(username='customer', password='password')
        
        # Make reservation with timezone-aware dates
        start_date = timezone.now() + timedelta(days=1)
        end_date = timezone.now() + timedelta(days=4)
        reservation_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('reserve_item', kwargs={'item_id': self.item.id}), reservation_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify reservation exists with timezone-aware dates
        reservation = Reservation.objects.filter(
            items__item=self.item,
            user=self.customer
        ).first()
        self.assertIsNotNone(reservation)
        self.assertTrue(reservation.start_date.tzinfo is not None)
        self.assertTrue(reservation.end_date.tzinfo is not None)
        self.assertEqual(reservation.status, 'active')

    def test_reserve_item_validation(self):
        self.client.login(username='customer', password='password')
        
        # Test past date with timezone-aware date
        start_date = timezone.now() - timedelta(days=1)
        end_date = timezone.now() + timedelta(days=1)
        reservation_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('reserve_item', kwargs={'item_id': self.item.id}), reservation_data)
        self.assertEqual(response.status_code, 302)  # Redirects with error message
        self.assertFalse(Reservation.objects.exists())

        # Test end date before start date with timezone-aware dates
        start_date = timezone.now() + timedelta(days=2)
        end_date = timezone.now() + timedelta(days=1)
        reservation_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('reserve_item', kwargs={'item_id': self.item.id}), reservation_data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Reservation.objects.exists())

    def test_maintenance_blocks_reservation(self):
        # Schedule maintenance with timezone-aware date
        maintenance_date = timezone.now() + timedelta(days=5)
        Maintenance.objects.create(
            item=self.item,
            staff=self.manager,
            maintenance_date=maintenance_date,
            description='Regular maintenance',
            status='SCHEDULED'
        )

        # Try to reserve item during maintenance
        self.client.login(username='customer', password='password')
        reservation_data = {
            'start_date': maintenance_date.strftime('%Y-%m-%d'),
            'end_date': (maintenance_date + timedelta(days=1)).strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('reserve_item', kwargs={'item_id': self.item.id}), reservation_data)
        
        # Verify reservation was not created
        self.assertFalse(Reservation.objects.filter(
            items__item=self.item,
            start_date__date=maintenance_date.date()
        ).exists())

    def test_cancel_reservation(self):
        # Create a reservation with timezone-aware dates
        self.client.login(username='customer', password='password')
        start_date = timezone.now() + timedelta(days=1)
        end_date = timezone.now() + timedelta(days=4)
        reservation_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        self.client.post(reverse('reserve_item', kwargs={'item_id': self.item.id}), reservation_data)
        
        reservation = Reservation.objects.first()
        response = self.client.post(reverse('cancel_reservation', kwargs={'reservation_id': reservation.id}))
        self.assertEqual(response.status_code, 302)
        
        # Verify reservation is cancelled
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'cancelled')

    def test_process_return(self):
        # Create a reservation with timezone-aware dates
        start_date = timezone.now() - timedelta(days=3)
        end_date = timezone.now() - timedelta(days=1)
        reservation = Reservation.objects.create(
            user=self.customer,
            start_date=start_date,
            end_date=end_date,
            status='active',
            total_cost=Decimal('150.00')
        )
        ReservationItem.objects.create(
            reservation=reservation,
            item=self.item,
            price_per_day=self.item.daily_rate,
            subtotal=Decimal('150.00')
        )
        
        # Process return as staff
        self.client.login(username='staff', password='password')
        response = self.client.post(
            reverse('process_return', kwargs={'reservation_id': reservation.id}),
            {'status': 'completed'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify reservation is completed and item is available
        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(reservation.status, 'completed')
        self.assertTrue(self.item.is_available)

    def test_reports_access(self):
        # Test manager access
        self.client.login(username='manager', password='password')
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        
        # Test staff access (should be denied)
        self.client.login(username='staff', password='password')
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 403)
        
        # Test customer access (should be denied)
        self.client.login(username='customer', password='password')
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 403)
