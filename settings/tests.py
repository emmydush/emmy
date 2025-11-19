from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import BusinessSettings
from .forms import BusinessSettingsForm


class BusinessSettingsTestCase(TestCase):
    def setUp(self):
        self.business_settings = BusinessSettings.objects.create(
            business_name="Test Business",
            business_address="123 Test St",
            business_email="test@example.com",
            business_phone="123-456-7890",
            currency="USD",
            currency_symbol="$",
            tax_rate=10.5,
        )

    def test_logo_deletion(self):
        # Create a simple image file
        image = SimpleUploadedFile(
            name="test_logo.png",
            content=b"test image content",
            content_type="image/png",
        )

        # Add logo to business settings
        self.business_settings.business_logo = image
        self.business_settings.save()

        # Verify logo was saved
        self.assertTrue(self.business_settings.business_logo)

        # Create form with delete_logo checked
        form_data = {
            "business_name": "Test Business",
            "business_address": "123 Test St",
            "business_email": "test@example.com",
            "business_phone": "123-456-7890",
            "currency": "USD",
            "currency_symbol": "$",
            "tax_rate": 10.5,
            "delete_logo": True,
            "expiry_alert_days": 7,
            "near_expiry_alert_days": 30,
        }

        form = BusinessSettingsForm(data=form_data, instance=self.business_settings)
        self.assertTrue(form.is_valid())

        # Save the form
        updated_settings = form.save()

        # Verify logo was deleted
        self.assertFalse(updated_settings.business_logo)

    def test_logo_update_without_deletion(self):
        # Create a simple image file
        image = SimpleUploadedFile(
            name="test_logo.png",
            content=b"test image content",
            content_type="image/png",
        )

        # Add logo to business settings
        self.business_settings.business_logo = image
        self.business_settings.save()

        # Verify logo was saved
        self.assertTrue(self.business_settings.business_logo)

        # Create form without delete_logo checked
        form_data = {
            "business_name": "Test Business Updated",
            "business_address": "123 Test St",
            "business_email": "test@example.com",
            "business_phone": "123-456-7890",
            "currency": "USD",
            "currency_symbol": "$",
            "tax_rate": 10.5,
            "delete_logo": False,
            "expiry_alert_days": 7,
            "near_expiry_alert_days": 30,
        }

        form = BusinessSettingsForm(data=form_data, instance=self.business_settings)
        self.assertTrue(form.is_valid())

        # Save the form
        updated_settings = form.save()

        # Verify business name was updated
        self.assertEqual(updated_settings.business_name, "Test Business Updated")

        # Verify logo still exists
        self.assertTrue(updated_settings.business_logo)
