from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product, Category, Unit
from suppliers.models import Supplier
from superadmin.models import Business
from superadmin.middleware import set_current_business

User = get_user_model()


class APITestCase(TestCase):
    def setUp(self):
        # Create test business
        self.business = Business.objects.create(
            company_name="Test Business",
            owner=User.objects.create_user(
                username="testowner", password="testpass123", email="owner@test.com"
            ),
            email="business@test.com",
            business_type="retail",
        )

        # Set current business context
        set_current_business(self.business)

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="user@test.com"
        )

        # Associate user with business
        self.user.businesses.add(self.business)

        # Create test category
        self.category = Category.objects.create(
            business=self.business,
            name="Test Category",
            description="Test category description",
        )

        # Create test unit
        self.unit = Unit.objects.create(
            business=self.business, name="Pieces", symbol="pcs"
        )

        # Create test supplier
        self.supplier = Supplier.objects.create(
            business=self.business,
            name="Test Supplier",
            email="supplier@test.com",
            phone="123-456-7890",
            address="123 Test Street",
        )

        # Create test product
        self.product = Product.objects.create(
            business=self.business,
            name="Test Product",
            sku="TP001",
            category=self.category,
            unit=self.unit,
            quantity=100,
            cost_price=10.00,
            selling_price=15.00,
            reorder_level=10,
        )

        # Create API client
        self.client = APIClient()

    def test_api_docs(self):
        """Test that API documentation endpoint works"""
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("endpoints", response.data)

    def test_product_list_unauthenticated(self):
        """Test that product list requires authentication"""
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_list_authenticated(self):
        """Test that authenticated users can list products"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_product_detail_authenticated(self):
        """Test that authenticated users can retrieve product details"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f"/api/v1/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Product")

    def test_dashboard_stats(self):
        """Test that dashboard stats endpoint works"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/api/v1/dashboard/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_products", response.data)
        self.assertIn("low_stock_products", response.data)

    def test_password_change(self):
        """Test that users can change their password"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Change password
        response = self.client.post(
            "/api/v1/auth/password/change/",
            {
                "old_password": "testpass123",
                "new_password": "newpass456",
                "confirm_password": "newpass456",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("token", response.data)

        # Verify user can login with new password
        self.client.logout()
        login_response = self.client.post(
            "/api/v1/auth/login/", {"username": "testuser", "password": "newpass456"}
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("token", login_response.data)

    def test_password_change_with_incorrect_old_password(self):
        """Test that password change fails with incorrect old password"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Try to change password with incorrect old password
        response = self.client.post(
            "/api/v1/auth/password/change/",
            {
                "old_password": "wrongpassword",
                "new_password": "newpass456",
                "confirm_password": "newpass456",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)

    def test_password_change_with_mismatched_passwords(self):
        """Test that password change fails with mismatched new passwords"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Try to change password with mismatched passwords
        response = self.client.post(
            "/api/v1/auth/password/change/",
            {
                "old_password": "testpass123",
                "new_password": "newpass456",
                "confirm_password": "differentpass789",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
