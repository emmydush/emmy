from django.core.management.base import BaseCommand
from authentication.models import User, UserPermission
from superadmin.models import Business


class Command(BaseCommand):
    help = "Check user details and permissions for troubleshooting access issues"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to check")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"User found: {user.username}")
            self.stdout.write(f"Role: {user.role}")
            self.stdout.write(f"Email: {user.email}")

            # Check owned businesses
            owned_businesses = user.owned_businesses.all()
            self.stdout.write(f"Owned businesses: {owned_businesses.count()}")
            for business in owned_businesses:
                self.stdout.write(
                    f"  - {business.company_name} (status: {business.status})"
                )

            # Check associated businesses
            associated_businesses = user.businesses.all()
            self.stdout.write(f"Associated businesses: {associated_businesses.count()}")
            for business in associated_businesses:
                self.stdout.write(
                    f"  - {business.company_name} (status: {business.status})"
                )

            # Check user permissions
            try:
                user_permission = UserPermission.objects.get(user=user)
                self.stdout.write("User permissions found:")
                self.stdout.write(f"  - can_create: {user_permission.can_create}")
                self.stdout.write(f"  - can_edit: {user_permission.can_edit}")
                self.stdout.write(f"  - can_delete: {user_permission.can_delete}")
                self.stdout.write(
                    f"  - can_manage_users: {user_permission.can_manage_users}"
                )
                self.stdout.write(
                    f"  - can_access_products: {user_permission.can_access_products}"
                )
                self.stdout.write(
                    f"  - can_access_sales: {user_permission.can_access_sales}"
                )
                self.stdout.write(
                    f"  - can_access_purchases: {user_permission.can_access_purchases}"
                )
                self.stdout.write(
                    f"  - can_access_customers: {user_permission.can_access_customers}"
                )
                self.stdout.write(
                    f"  - can_access_suppliers: {user_permission.can_access_suppliers}"
                )
                self.stdout.write(
                    f"  - can_access_expenses: {user_permission.can_access_expenses}"
                )
                self.stdout.write(
                    f"  - can_access_reports: {user_permission.can_access_reports}"
                )
                self.stdout.write(
                    f"  - can_access_settings: {user_permission.can_access_settings}"
                )
            except UserPermission.DoesNotExist:
                self.stdout.write("No UserPermission record found for this user")

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found in the database')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking user: {str(e)}"))
