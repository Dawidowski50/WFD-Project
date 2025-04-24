from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile
from inventory.models import Category, Item
from decimal import Decimal

User = get_user_model()

class InventoryManagementTests(TestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            is_staff=True,
            is_superuser=True
        )
        # Update the automatically created profile
        self.admin_user.userprofile.role = 'admin'
        self.admin_user.userprofile.save()
        
        self.client = Client()
        self.client.login(username='admin', password='adminpass')

        # Create test category for item availability test
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )

    def test_category_management(self):
        # Test adding a category
        response = self.client.post(reverse('manage_categories'), {
            'action': 'add_category',
            'name': 'Test Category',
            'description': 'Test Description'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Category.objects.filter(name='Test Category').exists())

        # Test editing a category
        category = Category.objects.filter(name='Test Category').first()
        response = self.client.post(reverse('manage_categories'), {
            'action': 'edit_category',
            'category_id': category.id,
            'name': 'Updated Category',
            'description': 'Updated Description'
        })
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Category')

    def test_item_management(self):
        # Create a category first
        category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )

        # Test adding an item
        response = self.client.post(reverse('manage_inventory'), {
            'action': 'add',
            'name': 'New Item',
            'category': category.id,
            'daily_rate': '50.00',
            'description': 'Test Item',
            'condition': 'good'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(name='New Item').exists())

        # Test editing an item
        item = Item.objects.get(name='New Item')
        response = self.client.post(reverse('manage_inventory'), {
            'action': 'edit',
            'item_id': item.id,
            'name': 'Updated Item',
            'category': category.id,
            'daily_rate': '75.00',
            'description': 'Updated Description',
            'condition': 'excellent'
        })
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.name, 'Updated Item')
        self.assertEqual(item.daily_rate, Decimal('75.00'))

    def test_item_availability(self):
        # Create test item
        item = Item.objects.create(
            name='Test Item',
            description='Test Description',
            category=self.category,
            daily_rate=Decimal('50.00'),
            condition='excellent',
            is_available=True
        )

        # Test item is available by default
        self.assertTrue(item.is_available)

        # Test item can be marked as unavailable
        item.is_available = False
        item.save()
        self.assertFalse(item.is_available) 