"""
Password Change Functionality Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status


User = get_user_model()


class PasswordChangeTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        # Create API client
        self.client = APIClient()

    def test_password_change_success(self):
        """Test successful password change"""
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
        """Test password change with incorrect old password"""
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
        """Test password change with mismatched new passwords"""
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

    def test_password_change_with_same_old_and_new_password(self):
        """Test password change with same old and new password"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Try to change password with same old and new password
        response = self.client.post(
            "/api/v1/auth/password/change/",
            {
                "old_password": "testpass123",
                "new_password": "testpass123",
                "confirm_password": "testpass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_password_change_requires_authentication(self):
        """Test that password change requires authentication"""
        response = self.client.post(
            "/api/v1/auth/password/change/",
            {
                "old_password": "testpass123",
                "new_password": "newpass456",
                "confirm_password": "newpass456",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
