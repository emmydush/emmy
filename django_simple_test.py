import os
import sys
import django
from django.test import TestCase

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings")
django.setup()


class SimpleDjangoTest(TestCase):
    def test_django_version(self):
        import django

        # Just check that Django is properly loaded
        self.assertIsNotNone(django.get_version())
        print(f"Django version: {django.get_version()}")

    def test_settings_loaded(self):
        from django.conf import settings

        # Check that settings are loaded
        self.assertTrue(hasattr(settings, "DATABASES"))
        print("Django settings loaded successfully")


if __name__ == "__main__":
    import unittest

    unittest.main()
