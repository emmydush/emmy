from django.core.management.base import BaseCommand
from expenses.forms import ExpenseForm
from superadmin.models import Business
from authentication.models import User
from superadmin.middleware import set_current_business


class Command(BaseCommand):
    help = "Test that expense form shows correct categories for a business"

    def handle(self, *args, **options):
        # Get a business
        business = Business.objects.first()
        if not business:
            self.stdout.write(self.style.ERROR("No businesses found"))
            return

        self.stdout.write(f"Testing categories for business: {business.company_name}")

        # Set the business context
        set_current_business(business)

        # Create the form
        form = ExpenseForm()

        # Get categories
        categories = form.fields["category"].queryset
        self.stdout.write(f"Found {categories.count()} categories for this business:")

        # Show first 20 categories
        for i, category in enumerate(categories[:20]):
            self.stdout.write(f"{i+1:2d}. {category.name}")

        # Show total count
        self.stdout.write(f"Total categories: {categories.count()}")
