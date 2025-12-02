from django.core.management.base import BaseCommand
from authentication.models import User, UserPermission
from superadmin.models import Business

class Command(BaseCommand):
    help = 'Fix role and permissions for business owner royke'

    def handle(self, *args, **options):
        try:
            # Get the user
            user = User.objects.get(username='royke')
            self.stdout.write(f'Found user: {user.username}')
            self.stdout.write(f'Current role: {user.role}')
            
            # Set the role to admin
            user.role = 'admin'
            user.save()
            self.stdout.write(self.style.SUCCESS('Updated user role to admin'))
            
            # Check if user has a business
            if not user.owned_businesses.exists():
                self.stdout.write(self.style.WARNING('User does not own any businesses'))
            else:
                business = user.owned_businesses.first()
                self.stdout.write(f'User owns business: {business.company_name}')
                
                # Ensure business is active
                if business.status != "active":
                    business.status = "active"
                    business.save()
                    self.stdout.write(self.style.SUCCESS(f'Activated business: {business.company_name}'))
            
            # Associate user with their business if not already associated
            if user.owned_businesses.exists():
                business = user.owned_businesses.first()
                if not user.businesses.filter(id=business.id).exists():
                    user.businesses.add(business)
                    self.stdout.write(self.style.SUCCESS(f'Associated user with business: {business.company_name}'))
            
            # Create or update UserPermission
            user_permission, created = UserPermission.objects.get_or_create(user=user)
            
            # Set all permissions to True for business owners
            user_permission.can_create = True
            user_permission.can_edit = True
            user_permission.can_delete = True
            user_permission.can_manage_users = True
            user_permission.can_create_users = True
            user_permission.can_edit_users = True
            user_permission.can_delete_users = True
            user_permission.can_access_products = True
            user_permission.can_access_sales = True
            user_permission.can_access_purchases = True
            user_permission.can_access_customers = True
            user_permission.can_access_suppliers = True
            user_permission.can_access_expenses = True
            user_permission.can_access_reports = True
            user_permission.can_access_settings = True
            
            user_permission.save()
            
            if created:
                self.stdout.write(self.style.SUCCESS('Created new UserPermission record with full access'))
            else:
                self.stdout.write(self.style.SUCCESS('Updated existing UserPermission record with full access'))
                
            self.stdout.write(self.style.SUCCESS(f'Successfully fixed role and permissions for user: {user.username}'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with username "royke" does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fixing role and permissions: {str(e)}'))