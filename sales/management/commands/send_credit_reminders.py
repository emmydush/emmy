from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from sales.models import CreditSale
from datetime import date
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send SMS reminders for overdue credit sales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-overdue',
            type=int,
            default=1,
            help='Number of days overdue before sending reminder (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        days_overdue = options['days_overdue']
        dry_run = options['dry_run']
        
        # Calculate the cutoff date
        cutoff_date = date.today() - timezone.timedelta(days=days_overdue)
        
        # Get overdue unpaid credit sales
        overdue_sales = CreditSale.objects.filter(
            due_date__lte=cutoff_date,
            is_fully_paid=False
        ).select_related('customer', 'sale')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Found {overdue_sales.count()} overdue credit sales '
                f'(due {days_overdue}+ days ago)'
            )
        )
        
        for credit_sale in overdue_sales:
            try:
                # Check if customer has a phone number
                if not credit_sale.customer.phone:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping customer {credit_sale.customer.full_name} '
                            f'- no phone number'
                        )
                    )
                    continue
                
                # Prepare the message
                message = (
                    f"Reminder: Your account has an outstanding balance of "
                    f"{credit_sale.outstanding_balance} for invoice #{credit_sale.sale.id}. "
                    f"The payment was due on {credit_sale.due_date.strftime('%Y-%m-%d')}. "
                    f"Please arrange payment at your earliest convenience."
                )
                
                if dry_run:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"[DRY RUN] Would send to {credit_sale.customer.phone}: {message}"
                        )
                    )
                else:
                    # Send the SMS (placeholder - implement actual SMS sending logic)
                    self.send_sms(credit_sale.customer.phone, message)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Sent reminder to {credit_sale.customer.phone} '
                            f'for sale #{credit_sale.sale.id}'
                        )
                    )
                    
            except Exception as e:
                logger.error(f"Error sending reminder for credit sale {credit_sale.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder for sale #{credit_sale.sale.id}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS('Finished processing credit sale reminders')
        )
    
    def send_sms(self, phone_number, message):
        """
        Placeholder method for sending SMS.
        In a real implementation, you would integrate with an SMS service provider
        such as Twilio, Nexmo, or a local SMS gateway.
        """
        # Example integration with a hypothetical SMS service:
        # 
        # import requests
        # response = requests.post(
        #     'https://api.sms-service.com/send',
        #     data={
        #         'api_key': settings.SMS_API_KEY,
        #         'to': phone_number,
        #         'message': message
        #     }
        # )
        # response.raise_for_status()
        #
        # For now, we'll just log the attempt
        logger.info(f"SMS would be sent to {phone_number}: {message}")
        print(f"SMS would be sent to {phone_number}: {message}")