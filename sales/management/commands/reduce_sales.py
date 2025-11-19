from django.core.management.base import BaseCommand
from sales.models import Sale, SaleItem
from superadmin.models import Business
from authentication.models import User


class Command(BaseCommand):
    help = "Reduce the number of sales for a specific user business"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email of the user to reduce sales for",
            required=True,
        )
        parser.add_argument(
            "--keep", type=int, help="Number of sales to keep", default=20
        )

    def handle(self, *args, **options):
        email = options["email"]
        keep_count = options["keep"]

        # Get the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with email {email} does not exist")
            )
            return

        # Get the user's business
        try:
            business = Business.objects.get(owner=user)
        except Business.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No business found for user {email}"))
            return

        # Get all sales for this business
        all_sales = Sale.objects.filter(business=business)
        total_sales = all_sales.count()

        if total_sales <= keep_count:
            self.stdout.write(
                f"User already has {total_sales} sales, which is less than or equal to {keep_count}. No reduction needed."
            )
            return

        # Calculate how many sales to delete
        delete_count = total_sales - keep_count

        # Get sales to delete (all except the first 'keep_count' sales)
        sales_to_delete = all_sales[keep_count:]

        # Delete sale items first (due to foreign key constraints)
        sale_items_deleted = 0
        sales_deleted = 0

        for sale in sales_to_delete:
            # Delete sale items for this sale
            items_count = sale.items.count()
            sale.items.all().delete()
            sale_items_deleted += items_count

            # Delete the sale
            sale.delete()
            sales_deleted += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {sales_deleted} sales and {sale_items_deleted} sale items. "
                f"Kept {keep_count} sales for user {email}"
            )
        )
