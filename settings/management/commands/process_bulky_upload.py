import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from products.models import Product, Category, Unit
from superadmin.models import Business
from superadmin.middleware import set_current_business
from authentication.models import User


class Command(BaseCommand):
    help = "Process bulky CSV upload for products"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", type=str, help="CSV file name in uploads directory"
        )
        parser.add_argument(
            "--business-id", type=int, help="Business ID to associate products with"
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="User ID to associate with the upload (optional)",
        )

    def handle(self, *args, **options):
        filename = options["filename"]
        business_id = options.get("business_id")
        user_id = options.get("user_id")

        # Construct file path
        file_path = os.path.join(settings.BASE_DIR, "uploads", filename)

        # Check if file exists
        if not os.path.exists(file_path):
            raise CommandError(f"File {filename} not found in uploads directory")

        # Get business context
        business = None
        if business_id:
            try:
                business = Business.objects.get(id=business_id)
            except Business.DoesNotExist:
                raise CommandError(f"Business with ID {business_id} not found")
        else:
            # Use the first business if none specified
            business = Business.objects.first()
            if not business:
                raise CommandError("No business found. Please specify a business ID.")

        # Set the current business context for the BusinessSpecificManager
        set_current_business(business)

        # Get user context
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f"User with ID {user_id} not found")

        self.stdout.write(f"Processing bulky upload: {filename}")
        self.stdout.write(f"Business: {business}")
        self.stdout.write(f"User: {user}")

        # Process the CSV file
        try:
            with open(file_path, "r", encoding="utf-8") as csv_file:
                reader = csv.reader(csv_file)

                # Skip header row
                header = next(reader)
                self.stdout.write(f'CSV Header: {", ".join(header)}')

                success_count = 0
                error_count = 0

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Process each row
                        if len(row) < 11:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {row_num}: Insufficient columns, skipping"
                                )
                            )
                            error_count += 1
                            continue

                        # Extract data from CSV row
                        # Expected columns: name, sku, barcode, category_name, unit_name,
                        # description, cost_price, selling_price, quantity, reorder_level, expiry_date
                        (
                            name,
                            sku,
                            barcode,
                            category_name,
                            unit_name,
                            description,
                            cost_price,
                            selling_price,
                            quantity,
                            reorder_level,
                            expiry_date,
                        ) = row

                        # Validate required fields
                        if not name or not sku or not category_name or not unit_name:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {row_num}: Missing required fields (name, sku, category, unit), skipping"
                                )
                            )
                            error_count += 1
                            continue

                        # Get or create category
                        category, created = Category.objects.get_or_create(
                            business=business,
                            name=category_name,
                            defaults={"description": f"Category for {category_name}"},
                        )
                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(f"Created category: {category_name}")
                            )

                        # Get or create unit
                        unit, created = Unit.objects.get_or_create(
                            business=business,
                            name=unit_name,
                            defaults={"symbol": unit_name[:3].upper()},
                        )
                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(f"Created unit: {unit_name}")
                            )

                        # Parse numeric values
                        try:
                            cost_price = float(cost_price) if cost_price else 0.0
                            selling_price = (
                                float(selling_price) if selling_price else 0.0
                            )
                            quantity = float(quantity) if quantity else 0.0
                            reorder_level = (
                                float(reorder_level) if reorder_level else 0.0
                            )
                        except ValueError as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {row_num}: Invalid numeric values, skipping - {e}"
                                )
                            )
                            error_count += 1
                            continue

                        # Parse expiry date if provided
                        expiry_date_parsed = None
                        if expiry_date:
                            try:
                                from datetime import datetime

                                expiry_date_parsed = datetime.strptime(
                                    expiry_date, "%Y-%m-%d"
                                ).date()
                            except ValueError:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Row {row_num}: Invalid expiry date format (expected YYYY-MM-DD), ignoring"
                                    )
                                )

                        # Create or update product
                        product, created = Product.objects.update_or_create(
                            business=business,
                            sku=sku,
                            defaults={
                                "name": name,
                                "barcode": barcode if barcode else None,
                                "category": category,
                                "unit": unit,
                                "description": description,
                                "cost_price": cost_price,
                                "selling_price": selling_price,
                                "quantity": quantity,
                                "reorder_level": reorder_level,
                                "expiry_date": expiry_date_parsed,
                            },
                        )

                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Created product: {name} (SKU: {sku})"
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Updated product: {name} (SKU: {sku})"
                                )
                            )

                        success_count += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Row {row_num}: Error processing row - {e}"
                            )
                        )
                        error_count += 1

                # Summary
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nUpload completed. Success: {success_count}, Errors: {error_count}"
                    )
                )

        except Exception as e:
            raise CommandError(f"Error processing file: {e}")
