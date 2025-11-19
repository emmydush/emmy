from django.core.management.base import BaseCommand
from products.models import Product
from products.utils import generate_product_barcode_image
import os
from django.conf import settings


class Command(BaseCommand):
    help = "Generate a test barcode image for the test product"

    def handle(self, *args, **options):
        try:
            # Get the test product
            product = Product.objects.get(barcode="123456789012")

            # Generate barcode image
            barcode_buffer = generate_product_barcode_image(product)

            if barcode_buffer:
                # Ensure the test_barcodes directory exists
                test_barcodes_dir = os.path.join(settings.MEDIA_ROOT, "test_barcodes")
                os.makedirs(test_barcodes_dir, exist_ok=True)

                # Save the barcode image
                barcode_path = os.path.join(test_barcodes_dir, "test_barcode.png")
                with open(barcode_path, "wb") as f:
                    f.write(barcode_buffer.getvalue())

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully generated test barcode: {barcode_path}"
                    )
                )
                self.stdout.write(
                    f"You can access it at: /media/test_barcodes/test_barcode.png"
                )
            else:
                self.stdout.write(self.style.ERROR("Failed to generate barcode image"))

        except Product.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Test product with barcode 123456789012 not found")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating barcode: {str(e)}"))
