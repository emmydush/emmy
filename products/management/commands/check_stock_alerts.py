from django.core.management.base import BaseCommand
from django.utils import timezone
from products.stock_monitoring import (
    check_low_stock_alerts,
    check_abnormal_reduction,
    check_expired_products,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check for stock alerts and create notifications"

    def add_arguments(self, parser):
        parser.add_argument(
            "--business-id",
            type=int,
            help="Business ID to check alerts for (optional - checks all if not provided)",
        )

    def handle(self, *args, **options):
        business_id = options.get("business_id")

        self.stdout.write(
            self.style.SUCCESS(
                f'[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Starting stock alert checks...'
            )
        )

        try:
            # Check for low stock alerts
            self.stdout.write("Checking for low stock alerts...")
            check_low_stock_alerts()

            # Check for abnormal reductions
            self.stdout.write("Checking for abnormal stock reductions...")
            check_abnormal_reduction()

            # Check for expired products
            self.stdout.write("Checking for expired products...")
            check_expired_products()

            self.stdout.write(
                self.style.SUCCESS(
                    f'[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Stock alert checks completed successfully!'
                )
            )

        except Exception as e:
            logger.error(f"Error during stock alert checks: {e}")
            self.stdout.write(self.style.ERROR(f"Error during stock alert checks: {e}"))
