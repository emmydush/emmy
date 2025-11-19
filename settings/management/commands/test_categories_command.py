from django.core.management.base import BaseCommand
from products.models import Category
from superadmin.models import Business


class Command(BaseCommand):
    help = "Test category creation"

    def add_arguments(self, parser):
        parser.add_argument("--business-id", type=int, help="Business ID to use")

    def handle(self, *args, **options):
        business_id = options.get("business_id")

        if business_id:
            try:
                business = Business.objects.get(id=business_id)
            except Business.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Business with ID {business_id} not found")
                )
                return
        else:
            business = Business.objects.first()
            if not business:
                self.stdout.write(self.style.ERROR("No businesses found"))
                return

        self.stdout.write(f"Business: {business.id} - {business.company_name}")

        # Check if Electronics category exists
        try:
            category = Category.objects.get(business=business, name="Electronics")
            self.stdout.write(
                self.style.SUCCESS(f"Found existing category: {category.name}")
            )
        except Category.DoesNotExist:
            self.stdout.write("Category does not exist")
            # Try to create it
            try:
                category = Category.objects.create(
                    business=business, name="Electronics", description="Test category"
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created category: {category.name}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating category: {e}"))
