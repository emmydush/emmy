from django.core.management.base import BaseCommand
from products.models import Product, Category, Unit


class Command(BaseCommand):
    help = "Create a test product with barcode for scanner testing"

    def handle(self, *args, **options):
        # Get the first category and unit
        category = Category.objects.first()
        unit = Unit.objects.first()

        if not category or not unit:
            self.stdout.write(
                self.style.ERROR("Please create at least one category and unit first")
            )
            return

        # Create test product
        product, created = Product.objects.get_or_create(
            name="Test Product",
            sku="TEST001",
            barcode="123456789012",
            category=category,
            unit=unit,
            defaults={"cost_price": 5.00, "selling_price": 10.00, "quantity": 10},
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created test product: {product.name} with barcode {product.barcode}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Test product already exists: {product.name} with barcode {product.barcode}"
                )
            )
