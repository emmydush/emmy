from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete all business-related data while preserving admin users and superusers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for confirmation',
        )

    def handle(self, *args, **options):
        # Check if we should prompt for confirmation
        if not options['no_input']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL business data including businesses, products, customers, suppliers, sales, purchases, etc.\n'
                    'Only admin users and superusers will be preserved.\n'
                    'This action cannot be undone.'
                )
            )
            
            confirm = input('Are you sure you want to proceed? Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.NOTICE('Operation cancelled.'))
                return

        try:
            # Import all the models we need to delete
            from superadmin.models import (
                Business, Branch, Subscription, SubscriptionPlan, 
                Payment, Announcement, SupportTicket, APIClient, APIRequestLog,
                SystemSetting, SystemLog, SecurityEvent
            )
            
            from products.models import Product, Category, Unit
            from customers.models import Customer
            from suppliers.models import Supplier
            from sales.models import Sale, SaleItem, Cart, CartItem
            from purchases.models import PurchaseOrder, PurchaseItem
            from expenses.models import Expense, ExpenseCategory
            from notifications.models import Notification
            
            # Get count of records before deletion for reporting
            business_count = Business.objects.count()
            user_count = User.objects.count()
            
            # Delete business-related data in the correct order to avoid constraint violations
            self.stdout.write('Deleting notifications...')
            Notification.objects.all().delete()
            
            self.stdout.write('Deleting carts and cart items...')
            CartItem.objects.all().delete()
            Cart.objects.all().delete()
            
            self.stdout.write('Deleting sales and sale items...')
            SaleItem.objects.all().delete()
            Sale.objects.all().delete()
            
            self.stdout.write('Deleting purchases and purchase items...')
            PurchaseItem.objects.all().delete()
            PurchaseOrder.objects.all().delete()
            
            self.stdout.write('Deleting products and related data...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            Unit.objects.all().delete()
            
            self.stdout.write('Deleting customers and suppliers...')
            Customer.objects.all().delete()
            Supplier.objects.all().delete()
            
            self.stdout.write('Deleting expenses...')
            Expense.objects.all().delete()
            ExpenseCategory.objects.all().delete()
            
            # Handle accounting tables if they exist
            self.stdout.write('Deleting accounting data...')
            try:
                with connection.cursor() as cursor:
                    # Delete accounting data that might reference businesses
                    cursor.execute("DELETE FROM accounting_account WHERE business_id IS NOT NULL")
                    cursor.execute("DELETE FROM accounting_transaction WHERE business_id IS NOT NULL")
                    cursor.execute("DELETE FROM accounting_journalentry WHERE business_id IS NOT NULL")
                    cursor.execute("DELETE FROM accounting_financialreport WHERE business_id IS NOT NULL")
                    cursor.execute("DELETE FROM accounting_transactionentry WHERE business_id IS NOT NULL")
            except Exception:
                # If accounting tables don't exist, continue
                pass
            
            self.stdout.write('Deleting superadmin data...')
            SupportTicket.objects.all().delete()
            APIRequestLog.objects.all().delete()
            APIClient.objects.all().delete()
            Payment.objects.all().delete()
            Subscription.objects.all().delete()
            Branch.objects.all().delete()
            Business.objects.all().delete()
            Announcement.objects.all().delete()
            SystemSetting.objects.all().delete()
            SystemLog.objects.all().delete()
            SecurityEvent.objects.all().delete()
            
            # Delete all users except superusers and staff members
            self.stdout.write('Deleting non-admin users...')
            non_admin_users = User.objects.filter(is_superuser=False, is_staff=False)
            deleted_user_count = non_admin_users.count()
            non_admin_users.delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during data reset: {str(e)}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully reset business data!\n'
                f'- Deleted {business_count} businesses\n'
                f'- Deleted {deleted_user_count} non-admin users\n'
                f'- Preserved all admin and superuser accounts'
            )
        )