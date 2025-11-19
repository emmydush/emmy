from django.core.management.base import BaseCommand
from expenses.models import ExpenseCategory
from superadmin.models import Business


class Command(BaseCommand):
    help = "Add more default expense categories for better labeling options"

    def handle(self, *args, **options):
        # Common expense categories that businesses typically use
        default_categories = [
            # Operational Expenses
            {
                "name": "Office Supplies",
                "description": "Stationery, printer ink, paper, etc.",
            },
            {
                "name": "Equipment",
                "description": "Computers, machinery, tools, office equipment",
            },
            {
                "name": "Software & Subscriptions",
                "description": "Software licenses, cloud services, subscriptions",
            },
            {
                "name": "Insurance",
                "description": "Business insurance, health insurance, liability insurance",
            },
            {
                "name": "Legal & Professional Fees",
                "description": "Legal services, accounting, consulting",
            },
            {
                "name": "Training & Development",
                "description": "Employee training, workshops, courses",
            },
            {
                "name": "Travel & Transportation",
                "description": "Business travel, fuel, vehicle maintenance",
            },
            {
                "name": "Meals & Entertainment",
                "description": "Business meals, client entertainment",
            },
            {
                "name": "Telecommunications",
                "description": "Phone, internet, mobile plans",
            },
            {
                "name": "Repairs & Maintenance",
                "description": "Building repairs, equipment maintenance",
            },
            # Financial Expenses
            {"name": "Bank Fees", "description": "Bank charges, transaction fees"},
            {"name": "Interest", "description": "Loan interest, credit card interest"},
            {"name": "Taxes", "description": "Business taxes, property taxes"},
            # Marketing & Sales
            {
                "name": "Advertising",
                "description": "Online ads, print ads, promotional materials",
            },
            {
                "name": "Marketing Materials",
                "description": "Brochures, business cards, signage",
            },
            {
                "name": "Events & Sponsorships",
                "description": "Trade shows, conferences, sponsorships",
            },
            # Inventory Related
            {
                "name": "Inventory Shrinkage",
                "description": "Lost, stolen, or damaged inventory",
            },
            {
                "name": "Storage & Warehousing",
                "description": "Storage fees, warehouse rent",
            },
            # Miscellaneous
            {"name": "Miscellaneous", "description": "Other uncategorized expenses"},
        ]

        # Get all businesses
        businesses = Business.objects.all()

        categories_added = 0
        categories_skipped = 0

        for business in businesses:
            for category_data in default_categories:
                # Check if category already exists for this business
                if not ExpenseCategory.objects.filter(
                    business=business, name=category_data["name"]
                ).exists():
                    # Create the category for this business
                    ExpenseCategory.objects.create(
                        business=business,
                        name=category_data["name"],
                        description=category_data["description"],
                    )
                    categories_added += 1
                else:
                    categories_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully added {categories_added} new expense categories. "
                f"Skipped {categories_skipped} existing categories."
            )
        )
