from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile

User = get_user_model()

class UserAuthenticationTest(TestCase):
    def setUp(self):
        # Create test users with different roles
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@admin.com',
            password='password',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'admin'
        self.admin.userprofile.save()

        self.manager = User.objects.create_user(
            username='manager',
            email='manager@manager.com',
            password='password',
            is_staff=True
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()

        self.staff = User.objects.create_user(
            username='staff',
            email='staff@staff.com',
            password='password',
            is_staff=True
        )
        self.staff.userprofile.role = 'staff'
        self.staff.userprofile.save()

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@customer.com',
            password='password'
        )
        self.customer.userprofile.role = 'customer'
        self.customer.userprofile.save()

    def test_login_redirects(self):
        # Test admin login redirects to home page
        response = self.client.post(reverse('login'), {
            'username': 'admin@admin.com',
            'password': 'password'
        })
        self.assertRedirects(response, '/')

        # Test customer login redirects to home page
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'customer@customer.com',
            'password': 'password'
        })
        self.assertRedirects(response, '/')

    def test_role_based_access(self):
        # Test admin access
        self.client.post(reverse('login'), {'username': 'admin@admin.com', 'password': 'password'})
        response = self.client.get(reverse('manage_inventory'))
        self.assertEqual(response.status_code, 200)

        # Test manager access
        self.client.post(reverse('login'), {'username': 'manager@manager.com', 'password': 'password'})
        response = self.client.get(reverse('manage_inventory'))
        self.assertEqual(response.status_code, 200)

        # Test staff access (should redirect to login)
        self.client.post(reverse('login'), {'username': 'staff@staff.com', 'password': 'password'})
        response = self.client.get(reverse('manage_inventory'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

        # Test customer access (should redirect to login)
        self.client.post(reverse('login'), {'username': 'customer@customer.com', 'password': 'password'})
        response = self.client.get(reverse('manage_inventory'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

        # Test unauthenticated access (should redirect to login)
        self.client.logout()
        response = self.client.get(reverse('manage_inventory'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/')) 