from django.core.management.base import BaseCommand
from products.models import Category
from superadmin.models import Business
from superadmin.middleware import set_current_business


class Command(BaseCommand):
    help = "Add more categories to the inventory"

    def handle(self, *args, **options):
        # Get the specific business with ID 3
        business = Business.objects.get(id=3)
        self.stdout.write(f"Business: {business.company_name}")

        # Set the current business context
        set_current_business(business)

        # Define additional categories
        categories_data = [
            {"name": "Books", "description": "Books and educational materials"},
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Food", "description": "Food and beverages"},
            {
                "name": "Home & Garden",
                "description": "Home improvement and garden supplies",
            },
            {"name": "Sports", "description": "Sports equipment and accessories"},
            {"name": "Toys", "description": "Toys and games for children"},
            {
                "name": "Health & Beauty",
                "description": "Healthcare and beauty products",
            },
            {"name": "Automotive", "description": "Automotive parts and accessories"},
        ]

        # Create categories
        created_count = 0
        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                business=business,
                name=category_data["name"],
                defaults={"description": category_data["description"]},
            )
            if created:
                self.stdout.write(f"Created category: {category.name}")
                created_count += 1
            else:
                self.stdout.write(f"Category already exists: {category.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully added {created_count} new categories. "
                f"Total categories: {Category.objects.filter(business=business).count()}"
            )
        )
